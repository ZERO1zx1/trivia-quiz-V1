from flask import Blueprint, render_template
from flask_login import login_required

from app.utils.daily_trivia import get_daily_questions

daily_trivia_bp = Blueprint('daily_trivia', __name__)

@daily_trivia_bp.route('/daily-trivia')
@login_required
def daily_trivia():
    """Display today's daily trivia questions."""
    questions = get_daily_questions()
    question_data = []
    for q in questions:
        question_data.append({
            'id': q.id,
            'question_text': q.question_text,
            'question_type': q.question_type,
            'image_url': q.image_url,
            'difficulty': q.difficulty,
            'category': q.category.name if q.category else 'General',
            'answers': [{'id': a.id, 'answer_text': a.answer_text} for a in q.answers]
        })
    return render_template('quiz/daily_trivia.html', questions=question_data)
