from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User, DiscordAccount, Friend
from app.models.notification import Notification
from app.utils.notify import send_notification

api_bp = Blueprint('api', __name__)

# ==========================================
#  Хэрэглэгчийн мэдээлэл (Discord ID-аар)
# ==========================================
@api_bp.route('/user/<discord_id>')
def get_user(discord_id):
    # DiscordAccount-с хэрэглэгчийг хайх
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404

    user = discord_account.user
    return jsonify({
        'id': user.id,
        'username': user.username,
        'level': user.level,
        'xp': user.xp,
        'coins': user.coins,
        'wins': user.wins,
        'accuracy': user.accuracy,
        'games_played': user.games_played,
        'display_name': user.display_name,
        'avatar_url': user.avatar_url
    })

# ==========================================
#  Нэвтэрсэн хэрэглэгчийн статистик
# ==========================================
@api_bp.route('/user/stats')
@login_required
def api_user_stats():
    stats = {
        'username': current_user.username,
        'display_name': current_user.display_name,
        'level': current_user.level,
        'xp': current_user.xp,
        'coins': current_user.coins,
        'wins': current_user.wins,
        'losses': current_user.losses,
        'games_played': current_user.games_played,
        'accuracy': round(current_user.accuracy, 1),
        'avatar': current_user.avatar_url,
        'is_online': current_user.is_online
    }
    return jsonify(stats)

# ==========================================
#  Мэдэгдлүүд
# ==========================================
@api_bp.route('/notifications')
@login_required
def get_notifications():
    notifs = current_user.notifications.limit(20).all()
    return jsonify([n.to_dict() for n in notifs])

@api_bp.route('/notifications/unread-count')
@login_required
def unread_count():
    count = current_user.notifications.filter_by(is_read=False).count()
    return jsonify({'count': count})

@api_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    current_user.notifications.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

# ==========================================
#  Найзын систем (API)
# ==========================================
@api_bp.route('/friends/search', methods=['POST'])
def api_search_friends():
    data = request.json
    discord_id = data.get('discord_id')
    username = data.get('username')

    # Discord ID-аар хэрэглэгчийг олох
    current_user_discord = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not current_user_discord or not current_user_discord.user:
        return jsonify({'error': 'Your account not found'}), 404

    sender = current_user_discord.user
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({'error': 'User not found'}), 404

    if target.id == sender.id:
        return jsonify({'error': 'Cannot add yourself'}), 400

    existing = Friend.query.filter(
        ((Friend.user_id == sender.id) & (Friend.friend_id == target.id)) |
        ((Friend.user_id == target.id) & (Friend.friend_id == sender.id))
    ).first()
    if existing:
        return jsonify({'error': 'Already friends or request pending'}), 409

    friendship = Friend(user_id=sender.id, friend_id=target.id, status='pending')
    db.session.add(friendship)
    db.session.commit()

    from app.utils.notify import send_notification
    send_notification(
        user_id=target.id,
        title='New Friend Request',
        message=f'{sender.username} wants to be your friend!',
        notif_type='info'
    )

    return jsonify({'message': 'Friend request sent'})

@api_bp.route('/users/coins/add', methods=['POST'])
def add_coins():
    data = request.json
    discord_id = data.get('discord_id')
    amount = data.get('amount', 0)
    reason = data.get('reason', 'Discord activity')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    user.add_coins(amount, reason)
    db.session.commit()
    
    return jsonify({'new_coins': user.coins})

@api_bp.route('/users/xp/add', methods=['POST'])
def add_xp():
    data = request.json
    discord_id = data.get('discord_id')
    amount = data.get('amount', 0)
    reason = data.get('reason', 'Discord activity')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    level_up, old_lvl, new_lvl = user.add_xp(amount)
    db.session.commit()
    
    return jsonify({
        'xp': user.xp,
        'level': user.level,
        'level_up': level_up,
        'old_level': old_lvl,
        'new_level': new_lvl
    })