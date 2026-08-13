from conftest import make_user

from app.extensions import db, socketio
from app.models.question import Answer, Category, Question
from app.models.room import GameSnapshot, Match, Room, RoomPlayer, Score
from app.sockets import game_socket


def _login(client, user):
    with client.session_transaction() as browser_session:
        browser_session['_user_id'] = str(user.id)
        browser_session['_fresh'] = True


def _events(socket_client, name):
    return [item for item in socket_client.get_received()
            if item['name'] == name]


def test_authoritative_game_socket_and_reconnect(app, client, user):
    guest = make_user(username='guest', email='guest@example.com')
    category = Category(name='Live test', slug='live-test')
    question = Question(
        category=category, question_text='2 + 2?', difficulty='easy',
        explanation='Basic addition')
    correct = Answer(question=question, answer_text='4', is_correct=True)
    Answer(question=question, answer_text='5', is_correct=False)
    db.session.add(question)
    db.session.flush()
    room = Room(
        code='LIVE01', name='Live', host_id=user.id,
        category_id=category.id, difficulty='easy', question_count=1,
        game_mode='classic')
    db.session.add_all([
        room,
        RoomPlayer(room=room, user_id=user.id, is_ready=True),
        RoomPlayer(room=room, user_id=guest.id, is_ready=True),
    ])
    db.session.commit()

    _login(client, user)
    live = socketio.test_client(app, flask_test_client=client)
    assert live.is_connected()
    live.emit('join_room', {'room_code': 'LIVE01'})
    assert _events(live, 'room_joined')

    live.emit('start_game', {'room_code': 'LIVE01'})
    assert GameSnapshot.query.filter_by(room_code='LIVE01').one().is_active
    assert Match.query.filter_by(room_id=room.id).count() == 1
    live.emit('request_question', {'room_code': 'LIVE01'})
    question_events = _events(live, 'question')
    assert question_events and question_events[0]['args'][0]['question_text'] == '2 + 2?'

    # Fast answers are rejected, normal answers are scored and snapshotted.
    live.emit('submit_answer', {
        'room_code': 'LIVE01', 'answer_id': correct.id, 'time_taken': 0.1})
    assert _events(live, 'error')
    live.emit('submit_answer', {
        'room_code': 'LIVE01', 'answer_id': correct.id, 'time_taken': 2.0})
    answer_events = _events(live, 'answer_result')
    assert answer_events and answer_events[0]['args'][0]['correct'] is True

    # Simulate a worker restart. State must recover before the next event.
    game_socket.game_states.clear()
    live.emit('recover_game', {'room_code': 'LIVE01'})
    recovery = _events(live, 'game_recovery')[0]['args'][0]
    assert recovery['found'] is True and recovery['score'] > 0

    live.emit('next_question', {'room_code': 'LIVE01'})
    db.session.expire_all()
    assert Room.query.filter_by(code='LIVE01').one().status == 'finished'
    assert Score.query.filter_by(match_id=Match.query.one().id).count() == 2
    assert GameSnapshot.query.filter_by(room_code='LIVE01').one().is_active is False
    assert 'LIVE01' not in game_socket.game_states
    live.disconnect()


def test_game_socket_authorization_and_survival(app, client, user):
    guest = make_user(username='survivor', email='survivor@example.com')
    room = Room(
        code='SURV01', name='Survival', host_id=guest.id,
        question_count=1, game_mode='survival')
    db.session.add_all([
        room,
        RoomPlayer(room=room, user_id=user.id, survival_lives=1),
        RoomPlayer(room=room, user_id=guest.id, survival_lives=1),
    ])
    db.session.commit()
    game_socket.game_states['SURV01'] = {
        'match_id': 999,
        'questions': [{
            'id': 1, 'question_text': 'x', 'question_type': 'multiple_choice',
            'image_url': None, 'explanation': '',
            'answers': [{'id': 1, 'answer_text': 'no', 'is_correct': False},
                        {'id': 2, 'answer_text': 'yes', 'is_correct': True}],
        }],
        'current_question': 0, 'answers': {},
        'scores': {user.id: 0, guest.id: 0},
        'streaks': {user.id: 0, guest.id: 0},
        'survival_lives': {user.id: 1, guest.id: 1},
        'eliminated': set(), 'game_mode': 'survival',
    }
    _login(client, user)
    live = socketio.test_client(app, flask_test_client=client)
    live.emit('join_room', {'room_code': 'SURV01'})
    live.get_received()
    live.emit('skip_question', {'room_code': 'SURV01'})
    assert _events(live, 'error')
    live.emit('game_admin_kick_player', {
        'room_code': 'SURV01', 'user_id': guest.id})
    assert _events(live, 'error')
    live.emit('submit_answer', {
        'room_code': 'SURV01', 'answer_id': 1, 'time_taken': 2})
    assert _events(live, 'player_eliminated')
    live.disconnect()


def test_game_socket_requires_membership_and_rejects_duplicate_answers(app, client, user, db):
    category = Category(name='Socket auth', slug='socket-auth')
    question = Question(category=category, question_text='1 + 1?', difficulty='easy')
    correct = Answer(question=question, answer_text='2', is_correct=True)
    Answer(question=question, answer_text='3', is_correct=False)
    db.session.add(question)
    db.session.flush()
    room = Room(
        code='SOCK01', name='Socket auth', host_id=user.id,
        category_id=category.id, difficulty='easy', question_count=1,
        game_mode='classic', status='playing')
    db.session.add_all([
        room,
        RoomPlayer(room=room, user_id=user.id),
    ])
    db.session.commit()

    game_socket.game_states['SOCK01'] = {
        'match_id': 999,
        'questions': [{
            'id': question.id,
            'question_text': question.question_text,
            'question_type': 'multiple_choice',
            'image_url': None,
            'explanation': '',
            'answers': [
                {'id': correct.id, 'answer_text': '2', 'is_correct': True},
                {'id': correct.id + 1, 'answer_text': '3', 'is_correct': False},
            ],
        }],
        'current_question': 0,
        'answers': {},
        'scores': {user.id: 0},
        'streaks': {user.id: 0},
        'survival_lives': {user.id: 1},
        'eliminated': set(),
        'game_mode': 'classic',
    }

    _login(client, user)
    live = socketio.test_client(app, flask_test_client=client)
    live.emit('submit_answer', {
        'room_code': 'SOCK01', 'answer_id': correct.id, 'time_taken': 2})
    assert _events(live, 'answer_result')
    score_after_first = game_socket.game_states['SOCK01']['scores'][user.id]

    live.emit('submit_answer', {
        'room_code': 'SOCK01', 'answer_id': correct.id, 'time_taken': 2})
    duplicate_errors = _events(live, 'error')
    assert duplicate_errors
    assert duplicate_errors[0]['args'][0]['message'] == 'Answer already submitted'
    assert game_socket.game_states['SOCK01']['scores'][user.id] == score_after_first
    live.disconnect()
    game_socket.game_states.pop('SOCK01', None)


def test_game_socket_membership_required_for_question_events(app, client, user, db):
    room = Room(code='SOCK02', name='Socket membership', host_id=user.id,
                status='playing', question_count=1)
    db.session.add_all([room, RoomPlayer(room=room, user_id=user.id)])
    db.session.commit()

    live = socketio.test_client(app, flask_test_client=client)
    live.emit('submit_answer', {
        'room_code': 'SOCK02', 'answer_id': 1, 'time_taken': 2})
    assert _events(live, 'error')[0]['args'][0]['message'] == 'Unauthorized'
    live.emit('next_question', {'room_code': 'SOCK02'})
    assert _events(live, 'error')[0]['args'][0]['message'] == 'Unauthorized'
    live.disconnect()


def test_game_socket_leave_and_recover_require_membership(app, client, user, db):
    room = Room(code='SOCK03', name='Socket leave', host_id=user.id,
                status='playing', question_count=1)
    db.session.add_all([room, RoomPlayer(room=room, user_id=user.id)])
    db.session.commit()
    game_socket.game_states['SOCK03'] = {
        'match_id': 1,
        'questions': [],
        'current_question': 0,
        'answers': {},
        'scores': {user.id: 0},
        'streaks': {user.id: 0},
        'survival_lives': {user.id: 1},
        'eliminated': set(),
        'game_mode': 'classic',
    }

    live = socketio.test_client(app, flask_test_client=client)
    live.emit('leave_game', {'room_code': 'SOCK03'})
    assert _events(live, 'error')[0]['args'][0]['message'] == 'Unauthorized'
    live.emit('recover_game', {'room_code': 'SOCK03'})
    recovery = _events(live, 'game_recovery')[0]['args'][0]
    assert recovery == {'found': False, 'error': 'Unauthorized'}
    live.disconnect()
    game_socket.game_states.pop('SOCK03', None)
