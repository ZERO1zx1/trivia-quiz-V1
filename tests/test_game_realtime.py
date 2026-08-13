from app.extensions import db, socketio
from app.models.question import Answer, Category, Question
from app.models.room import GameSnapshot, Match, Room, RoomPlayer, Score
from app.sockets import game_socket
from conftest import make_user


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
