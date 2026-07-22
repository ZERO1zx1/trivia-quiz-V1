"""Social Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User, Friend
from app.utils.notify import send_notification

social_bp = Blueprint('social', __name__)

@social_bp.route('/friends')
@login_required
def friends():
    pending_requests = Friend.query.filter_by(friend_id=current_user.id, status='pending').all()
    friends = current_user.get_friends()
    return render_template('social/friends.html', friends=friends, friend_requests=pending_requests)

@social_bp.route('/friends/search', methods=['POST'])
@login_required
def search_friends():
    username = request.form.get('username', '').strip()
    if not username:
        flash('Username is required.', 'warning')
        return redirect(url_for('social.friends'))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('social.friends'))

    if user.id == current_user.id:
        flash('You cannot add yourself.', 'warning')
        return redirect(url_for('social.friends'))

    # Аль хэдийн найз эсэхийг шалгах
    existing = Friend.query.filter(
        ((Friend.user_id == current_user.id) & (Friend.friend_id == user.id)) |
        ((Friend.user_id == user.id) & (Friend.friend_id == current_user.id))
    ).first()

    if existing:
        if existing.status == 'accepted':
            flash('Already friends!', 'info')
        else:
            flash('Friend request already sent.', 'info')
        return redirect(url_for('social.friends'))

    # Хүсэлт илгээх
    friendship = Friend(user_id=current_user.id, friend_id=user.id, status='pending')
    db.session.add(friendship)
    db.session.commit()

    # Мэдэгдэл илгээх
    send_notification(
        user_id=user.id,
        title='New Friend Request',
        message=f'{current_user.username} wants to be your friend!',
        notif_type='info'
    )

    flash(f'Friend request sent to {user.username}!', 'success')
    return redirect(url_for('social.friends'))

@social_bp.route('/friends/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    req = Friend.query.get_or_404(request_id)
    if req.friend_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('social.friends'))

    req.status = 'accepted'
    db.session.commit()

    send_notification(
        user_id=req.user_id,
        title='Friend Request Accepted',
        message=f'{current_user.username} accepted your friend request!',
        notif_type='success'
    )

    flash('Friend request accepted!', 'success')
    return redirect(url_for('social.friends'))

@social_bp.route('/friends/decline/<int:request_id>', methods=['POST'])
@login_required
def decline_request(request_id):
    req = Friend.query.get_or_404(request_id)
    if req.friend_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('social.friends'))

    db.session.delete(req)
    db.session.commit()

    flash('Friend request declined.', 'info')
    return redirect(url_for('social.friends'))

@social_bp.route('/friends/remove/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    friendship = Friend.query.filter(
        ((Friend.user_id == current_user.id) & (Friend.friend_id == friend_id)) |
        ((Friend.user_id == friend_id) & (Friend.friend_id == current_user.id))
    ).first()

    if friendship:
        db.session.delete(friendship)
        db.session.commit()
        flash('Friend removed.', 'info')
    else:
        flash('Friend not found.', 'danger')

    return redirect(url_for('social.friends'))