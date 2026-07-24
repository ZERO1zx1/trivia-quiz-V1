"""Fortune Wheel Route (Chapter 19)"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import random
from app.extensions import db

fortune_bp = Blueprint('fortune', __name__)

# Weighted prizes: (name, data, weight)
# Higher weight = more common
PRIZES = [
    {'name': '50 Coins', 'coins': 50, 'icon': '💰', 'weight': 30},
    {'name': '100 Coins', 'coins': 100, 'icon': '💰', 'weight': 25},
    {'name': '250 Coins', 'coins': 250, 'icon': '🪙', 'weight': 15},
    {'name': 'XP Booster', 'xp_boost': 50, 'icon': '🧪', 'weight': 12},
    {'name': 'Common Box', 'box_rarity': 'common', 'icon': '📦', 'weight': 10},
    {'name': 'Rare Box', 'box_rarity': 'rare', 'icon': '📦', 'weight': 5},
    {'name': 'Epic Box', 'box_rarity': 'epic', 'icon': '🎁', 'weight': 2},
    {'name': 'Jackpot', 'coins': 10000, 'aura_frame': 'golden', 'icon': '👑', 'weight': 1},
]


def weighted_choice(items):
    """Select a random item based on weights."""
    weights = [item.get('weight', 1) for item in items]
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for item in items:
        cumulative += item.get('weight', 1)
        if r <= cumulative:
            return item
    return items[-1]


@fortune_bp.route('/spin', methods=['POST'])
@login_required
def spin_wheel():
    """Spin the fortune wheel once per 22 hours. Awards prizes."""
    # Check cooldown
    if current_user.last_fortune_spin:
        time_diff = datetime.utcnow() - current_user.last_fortune_spin
        if time_diff < timedelta(hours=22):
            hours_left = round(22 - (time_diff.total_seconds() / 3600), 1)
            return jsonify({'success': False, 'message': f'Come back in {hours_left} hours.'})

    # Weighted random prize
    prize = weighted_choice(PRIZES)

    # Remove weight from response
    prize_response = {k: v for k, v in prize.items() if k != 'weight'}

    # Award prize
    if 'coins' in prize:
        current_user.add_coins(prize['coins'], 'Fortune Wheel')
    if 'xp_boost' in prize:
        current_user.add_xp(prize['xp_boost'])
    if 'box_rarity' in prize:
        try:
            from app.models.box import Box, UserBox
            box = Box.query.filter_by(rarity=prize['box_rarity']).first()
            if box:
                existing = UserBox.query.filter_by(user_id=current_user.id, box_id=box.id).first()
                if existing:
                    existing.quantity += 1
                else:
                    db.session.add(UserBox(user_id=current_user.id, box_id=box.id, quantity=1))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to award box: {e}")

    current_user.last_fortune_spin = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'prize': prize_response})
