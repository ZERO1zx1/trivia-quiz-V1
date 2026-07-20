from datetime import date
from app.models.question import Question

def get_daily_questions(category_id=None, count=10):
    today = date.today()
    # Өдрийн асуултуудыг тодорхой seed-ээр сонгох (өдөр бүр ижил)
    import random
    random.seed(today.toordinal())
    
    query = Question.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    all_ids = [q.id for q in query.all()]
    if len(all_ids) < count:
        count = len(all_ids)
    selected_ids = random.sample(all_ids, count)
    
    return Question.query.filter(Question.id.in_(selected_ids)).all()