"""Daily Quest Assignment Utilities (Chapter 20)"""
import random
from datetime import date
from app.extensions import db
from app.models.quest import DailyQuest

QUEST_TEMPLATES = [
    # (quest_type, target, reward_coins, reward_xp)
    ('play_games', 2, 50, 25),
    ('play_games', 3, 75, 35),
    ('play_games', 5, 100, 50),
    ('win_games', 1, 75, 30),
    ('win_games', 2, 100, 45),
    ('correct_answers', 10, 60, 30),
    ('correct_answers', 20, 100, 50),
    ('correct_answers', 50, 200, 100),
]


def assign_daily_quests(user, count=3):
    """Assign daily quests to a user if they don't have any for today.
    Randomly selects from quest templates to add variety.
    """
    today = date.today()
    existing_count = DailyQuest.query.filter_by(user_id=user.id, date_assigned=today).count()
    
    if existing_count >= count:
        return

    # Get quests the user doesn't already have today
    available = list(QUEST_TEMPLATES)
    random.shuffle(available)
    
    assigned = 0
    for template in available:
        if assigned >= count - existing_count:
            break
        quest_type, target, coins, xp = template
        quest = DailyQuest(
            user_id=user.id,
            quest_type=quest_type,
            target_value=target,
            reward_coins=coins,
            reward_xp=xp,
            date_assigned=today
        )
        db.session.add(quest)
        assigned += 1
    
    db.session.commit()
