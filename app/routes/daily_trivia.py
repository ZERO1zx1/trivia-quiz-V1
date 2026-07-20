from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.utils.daily_trivia import get_daily_questions

daily_trivia_bp = Blueprint('daily_trivia', __name__)

@daily_trivia_bp.route('/daily-trivia')
@login_required
def daily_trivia():
    questions = get_daily_questions()
    return render_template('quiz/daily_trivia.html', questions=questions)