from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import date
from app.extensions import db
from app.models.quest import DailyQuest
from app.utils.quests import assign_daily_quests

quests_bp = Blueprint('quests', __name__)

@quests_bp.route('/daily-quests')
@login_required
def get_daily_quests():
    assign_daily_quests(current_user)  # Өнөөдрийн даалгавруудыг баталгаажуулах
    today = date.today()
    quests = DailyQuest.query.filter_by(user_id=current_user.id, date_assigned=today).all()
    return jsonify([q.to_dict() for q in quests])

@quests_bp.route('/daily-quests/<int:quest_id>/claim', methods=['POST'])
@login_required
def claim_quest_reward(quest_id):
    quest = DailyQuest.query.get_or_404(quest_id)
    if quest.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    if not quest.is_completed or quest.is_claimed:
        return jsonify({'error': 'Cannot claim this reward'}), 400

    # Шагнал олгох
    current_user.add_coins(quest.reward_coins, f'Daily Quest: {quest.quest_type}')
    current_user.add_xp(quest.reward_xp)
    quest.is_claimed = True
    db.session.commit()

    return jsonify({
        'success': True,
        'reward_coins': quest.reward_coins,
        'reward_xp': quest.reward_xp,
        'new_coins': current_user.coins,
        'new_xp': current_user.xp
    })