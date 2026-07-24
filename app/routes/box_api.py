"""Box opening API"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
import random
from app.extensions import db
from app.models.box import UserBox, Box
from app.models.shop import ShopItem, UserInventory

box_api_bp = Blueprint('box_api', __name__)   # <-- ЭНЭ МӨР НЭМЭГДСЭН

@box_api_bp.route('/open-box/<int:box_id>', methods=['POST'])
@login_required
def open_box(box_id):
    """Авдар нээх (atomic)"""
    user_box = UserBox.query.with_for_update().filter_by(
        id=box_id, user_id=current_user.id, is_opened=False
    ).first()

    if not user_box:
        return jsonify({'success': False, 'message': 'Box not found or already opened.'})

    loot = generate_loot(user_box.box.rarity)

    user_box.is_opened = True
    user_box.opened_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'loot': loot})


def generate_loot(rarity):
    """Санамсаргүй item, coins, XP үүсгэх"""
    loot_table = {
        'common': [
            {'type': 'coins', 'amount': 50},
            {'type': 'xp', 'amount': 10},
        ],
        'rare': [
            {'type': 'coins', 'amount': 200},
            {'type': 'xp', 'amount': 50},
            {'type': 'item', 'name': 'Silver Frame', 'item_type': 'frame'},
        ],
        'epic': [
            {'type': 'coins', 'amount': 500},
            {'type': 'xp', 'amount': 100},
            {'type': 'item', 'name': 'Epic Badge', 'item_type': 'badge'},
        ],
        'legendary': [
            {'type': 'coins', 'amount': 2000},
            {'type': 'xp', 'amount': 500},
            {'type': 'item', 'name': 'Legendary Crown', 'item_type': 'title'},
        ]
    }
    possible = loot_table.get(rarity, loot_table['common'])
    chosen = random.choice(possible)

    if chosen['type'] == 'coins':
        current_user.add_coins(chosen['amount'], f'Opened {rarity} box')
    elif chosen['type'] == 'xp':
        current_user.add_xp(chosen['amount'])
    elif chosen['type'] == 'item':
        # ShopItem-с хайх эсвэл үүсгэх
        item = ShopItem.query.filter_by(name=chosen['name']).first()
        if not item:
            item = ShopItem(name=chosen['name'], description=f'From {rarity} box', price=0, item_type=chosen.get('item_type', 'other'), is_active=True)
            db.session.add(item)
            db.session.flush()
        inv = UserInventory.query.filter_by(user_id=current_user.id, item_id=item.id).first()
        if inv:
            inv.quantity += 1
        else:
            db.session.add(UserInventory(user_id=current_user.id, item_id=item.id, quantity=1))
    db.session.commit()
    return chosen