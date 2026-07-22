from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import random
from app.extensions import db

fortune_bp = Blueprint('fortune', __name__)

PRIZES = [
    {'name': '100 Coins', 'coins': 100, 'icon': '💰'},
    {'name': '500 Coins', 'coins': 500, 'icon': '🪙'},
    {'name': 'XP Booster', 'xp_boost': 50, 'icon': '🧪'},
    {'name': 'Common Box', 'box_rarity': 'common', 'icon': '📦'},
    {'name': 'Rare Box', 'box_rarity': 'rare', 'icon': '📦'},
    {'name': 'Jackpot', 'coins': 10000, 'aura_frame': 'golden', 'icon': '👑'},
]

@fortune_bp.route('/spin', methods=['POST'])
@login_required
def spin_wheel():
    # Өдөрт нэг удаа эсэхийг шалгах
    if current_user.last_fortune_spin:
        time_diff = datetime.utcnow() - current_user.last_fortune_spin
        if time_diff < timedelta(hours=22):
            hours_left = 22 - (time_diff.total_seconds() / 3600)
            return jsonify({'success': False, 'message': f'Come back in {int(hours_left)} hours.'})

    # Санамсаргүй шагнал сонгох
    prize = random.choice(PRIZES)

    # Шагналыг олгох
    if 'coins' in prize:
        current_user.add_coins(prize['coins'], 'Fortune Wheel')
    if 'xp_boost' in prize:
        current_user.add_xp(prize['xp_boost'])
    if 'box_rarity' in prize:
        from app.models.box import Box, UserBox
        box = Box.query.filter_by(rarity=prize['box_rarity']).first()
        if box:
            db.session.add(UserBox(user_id=current_user.id, box_id=box.id, quantity=1))

    current_user.last_fortune_spin = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'prize': prize})