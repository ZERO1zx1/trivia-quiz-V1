from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.notification import Notification

api_bp = Blueprint('api', __name__)

# ==========================================
#  Мэдэгдлүүд
# ==========================================
@api_bp.route('/notifications')
@login_required
def get_notifications():
    """Хэрэглэгчийн сүүлийн 20 мэдэгдлийг авах"""
    notifs = current_user.notifications.limit(20).all()
    return jsonify([n.to_dict() for n in notifs])

@api_bp.route('/notifications/unread-count')
@login_required
def unread_count():
    """Уншаагүй мэдэгдлийн тоо"""
    count = current_user.notifications.filter_by(is_read=False).count()
    return jsonify({'count': count})

@api_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    """Тухайн мэдэгдлийг уншсан болгох"""
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    """Бүх мэдэгдлийг уншсан болгох"""
    current_user.notifications.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})