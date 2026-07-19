from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user_question import UserQuestion
from app.models.question import Question, Answer

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

    from app.models.question import Category
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('questions/submit.html', categories=categories)