"""Game Socket Events"""
from flask import request
from flask_socketio import emit
from flask_login import current_user
from datetime import datetime, date
from app.extensions import db
from app.models.room import Room, RoomPlayer, Match, Score
from app.models.question import Question
from app.models.user import User
from app.models.notification import Notification
from app.models.achievement import Achievement, UserAchievement
from app.models.quest import DailyQuest

game_states = {}

def register_game_events(socketio):

    @socketio.on('start_game')
    def handle_start_game(data):
        room_code = data.get('room_code')
        room = Room.query.filter_by(code=room_code).first()
        if not room or room.host_id != current_user.id:
            emit('error', {'message': 'Unauthorized'})
            return

        players = RoomPlayer.query.filter_by(room_id=room.id).all()
        if len(players) < 2:
            emit('error', {'message': 'Need at least 2 players'})
            return

        # Survival Mode-д амьдралыг оноох
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
            'started_at': datetime.utcnow().isoformat(),
            'game_mode': room.game_mode,
            'survival_lives': {p.user_id: p.survival_lives for p in players},
            'eliminated': set()
        }

        room.status = 'playing'
        room.started_at = datetime.utcnow()
        db.session.commit()

        emit('game_started', {
            'match_id': match.id,
            'total_questions': len(questions),
            'time_per_question': room.time_per_question,
            'game_mode': room.game_mode
        }, room=room_code)

    @socketio.on('request_question')
    def handle_request_question(data):
        room_code = data.get('room_code')
        if room_code not in game_states:
            emit('error', {'message': 'Game not found'})
            return

        state = game_states[room_code]
        q_idx = state['current_question']

        # Хасагдсан тоглогчийг шалгах (Survival)
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

        question_data = {
            'id': question['id'],
            'question_text': question['question_text'],
            'question_type': question['question_type'],
            'image_url': question.get('image_url'),
            'answers': [{'id': a['id'], 'answer_text': a['answer_text']} for a in question['answers']],
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

        if room_code not in game_states:
            return

        state = game_states[room_code]
        q_idx = state['current_question']
        question = state['questions'][q_idx]

        # Хасагдсан тоглогч хариулах ёсгүй
        if current_user.id in state.get('eliminated', set()):
            return

        correct_answer = next((a for a in question['answers'] if a['is_correct']), None)
        is_correct = correct_answer and correct_answer['id'] == answer_id

        room = Room.query.filter_by(code=room_code).first()
        base_score = 100
        time_bonus = max(0, int((room.time_per_question - time_taken) * 5))
        streak_bonus = state['streaks'].get(current_user.id, 0) * 10

        question_score = 0
        if is_correct:
            question_score = base_score + time_bonus + streak_bonus
            state['streaks'][current_user.id] = state['streaks'].get(current_user.id, 0) + 1
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

        # Survival Mode: буруу хариулсан бол амь хасах
        if not is_correct and state['game_mode'] == 'survival':
            state['survival_lives'][current_user.id] = state['survival_lives'].get(current_user.id, 1) - 1
            if state['survival_lives'][current_user.id] <= 0:
                state['eliminated'].add(current_user.id)
                emit('player_eliminated', {'user_id': current_user.id}, room=room_code)
                # Зөвхөн нэг тоглогч үлдсэн бол тоглоомыг дуусгах
                remaining = [uid for uid in state['survival_lives'] 
                            if uid not in state['eliminated'] and state['survival_lives'][uid] > 0]
                if len(remaining) <= 1:
                    _end_game(socketio, room_code)
                    return

        emit('answer_result', {
            'correct': is_correct,
            'correct_answer_id': correct_answer['id'] if correct_answer else None,
            'score_earned': question_score,
            'total_score': state['scores'][current_user.id],
            'streak': state['streaks'][current_user.id],
            'explanation': question.get('explanation', ''),
            'survival_lives': state['survival_lives'].get(current_user.id) if state['game_mode'] == 'survival' else None
        })

        # Бүгд хариулсан эсэхийг шалгах (хасагдсангүй тоглогчид)
        players = RoomPlayer.query.filter_by(room_id=room.id).all()
        all_answered = all(
            p.user_id in state.get('eliminated', set()) or
            (current_user.id in state['answers'] and q_idx in state['answers'].get(p.user_id, {}))
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
        if room_code not in game_states:
            return
        state = game_states[room_code]
        state['current_question'] += 1
        if state['current_question'] >= len(state['questions']):
            _end_game(socketio, room_code)
        else:
            emit('next_question_ready', {
                'question_number': state['current_question'] + 1
            }, room=room_code)

def _end_game(socketio, room_code):
    if room_code not in game_states:
        return

    state = game_states[room_code]
    room = Room.query.filter_by(code=room_code).first()
    match = Match.query.get(state['match_id'])

    if not room or not match:
        return

    players = RoomPlayer.query.filter_by(room_id=room.id).all()
    results = []
    winner_id = None
    max_score = -1

    for p in players:
        user = p.user
        # Хасагдсан тоглогчид оноо тооцохгүй (хэрэв survival)
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
        winner = User.query.get(winner_id)
        winner.wins += 1
        match.winner_id = winner_id
        from flask import current_app
        winner.add_coins(current_app.config['WIN_REWARD_COINS'], 'Match Win')

        winner_answers = state['answers'].get(winner_id, {})
        if all(a['correct'] for a in winner_answers.values()) and len(winner_answers) == len(state['questions']):
            winner.add_coins(current_app.config['PERFECT_GAME_BONUS'], 'Perfect Game Bonus')
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
    room.ended_at = datetime.utcnow()
    db.session.commit()

    del game_states[room_code]

    emit('game_over', {
        'results': results,
        'winner': results[0] if results else None,
        'total_questions': len(state['questions']),
        'game_mode': state.get('game_mode', 'classic')
    }, room=room_code)

    # Өдөр тутмын даалгаврыг шинэчлэх
    _update_daily_quests(state, players, winner_id)


def _update_daily_quests(state, players, winner_id):
    from datetime import date
    today = date.today()
    for p in players:
        # play_games даалгавар
        play_quests = DailyQuest.query.filter_by(
            user_id=p.user_id, quest_type='play_games', date_assigned=today, is_completed=False
        ).all()
        for q in play_quests:
            q.current_value += 1
            if q.current_value >= q.target_value:
                q.is_completed = True
                q.completed_at = datetime.utcnow()

        # win_games даалгавар
        if p.user_id == winner_id:
            win_quests = DailyQuest.query.filter_by(
                user_id=p.user_id, quest_type='win_games', date_assigned=today, is_completed=False
            ).all()
            for q in win_quests:
                q.current_value += 1
                if q.current_value >= q.target_value:
                    q.is_completed = True
                    q.completed_at = datetime.utcnow()

        # correct_answers даалгавар
        user_answers = state['answers'].get(p.user_id, {})
        correct_count = sum(1 for a in user_answers.values() if a['correct'])
        answer_quests = DailyQuest.query.filter_by(
            user_id=p.user_id, quest_type='correct_answers', date_assigned=today, is_completed=False
        ).all()
        for q in answer_quests:
            q.current_value += correct_count
            if q.current_value >= q.target_value:
                q.is_completed = True
                q.completed_at = datetime.utcnow()
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
            ua.unlocked_at = datetime.utcnow()
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