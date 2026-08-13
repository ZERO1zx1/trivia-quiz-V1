"""Game Socket Events"""
from flask import request
from flask_socketio import emit
from flask_login import current_user
from datetime import datetime, date
import random
from app.extensions import db, utcnow
from app.models.room import GameSnapshot, Room, RoomPlayer, Match, Score
from app.models.question import Question
from app.models.user import User
from app.models.notification import Notification
from app.models.achievement import Achievement, UserAchievement
from app.models.quest import DailyQuest

game_states = {}


def _json_state(state):
    payload = dict(state)
    payload['eliminated'] = list(state.get('eliminated', set()))
    return payload


def _restore_state(payload):
    state = dict(payload)
    state['eliminated'] = set(
        int(value) for value in state.get('eliminated', []))
    for key in ('scores', 'streaks', 'survival_lives'):
        state[key] = {
            int(user_id): value
            for user_id, value in state.get(key, {}).items()
        }
    state['answers'] = {
        int(user_id): {
            int(index): answer for index, answer in answers.items()
        }
        for user_id, answers in state.get('answers', {}).items()
    }
    return state


def _save_snapshot(room_code):
    state = game_states.get(room_code)
    room = Room.query.filter_by(code=room_code).first()
    if not state or not room:
        return
    snapshot = GameSnapshot.query.filter_by(room_id=room.id).first()
    if snapshot:
        snapshot.version += 1
        snapshot.state = _json_state(state)
        snapshot.is_active = True
    else:
        db.session.add(GameSnapshot(
            room_id=room.id, room_code=room_code,
            state=_json_state(state), is_active=True))
    db.session.commit()


def _state(room_code):
    state = game_states.get(room_code)
    if state:
        return state
    snapshot = GameSnapshot.query.filter_by(
        room_code=room_code, is_active=True).first()
    if snapshot:
        state = _restore_state(snapshot.state)
        game_states[room_code] = state
    return state

def register_game_events(socketio):

    @socketio.on('start_game')
    def handle_start_game(data):
        """Initialize actual game state from questions and start gameplay."""
        room_code = data.get('room_code')
        room = Room.query.filter_by(code=room_code).first()
        if not room or room.host_id != current_user.id:
            emit('error', {'message': 'Unauthorized'})
            return

        players = RoomPlayer.query.filter_by(room_id=room.id).all()
        if len(players) < 2:
            emit('error', {'message': 'Need at least 2 players'})
            return

        if room.game_mode == 'survival':
            for p in players:
                p.survival_lives = room.survival_lives
            db.session.commit()

        query = Question.query.filter_by(is_active=True)
        if room.category_id:
            query = query.filter_by(category_id=room.category_id)
        if room.difficulty != 'mixed':
            query = query.filter_by(difficulty=room.difficulty)

        questions = query.order_by(db.func.random()).limit(room.question_count).all()
        if len(questions) < room.question_count:
            emit('error', {'message': 'Not enough questions available'})
            return

        match = Match(room_id=room.id, category_id=room.category_id,
                     difficulty=room.difficulty, question_count=room.question_count)
        db.session.add(match)
        db.session.flush()

        game_states[room_code] = {
            'match_id': match.id,
            'questions': [q.to_dict() for q in questions],
            'current_question': 0,
            'answers': {},
            'scores': {p.user_id: 0 for p in players},
            'streaks': {p.user_id: 0 for p in players},
            'started_at': utcnow().isoformat(),
            'game_mode': room.game_mode,
            'survival_lives': {p.user_id: p.survival_lives for p in players},
            'eliminated': set()
        }

        room.status = 'playing'
        room.started_at = utcnow()
        db.session.commit()
        _save_snapshot(room_code)

        emit('game_started', {
            'match_id': match.id,
            'total_questions': len(questions),
            'time_per_question': room.time_per_question,
            'game_mode': room.game_mode
        }, room=room_code)

    @socketio.on('request_question')
    def handle_request_question(data):
        room_code = data.get('room_code')
        state = _state(room_code)
        if not state:
            emit('error', {'message': 'Game not found'})
            return
        q_idx = state['current_question']

        if current_user.id in state.get('eliminated', set()):
            emit('error', {'message': 'You have been eliminated'})
            return

        if q_idx >= len(state['questions']):
            _end_game(socketio, room_code)
            return

        question = state['questions'][q_idx]
        room = Room.query.filter_by(code=room_code).first()
        time_limit = room.time_per_question
        if state['game_mode'] == 'time_attack':
            time_limit = room.time_attack_duration

        # ХАРИУЛТУУДЫГ ХОЛИХ (shuffle)
        answers = question['answers'][:]
        random.shuffle(answers)

        question_data = {
            'id': question['id'],
            'question_text': question['question_text'],
            'question_type': question['question_type'],
            'image_url': question.get('image_url'),
            'answers': [{'id': a['id'], 'answer_text': a['answer_text']} for a in answers],
            'question_number': q_idx + 1,
            'total_questions': len(state['questions']),
            'time_limit': time_limit,
            'game_mode': state['game_mode']
        }
        emit('question', question_data, room=room_code)

    @socketio.on('submit_answer')
    def handle_submit_answer(data):
        room_code = data.get('room_code')
        answer_id = data.get('answer_id')
        time_taken = data.get('time_taken', 0)

        state = _state(room_code)
        if not state:
            return
        q_idx = state['current_question']
        question = state['questions'][q_idx]

        if current_user.id in state.get('eliminated', set()):
            return

        correct_answer = next((a for a in question['answers'] if a['is_correct']), None)
        is_correct = correct_answer and correct_answer['id'] == answer_id

        # Anti-Cheat Logic: If answer is too fast (e.g., < 0.5s)
        if time_taken < 0.5:
            emit('error', {'message': 'Suspiciously fast answer! Anti-cheat triggered.'})
            return

        room = Room.query.filter_by(code=room_code).first()
        # Decreasing Point Timer Logic
        # Start with 1000, decrease by 50 per second
        # Safety: ensure time_taken is reasonable
        safe_time = max(0.5, min(time_taken, 30.0))
        base_points = 1000
        time_penalty = int(safe_time * 50)
        calculated_base = max(100, base_points - time_penalty)
        
        # Combo Multiplier System
        # 1x -> 1.5x -> 2x -> 3x
        streak = state['streaks'].get(current_user.id, 0)
        multiplier = 1.0
        if streak >= 10: multiplier = 3.0
        elif streak >= 5: multiplier = 2.0
        elif streak >= 2: multiplier = 1.5

        question_score = 0
        if is_correct:
            question_score = int(calculated_base * multiplier)
            state['streaks'][current_user.id] = streak + 1

            multiplier = current_user.coin_multiplier if current_user.is_premium else 1
            coins_earned = 5 * multiplier
            current_user.add_coins(coins_earned, 'Correct answer')
        else:
            state['streaks'][current_user.id] = 0

        state['scores'][current_user.id] = state['scores'].get(current_user.id, 0) + question_score

        if current_user.id not in state['answers']:
            state['answers'][current_user.id] = {}
        state['answers'][current_user.id][q_idx] = {
            'answer_id': answer_id,
            'time_taken': time_taken,
            'correct': is_correct,
            'score': question_score
        }
        _save_snapshot(room_code)

        if not is_correct and state['game_mode'] == 'survival':
            state['survival_lives'][current_user.id] = state['survival_lives'].get(current_user.id, 1) - 1
            if state['survival_lives'][current_user.id] <= 0:
                state['eliminated'].add(current_user.id)
                emit('player_eliminated', {'user_id': current_user.id}, room=room_code)
                remaining = [uid for uid in state['survival_lives'] 
                            if uid not in state['eliminated'] and state['survival_lives'][uid] > 0]
                if len(remaining) <= 1:
                    _end_game(socketio, room_code)
                    return

        # ЗӨВ ХАРИУЛТЫН ID-Г ХУВИЙН ЗУРВАСАНД ИЛГЭЭХГҮЙ
        emit('answer_result', {
            'correct': is_correct,
            'score_earned': question_score,
            'total_score': state['scores'][current_user.id],
            'streak': state['streaks'][current_user.id],
            'explanation': question.get('explanation', ''),
            'survival_lives': state['survival_lives'].get(current_user.id) if state['game_mode'] == 'survival' else None
        })

        players = RoomPlayer.query.filter_by(room_id=room.id).all()
        all_answered = all(
            p.user_id in state.get('eliminated', set()) or
            (p.user_id in state['answers'] and q_idx in state['answers'].get(p.user_id, {}))
            for p in players
        )

        if all_answered:
            leaderboard = []
            for p in players:
                leaderboard.append({
                    'user_id': p.user_id,
                    'username': p.user.username if p.user else 'Unknown',
                    'avatar': p.user.avatar_url if p.user else None,
                    'score': state['scores'].get(p.user_id, 0),
                    'streak': state['streaks'].get(p.user_id, 0),
                    'survival_lives': state['survival_lives'].get(p.user_id) if state['game_mode'] == 'survival' else None
                })
            leaderboard.sort(key=lambda x: x['score'], reverse=True)
            emit('round_results', {
                'leaderboard': leaderboard,
                'correct_answer_id': correct_answer['id'] if correct_answer else None
            }, room=room_code)

    @socketio.on('next_question')
    def handle_next_question(data):
        room_code = data.get('room_code')
        state = _state(room_code)
        if not state:
            return
        state['current_question'] += 1
        _save_snapshot(room_code)
        if state['current_question'] >= len(state['questions']):
            _end_game(socketio, room_code)
        else:
            emit('next_question_ready', {
                'question_number': state['current_question'] + 1
            }, room=room_code)

    # АДМИН КОМАНДУУД
    @socketio.on('skip_question')
    def handle_skip_question(data):
        room_code = data.get('room_code')
        state = _state(room_code)
        if not state:
            return
        if current_user.role not in ('admin', 'moderator', 'owner'):
            emit('error', {'message': 'Unauthorized'})
            return
        state['current_question'] += 1
        _save_snapshot(room_code)
        if state['current_question'] >= len(state['questions']):
            _end_game(socketio, room_code)
        else:
            emit('next_question_ready', {
                'question_number': state['current_question'] + 1,
                'skipped_by': current_user.username
            }, room=room_code)

    # Keep the lobby host command (`kick_player`) distinct. Registering two
    # handlers with the same event silently replaced one of them.
    @socketio.on('game_admin_kick_player')
    def handle_kick_player(data):
        room_code = data.get('room_code')
        target_id = data.get('user_id')
        if current_user.role not in ('admin', 'moderator', 'owner'):
            emit('error', {'message': 'Unauthorized'})
            return
        room = Room.query.filter_by(code=room_code).first()
        if not room:
            return
        player = RoomPlayer.query.filter_by(room_id=room.id, user_id=target_id).first()
        if player:
            db.session.delete(player)
            db.session.commit()
            emit('player_kicked', {
                'user_id': target_id,
                'kicked_by': current_user.username,
                'players': [p.to_dict() for p in RoomPlayer.query.filter_by(room_id=room.id).all()]
            }, room=room_code)
            emit('kicked_from_room', {'room_code': room_code}, room=request.sid)

    @socketio.on('leave_game')
    def handle_leave_game(data):
        """Player leaves during an active game."""
        room_code = data.get('room_code')
        state = _state(room_code)
        if not state:
            return
        state['eliminated'].add(current_user.id)
        _save_snapshot(room_code)

        # Check if enough players remain
        room = Room.query.filter_by(code=room_code).first()
        players = RoomPlayer.query.filter_by(room_id=room.id).all()
        remaining = [p.user_id for p in players if p.user_id not in state['eliminated']]
        
        if len(remaining) <= 1:
            _end_game(socketio, room_code)
        else:
            emit('player_left_game', {
                'user_id': current_user.id,
                'username': current_user.username
            }, room=room_code)

    @socketio.on('recover_game')
    def handle_recover_game(data):
        """Restore the latest committed state after reconnect or restart."""
        room_code = data.get('room_code')
        state = _state(room_code)
        room = Room.query.filter_by(code=room_code).first()
        if not state or not room:
            emit('game_recovery', {'found': False})
            return
        player = RoomPlayer.query.filter_by(
            room_id=room.id, user_id=current_user.id).first()
        if not player:
            emit('game_recovery', {'found': False, 'error': 'Unauthorized'})
            return
        emit('game_recovery', {
            'found': True,
            'room_code': room_code,
            'match_id': state['match_id'],
            'current_question': state['current_question'],
            'total_questions': len(state['questions']),
            'score': state['scores'].get(current_user.id, 0),
            'streak': state['streaks'].get(current_user.id, 0),
            'game_mode': state['game_mode'],
        })


def _end_game(socketio, room_code):
    state = _state(room_code)
    if not state:
        return

    room = Room.query.filter_by(code=room_code).first()
    match = db.session.get(Match, state['match_id'])

    if not room or not match:
        return

    players = RoomPlayer.query.filter_by(room_id=room.id).all()
    results = []
    winner_id = None
    max_score = -1

    for p in players:
        user = p.user
        user_answers = state['answers'].get(p.user_id, {})
        correct_count = sum(1 for a in user_answers.values() if a['correct'])
        total_time = sum(a['time_taken'] for a in user_answers.values())
        final_score = state['scores'].get(p.user_id, 0)

        user.games_played += 1
        user.total_correct += correct_count
        user.total_questions += len(state['questions'])
        user.update_accuracy()

        if final_score > max_score and p.user_id not in state.get('eliminated', set()):
            max_score = final_score
            winner_id = p.user_id

        score = Score(
            match_id=match.id,
            user_id=p.user_id,
            score=final_score,
            correct_answers=correct_count,
            total_questions=len(state['questions']),
            accuracy=(correct_count / len(state['questions'])) * 100 if state['questions'] else 0,
            avg_time=total_time / len(user_answers) if user_answers else 0,
            max_streak=state['streaks'].get(p.user_id, 0)
        )
        db.session.add(score)

        results.append({
            'user_id': p.user_id,
            'username': user.username,
            'avatar': user.avatar_url,
            'score': final_score,
            'correct': correct_count,
            'accuracy': round((correct_count / len(state['questions'])) * 100, 1) if state['questions'] else 0,
            'streak': state['streaks'].get(p.user_id, 0),
            'eliminated': p.user_id in state.get('eliminated', set())
        })

    if winner_id:
        winner = db.session.get(User, winner_id)
        winner.wins += 1
        match.winner_id = winner_id
        
        # Elo Rating System Logic
        # Simplified: Winner gains 20, Losers lose 10
        winner.elo_rating += 20
        for p in players:
            if p.user_id != winner_id:
                p.user.elo_rating = max(0, p.user.elo_rating - 10)

        from flask import current_app
        winner.add_coins(current_app.config.get('WIN_REWARD_COINS', 100), 'Match Win')

        winner_answers = state['answers'].get(winner_id, {})
        if all(a['correct'] for a in winner_answers.values()) and len(winner_answers) == len(state['questions']):
            winner.add_coins(current_app.config.get('PERFECT_GAME_BONUS', 50), 'Perfect Game Bonus')
            winner.xp += 100

        winner.xp += 50
        winner.add_coins(25, 'Participation')
        _check_achievements(winner)

    for p in players:
        if p.user_id != winner_id:
            p.user.losses += 1
            p.user.xp += 10
            p.user.add_coins(10, 'Participation')

    results.sort(key=lambda x: x['score'], reverse=True)
    room.status = 'finished'
    room.ended_at = utcnow()
    db.session.commit()

    snapshot = GameSnapshot.query.filter_by(room_code=room_code).first()
    if snapshot:
        snapshot.is_active = False
        snapshot.state = _json_state(state)
        snapshot.version += 1
        db.session.commit()

    game_states.pop(room_code, None)

    emit('game_over', {
        'results': results,
        'winner': results[0] if results else None,
        'total_questions': len(state['questions']),
        'game_mode': state.get('game_mode', 'classic')
    }, room=room_code)

    _update_daily_quests(state, players, winner_id)


def _update_daily_quests(state, players, winner_id):
    today = date.today()
    for p in players:
        play_quests = DailyQuest.query.filter_by(
            user_id=p.user_id, quest_type='play_games', date_assigned=today, is_completed=False
        ).all()
        for q in play_quests:
            q.current_value += 1
            if q.current_value >= q.target_value:
                q.is_completed = True
                q.completed_at = utcnow()

        if p.user_id == winner_id:
            win_quests = DailyQuest.query.filter_by(
                user_id=p.user_id, quest_type='win_games', date_assigned=today, is_completed=False
            ).all()
            for q in win_quests:
                q.current_value += 1
                if q.current_value >= q.target_value:
                    q.is_completed = True
                    q.completed_at = utcnow()

        user_answers = state['answers'].get(p.user_id, {})
        correct_count = sum(1 for a in user_answers.values() if a['correct'])
        answer_quests = DailyQuest.query.filter_by(
            user_id=p.user_id, quest_type='correct_answers', date_assigned=today, is_completed=False
        ).all()
        for q in answer_quests:
            q.current_value += correct_count
            if q.current_value >= q.target_value:
                q.is_completed = True
                q.completed_at = utcnow()
    db.session.commit()


def _check_achievements(user):
    achievements = Achievement.query.all()
    for ach in achievements:
        ua = UserAchievement.query.filter_by(user_id=user.id, achievement_id=ach.id).first()
        if not ua or ua.is_unlocked:
            continue
        
        if ach.check_requirement(user):
            ua.progress = ach.requirement_value
            ua.is_unlocked = True
            ua.unlocked_at = utcnow()
            user.xp += ach.xp_reward
            user.add_coins(ach.coin_reward, f'Achievement: {ach.name}')
            notif = Notification(
                user_id=user.id,
                type='achievement',
                title='Achievement Unlocked!',
                message=f'You unlocked "{ach.name}"! +{ach.xp_reward} XP, +{ach.coin_reward} Coins'
            )
            db.session.add(notif)
    db.session.commit()
