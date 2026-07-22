from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.box import UserBox, Box
import random

box_api_bp = Blueprint('box_api', __name__)

@box_api_bp.route('/open-box/<int:box_id>', methods=['POST'])
@login_required
def open_box(box_id):
    """Авдар нээх (atomic)"""
    # Транзакц эхлүүлэх
    user_box = UserBox.query.with_for_update().filter_by(
        id=box_id, user_id=current_user.id, is_opened=False
    ).first()

    if not user_box:
        return jsonify({'success': False, 'message': 'Box not found or already opened.'})

    # Авдрыг нээсэн төлөвт шилжүүлэх
    user_box.is_opened = True
    user_box.opened_at = datetime.utcnow()

    # Loot үүсгэх (жишээ)
    loot = generate_loot(user_box.box.rarity)

    db.session.commit()
    return jsonify({'success': True, 'loot': loot})