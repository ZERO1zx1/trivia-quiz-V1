import random
from datetime import date
from app.extensions import db
from app.models.quest import DailyQuest

def assign_daily_quests(user):
    """Хэрэглэгчид өнөөдрийн даалгавруудыг үүсгэх"""
    today = date.today()
    existing = DailyQuest.query.filter_by(user_id=user.id, date_assigned=today).first()
    if existing:
        return  # Өнөөдрийн даалгавар аль хэдийн үүссэн

    quests = [
        {'type': 'play_games', 'target': 3, 'reward_coins': 30, 'reward_xp': 15},
        {'type': 'win_games', 'target': 1, 'reward_coins': 50, 'reward_xp': 25},
        {'type': 'correct_answers', 'target': 15, 'reward_coins': 40, 'reward_xp': 20}
    ]
    for q in quests:
        db.session.add(DailyQuest(
            user_id=user.id,
            quest_type=q['type'],
            target_value=q['target'],
            reward_coins=q['reward_coins'],
            reward_xp=q['reward_xp'],
            date_assigned=today
        ))
    db.session.commit()