"""Premium-specific API endpoints"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.extensions import db
from app.utils.decorators import premium_required

premium_api_bp = Blueprint('premium_api', __name__)

@premium_api_bp.route('/daily-premium-reward', methods=['POST'])
@login_required
@premium_required
def claim_daily_premium_reward():
    """Өдөр бүр 3,000 coin авах (зөвхөн Premium)"""
    today = datetime.utcnow().date()
    if current_user.daily_premium_reward_claimed_at:
        last_claim = current_user.daily_premium_reward_claimed_at.date()
        if last_claim == today:
            return jsonify({'success': False, 'message': 'Already claimed today.'})

    reward = 3000
    current_user.add_coins(reward, 'Daily Premium Reward')
    current_user.daily_premium_reward_claimed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'reward': reward, 'new_coins': current_user.coins})

@premium_api_bp.route('/coin-multiplier-info')
@login_required
def coin_multiplier_info():
    """Premium үед 3x үржүүлэгч байгаа эсэхийг буцаана"""
    return jsonify({
        'multiplier': current_user.coin_multiplier,
        'is_premium': current_user.is_premium
    })

# Premium Shop Items
@premium_api_bp.route('/premium-items')
@login_required
def get_premium_items():
    from app.models.shop import ShopItem
    items = ShopItem.query.filter_by(premium_only=True, is_active=True).all()
    return jsonify([item.to_dict() for item in items])