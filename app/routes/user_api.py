"""User interaction API (views, respect, challenge, gift)"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User
from app.models.profile import ProfileView, UserRespect, GameChallenge, GiftTransaction
from app.utils.notify import send_notification

user_api_bp = Blueprint('user_api', __name__)

# ==========================================
#  Профайл үзэлт (24 цагт 1 удаа)
# ==========================================
@user_api_bp.route('/profile/view/<int:user_id>', methods=['POST'])
@login_required
def record_profile_view(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot view yourself'})

    # 24 цагийн хязгаар
    last_view = ProfileView.query.filter_by(
        viewer_id=current_user.id, profile_id=user_id
    ).order_by(ProfileView.viewed_at.desc()).first()

    if last_view and (datetime.utcnow() - last_view.viewed_at) < timedelta(hours=24):
        return jsonify({'success': False, 'message': 'Already viewed within 24h'})

    view = ProfileView(viewer_id=current_user.id, profile_id=user_id)
    db.session.add(view)
    db.session.commit()
    return jsonify({'success': True, 'total_views': ProfileView.query.filter_by(profile_id=user_id).count()})

# ==========================================
#  Respect өгөх
# ==========================================
@user_api_bp.route('/respect/<int:user_id>', methods=['POST'])
@login_required
def give_respect(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot respect yourself'})

    # Өдөрт нэг удаа
    today = datetime.utcnow().date()
    already = UserRespect.query.filter(
        UserRespect.giver_id == current_user.id,
        UserRespect.receiver_id == user_id,
        db.func.date(UserRespect.created_at) == today
    ).first()
    if already:
        return jsonify({'success': False, 'message': 'Already respected today'})

    respect = UserRespect(giver_id=current_user.id, receiver_id=user_id)
    db.session.add(respect)
    user = User.query.get(user_id)
    user.respect_count += 1
    db.session.commit()

    send_notification(user_id, '❤️ Respect Received', f'{current_user.username} gave you respect!', 'info')
    return jsonify({'success': True, 'respect_count': user.respect_count})

# ==========================================
#  1v1 Challenge урилга
# ==========================================
@user_api_bp.route('/challenge/<int:user_id>', methods=['POST'])
@login_required
def challenge_user(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot challenge yourself'})

    target = User.query.get_or_404(user_id)
    if target.do_not_disturb:
        return jsonify({'success': False, 'message': 'User is in Do Not Disturb mode'})

    # Cooldown шалгах (1 минутын дотор дахин илгээхгүй)
    last_challenge = GameChallenge.query.filter_by(
        sender_id=current_user.id, receiver_id=user_id
    ).order_by(GameChallenge.created_at.desc()).first()

    if last_challenge and (datetime.utcnow() - last_challenge.created_at) < timedelta(minutes=1):
        return jsonify({'success': False, 'message': 'Please wait before challenging again'})

    challenge = GameChallenge(sender_id=current_user.id, receiver_id=user_id, status='pending')
    db.session.add(challenge)
    db.session.commit()

    send_notification(
        user_id,
        '⚔️ Challenge!',
        f'{current_user.username} challenged you to a 1v1!',
        'game_invite'
    )
    return jsonify({'success': True, 'challenge_id': challenge.id})

@user_api_bp.route('/challenge/<int:challenge_id>/accept', methods=['POST'])
@login_required
def accept_challenge(challenge_id):
    challenge = GameChallenge.query.get_or_404(challenge_id)
    if challenge.receiver_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    challenge.status = 'accepted'
    db.session.commit()
    # Өрөө үүсгэх эсвэл одоогийн өрөө рүү чиглүүлэх логик
    return jsonify({'success': True, 'redirect': f'/rooms/lobby'})

@user_api_bp.route('/challenge/<int:challenge_id>/decline', methods=['POST'])
@login_required
def decline_challenge(challenge_id):
    challenge = GameChallenge.query.get_or_404(challenge_id)
    if challenge.receiver_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    challenge.status = 'declined'
    db.session.commit()
    return jsonify({'success': True})

# ==========================================
#  Бэлэг илгээх
# ==========================================
@user_api_bp.route('/gift/<int:user_id>', methods=['POST'])
@login_required
def send_gift(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot gift yourself'})

    data = request.json
    gift_type = data.get('gift_type', 'coffee')
    coin_map = {'coffee': 10, 'crown': 500, 'xp_boost': 200}
    coins_needed = coin_map.get(gift_type, 10)

    if current_user.coins < coins_needed:
        return jsonify({'success': False, 'message': 'Not enough coins'})

    current_user.coins -= coins_needed
    receiver = User.query.get_or_404(user_id)

    if gift_type == 'xp_boost':
        receiver.xp += 50
    elif gift_type == 'crown':
        # Crown логик (профайл дээр тэмдэг харуулах)
        pass

    gift = GiftTransaction(
        sender_id=current_user.id,
        receiver_id=user_id,
        gift_type=gift_type,
        coin_amount=coins_needed
    )
    db.session.add(gift)
    db.session.commit()

    send_notification(user_id, '🎁 Gift Received!', f'{current_user.username} sent you a {gift_type}!', 'success')
    return jsonify({'success': True, 'coins_left': current_user.coins})

@user_api_bp.route('/hover-info/<int:user_id>')
@login_required
def hover_info(user_id):
    user = User.query.get_or_404(user_id)
    total_views = ProfileView.query.filter_by(profile_id=user_id).count()
    return jsonify({
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name,
        'avatar_url': user.avatar_url,
        'role': user.role,
        'profile_views': total_views,
        'respect_count': user.respect_count,
        'accuracy': user.accuracy or 0
    })