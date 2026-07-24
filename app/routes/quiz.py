"""Quiz Routes (Chapter 3, 14, 16)"""
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.question import Category, Question, Answer
from app.models.room import Room, RoomPlayer
from app.utils.notify import send_notification

quiz_bp = Blueprint('quiz', __name__)


@quiz_bp.route('/categories')
def categories():
    cats = Category.query.filter_by(is_active=True).all()
    return jsonify([c.to_dict() for c in cats])


@quiz_bp.route('/questions')
def get_questions():
    category_id = request.args.get('category_id', type=int)
    difficulty = request.args.get('difficulty', 'mixed')
    limit = request.args.get('limit', 10, type=int)
    search = request.args.get('search', '').strip()

    query = Question.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if difficulty != 'mixed':
        query = query.filter_by(difficulty=difficulty)
    if search:
        query = query.filter(Question.question_text.ilike(f'%{search}%'))

    questions = query.order_by(db.func.random()).limit(limit).all()
    result = []
    for q in questions:
        answers = [{'id': a.id, 'answer_text': a.answer_text} for a in q.answers]
        result.append({
            'id': q.id,
            'question_text': q.question_text,
            'question_type': q.question_type,
            'image_url': q.image_url,
            'difficulty': q.difficulty,
            'category': q.category.name if q.category else None,
            'answers': answers
        })
    return jsonify(result)


@quiz_bp.route('/play/<room_code>')
@login_required
def play(room_code):
    room = Room.query.filter_by(code=room_code).first_or_404()
    player = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()
    if not player:
        flash('You are not in this room.', 'danger')
        return redirect(url_for('rooms.lobby'))
    return render_template('quiz/play.html', room=room)


@quiz_bp.route('/solo/play/<room_code>')
@login_required
def solo_play(room_code):
    room = Room.query.filter_by(code=room_code).first_or_404()
    if room.host_id != current_user.id or room.game_mode != 'classic':
        flash('Invalid solo session.', 'danger')
        return redirect(url_for('dashboard.index'))
    return render_template('quiz/solo_play.html', room=room)


@quiz_bp.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    """Check user answer, award XP, update stats. Uses Answer.get_correct_answer() properly."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    question_id = data.get('question_id')
    answer_id = data.get('answer_id')

    if not question_id or not answer_id:
        return jsonify({'error': 'Missing question_id or answer_id'}), 400

    question = Question.query.get(question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    # Use the model's get_correct_answer() method
    correct_answer = question.get_correct_answer()
    if not correct_answer:
        return jsonify({'error': 'No correct answer defined for this question'}), 500

    is_correct = (int(answer_id) == correct_answer.id)

    xp_earned = 0
    level_up = False
    old_lvl = current_user.level
    new_lvl = current_user.level

    if is_correct:
        xp_earned = 10
        level_up, old_lvl, new_lvl = current_user.add_xp(xp_earned)

        current_user.total_correct = (current_user.total_correct or 0) + 1
        current_user.total_questions = (current_user.total_questions or 0) + 1
        if current_user.total_questions > 0:
            current_user.accuracy = (current_user.total_correct / current_user.total_questions) * 100

        current_user.add_coins(5, 'Correct answer')
        db.session.commit()

        if level_up:
            send_notification(
                user_id=current_user.id,
                title='Level Up! 🎉',
                message=f'Congratulations! You are now level {new_lvl}!',
                notif_type='success'
            )
    else:
        current_user.total_questions = (current_user.total_questions or 0) + 1
        if current_user.total_questions > 0:
            current_user.accuracy = (current_user.total_correct / current_user.total_questions) * 100
        db.session.commit()

    return jsonify({
        'correct': is_correct,
        'xp_earned': xp_earned,
        'level_up': level_up,
        'old_level': old_lvl,
        'new_level': new_lvl,
        'total_coins': current_user.coins
    })


@quiz_bp.route('/solo/start', methods=['POST'])
@login_required
def start_solo():
    category_id = request.form.get('category_id', type=int)
    difficulty = request.form.get('difficulty', 'mixed')
    question_count = request.form.get('question_count', 10, type=int)

    query = Question.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if difficulty != 'mixed':
        query = query.filter_by(difficulty=difficulty)

    questions = query.order_by(db.func.random()).limit(question_count).all()
    if len(questions) < question_count:
        flash('Not enough questions available.', 'danger')
        return redirect(url_for('dashboard.index'))

    import random
    import string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    room = Room(
        code=code,
        name='Solo Practice',
        host_id=current_user.id,
        is_private=True,
        category_id=category_id if category_id else None,
        difficulty=difficulty,
        question_count=question_count,
        max_players=1,
        game_mode='classic',
        status='playing'
    )
    db.session.add(room)
    db.session.commit()

    return redirect(url_for('quiz.solo_play', room_code=code))


@quiz_bp.route('/solo/submit', methods=['POST'])
@login_required
def solo_submit():
    data = request.json
    current_user.games_played += 1
    current_user.total_correct += data.get('correct', 0)
    current_user.total_questions += data.get('total', 0)
    current_user.update_accuracy()
    current_user.add_xp(data.get('correct', 0) * 5)
    current_user.add_coins(data.get('correct', 0) * 2, 'Solo practice')
    db.session.commit()
    return jsonify({'success': True, 'xp_earned': data.get('correct', 0) * 5, 'coins_earned': data.get('correct', 0) * 2})


@quiz_bp.route('/solo/check_answer', methods=['POST'])
@login_required
def check_solo_answer():
    data = request.json
    question_id = data.get('question_id')
    answer_id = data.get('answer_id')
    question = Question.query.get(question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    correct_answer = question.get_correct_answer()
    is_correct = (correct_answer and correct_answer.id == answer_id)
    return jsonify({
        'correct': is_correct,
        'correct_answer_id': correct_answer.id if correct_answer else None
    })
