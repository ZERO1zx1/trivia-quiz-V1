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

    if 'coins' in prize:
        current_user.add_coins(prize['coins'], 'Fortune Wheel')
    if 'xp_boost' in prize:
        current_user.add_xp(prize['xp_boost'])
    if 'box_rarity' in prize:
        box = Box.query.filter_by(rarity=prize['box_rarity']).first()
        if box:
            user_box = UserBox(user_id=current_user.id, box_id=box.id, quantity=1)
            db.session.add(user_box)
    # ★ JACKPOT: Aura Frame ★
    if 'aura_frame' in prize:
        # ShopItem-с "golden_aura_frame" гэх item-г хайх (эсвэл шинээр үүсгэх)
        frame_item = ShopItem.query.filter_by(name='Golden Aura Frame').first()
        if not frame_item:
            frame_item = ShopItem(
                name='Golden Aura Frame',
                description='Exclusive golden aura frame from Jackpot',
                price=0,
                item_type='frame',
                image_url='/static/shop/frame_golden_aura.png',
                is_active=True
            )
            db.session.add(frame_item)
            db.session.flush()
        # Инвентарьт нэмэх
        inv = UserInventory.query.filter_by(user_id=current_user.id, item_id=frame_item.id).first()
        if inv:
            inv.quantity += 1
        else:
            inv = UserInventory(user_id=current_user.id, item_id=frame_item.id, quantity=1)
            db.session.add(inv)

    current_user.last_fortune_spin = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'prize': prize})