"""Quiz Routes"""
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.question import Category, Question, Answer
from app.models.room import Room, RoomPlayer
from app.utils.notify import send_notification  # дээд хэсэгт импорт хийх

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

    query = Question.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if difficulty != 'mixed':
        query = query.filter_by(difficulty=difficulty)

    questions = query.order_by(db.func.random()).limit(limit).all()
    return jsonify([q.to_dict() for q in questions])

@quiz_bp.route('/play/<room_code>')
@login_required
def play(room_code):
    room = Room.query.filter_by(code=room_code).first_or_404()
    player = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()
    if not player:
        flash('You are not in this room.', 'danger')
        return redirect(url_for('rooms.lobby'))
    return render_template('quiz/play.html', room=room)

@quiz_bp.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    """Хэрэглэгчийн хариултыг шалгах, XP нэмэх, level up хийх"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    question_id = data.get('question_id')
    answer_id = data.get('answer_id')
    room_code = data.get('room_code')

    if not question_id or not answer_id:
        return jsonify({'error': 'Missing question_id or answer_id'}), 400

    # Асуулт, зөв хариултыг олох
    question = Question.query.get(question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    # Хариултын зөв эсэхийг шалгах (таны моделоос хамаарч өөрчилж болно)
    # Жишээ: Question.correct_answer_id гэсэн талбар бий гэж үзье
    correct_answer_id = question.correct_answer_id if hasattr(question, 'correct_answer_id') else None
    if correct_answer_id is None:
        return jsonify({'error': 'No correct answer defined for this question'}), 500

    is_correct = (int(answer_id) == correct_answer_id)

    xp_earned = 0
    level_up = False
    old_lvl = current_user.level
    new_lvl = current_user.level

    if is_correct:
        xp_earned = 10  # Нэг зөв хариултанд 10 XP
        level_up, old_lvl, new_lvl = current_user.add_xp(xp_earned)

        # Хэрэглэгчийн статистик шинэчлэх
        current_user.total_correct = (current_user.total_correct or 0) + 1
        current_user.total_questions = (current_user.total_questions or 0) + 1
        # accuracy шинэчлэх
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
        # Буруу хариулт: статистик шинэчлэх
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