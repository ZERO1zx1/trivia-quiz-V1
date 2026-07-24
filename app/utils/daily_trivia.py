"""Daily Trivia Utilities (Chapter 21)"""
from datetime import date
from app.models.question import Question


def get_daily_questions(category_id=None, count=10):
    """Get questions for today's daily trivia.
    Uses a deterministic seed based on the date so all users get the same questions.
    Returns list of Question objects (route handles serialization).
    """
    today = date.today()
    import random
    random.seed(today.toordinal())
    
    query = Question.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    all_questions = query.all()
    if len(all_questions) < count:
        count = len(all_questions)
    
    selected = random.sample(all_questions, count)
    return selected
