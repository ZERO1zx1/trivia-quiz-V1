"""RESTful API v1"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User, DiscordAccount
from app.models.notification import Notification

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# ===================== Хэрэглэгчид =====================
@api_v1_bp.route('/users/<int:user_id>')
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@api_v1_bp.route('/users/me')
@login_required
def get_me():
    return jsonify(current_user.to_dict())

# ===================== Discord =====================
@api_v1_bp.route('/discord/<discord_id>')
def get_by_discord(discord_id):
    discord = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord or not discord.user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(discord.user.to_dict())

# ===================== Мэдэгдлүүд =====================
@api_v1_bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    notifs = current_user.notifications.paginate(page=page, per_page=per_page)
    return jsonify({
        'items': [n.to_dict() for n in notifs.items],
        'total': notifs.total,
        'pages': notifs.pages,
        'page': notifs.page
    })