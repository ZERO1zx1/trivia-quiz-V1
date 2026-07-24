from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user_question import UserQuestion
from app.models.question import Question, Answer, Category
from app.models.room import Room

user_q_bp = Blueprint('user_questions', __name__)

@user_q_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_question():
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        correct_answer = request.form.get('correct_answer')
        wrong1 = request.form.get('wrong_answer1')
        wrong2 = request.form.get('wrong_answer2')
        wrong3 = request.form.get('wrong_answer3')
        category_id = request.form.get('category_id', type=int)
        difficulty = request.form.get('difficulty', 'medium')

        if not all([question_text, correct_answer, wrong1, wrong2, wrong3]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('user_questions.submit_question'))

        uq = UserQuestion(
            user_id=current_user.id,
            question_text=question_text,
            correct_answer=correct_answer,
            wrong_answer1=wrong1,
            wrong_answer2=wrong2,
            wrong_answer3=wrong3,
            category_id=category_id,
            difficulty=difficulty
        )
        db.session.add(uq)
        db.session.commit()
        flash('Question submitted! It will be reviewed by an admin.', 'success')
        return redirect(url_for('dashboard.index'))

    categories = Category.query.filter_by(is_active=True).all()
    return render_template('questions/submit.html', categories=categories)

@user_q_bp.route('/create-quiz', methods=['POST'])
@login_required
def create_quiz():
    """Create a custom quiz room from user-submitted questions."""
    data = request.json
    if not data or 'questions' not in data:
        return jsonify({'error': 'No questions provided'}), 400

    # Generate unique room code
    import random, string
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Room.query.filter_by(code=code).first():
            break

    room = Room(
        name='Custom Quiz',
        code=code,
        host_id=current_user.id,
        is_private=True,
        max_players=data.get('max_players', 8),
        question_count=len(data['questions']),
        game_mode='classic',
        status='waiting'
    )
    db.session.add(room)
    db.session.flush()

    for item in data['questions']:
        q = Question(
            question_text=item['text'],
            difficulty='custom',
            category_id=item.get('category_id', 1),
            question_type='multiple_choice',
            is_active=True
        )
        db.session.add(q)
        db.session.flush()
        db.session.add(Answer(question_id=q.id, answer_text=item['correct'], is_correct=True))
        db.session.add(Answer(question_id=q.id, answer_text=item.get('wrong1', ''), is_correct=False))
        db.session.add(Answer(question_id=q.id, answer_text=item.get('wrong2', ''), is_correct=False))
        db.session.add(Answer(question_id=q.id, answer_text=item.get('wrong3', ''), is_correct=False))

    db.session.commit()
    return jsonify({'quiz_code': code})
