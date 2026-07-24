from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash
from app.extensions import db
from app.models.user import User
from app.models.profile import ProfileView
import os
from werkzeug.utils import secure_filename

account_bp = Blueprint('account', __name__)

@account_bp.route('/profile')
@login_required
def profile():
    """Өөрийн профайл"""
    return render_template('account/profile.html', user=current_user, is_owner=True)

@account_bp.route('/profile/<int:user_id>')
@login_required
def user_profile(user_id):
    """Бусдын профайл"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return redirect(url_for('account.profile'))
    # Профайл үзэлт бүртгэх
    from datetime import datetime, timedelta
    last_view = ProfileView.query.filter_by(
        viewer_id=current_user.id, profile_id=user_id
    ).order_by(ProfileView.viewed_at.desc()).first()
    if not last_view or (datetime.utcnow() - last_view.viewed_at) > timedelta(hours=24):
        view = ProfileView(viewer_id=current_user.id, profile_id=user_id)
        db.session.add(view)
        db.session.commit()
    return render_template('account/profile.html', user=user, is_owner=False)

@account_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Профайл мэдээлэл шинэчлэх"""
    current_user.display_name = request.form.get('display_name', current_user.display_name)
    current_user.bio = request.form.get('bio', current_user.bio)
    current_user.country = request.form.get('country', current_user.country)

    if 'avatar' in request.files and request.files['avatar'].filename:
        file = request.files['avatar']
        filename = secure_filename(file.filename)
        avatar_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        file.save(os.path.join(avatar_dir, filename))
        current_user.avatar_url = '/static/uploads/avatars/' + filename

    if current_user.is_premium and 'banner' in request.files and request.files['banner'].filename:
        file = request.files['banner']
        filename = secure_filename(file.filename)
        banner_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'banners')
        os.makedirs(banner_dir, exist_ok=True)
        file.save(os.path.join(banner_dir, filename))
        current_user.banner_url = '/static/uploads/banners/' + filename

    db.session.commit()
    flash('Profile updated!', 'success')
    return redirect(url_for('account.profile'))

@account_bp.route('/settings')
@login_required
def settings():
    """Тохиргооны хуудас"""
    return render_template('account/settings.html')

# ================= ШИНЭ: Нууц үг солих =================
@account_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Хэрэглэгчийн нууц үгийг солих"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_password or not new_password or not confirm_password:
        flash('All fields are required.', 'danger')
        return redirect(url_for('account.settings'))

    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('account.settings'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('account.settings'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'danger')
        return redirect(url_for('account.settings'))

    current_user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('account.settings'))

@account_bp.route('/update-discord-settings', methods=['POST'])
@login_required
def update_discord_settings():
    data = request.json
    if 'rich_presence' in data:
        current_user.discord_rich_presence = data['rich_presence']
    if 'dm_notifications' in data:
        current_user.discord_dm_notifications = data['dm_notifications']
    db.session.commit()
    return jsonify({'success': True})

@account_bp.route('/update-game-settings', methods=['POST'])
@login_required
def update_game_settings():
    data = request.json
    if 'preferred_difficulty' in data:
        current_user.preferred_difficulty = data['preferred_difficulty']
    if 'performance_mode' in data:
        current_user.performance_mode = data['performance_mode']
    db.session.commit()
    return jsonify({'success': True})

@account_bp.route('/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    """Мэдэгдлийн тохиргоог хадгалах"""
    # Одоогоор заглуушка (хэрэгжүүлээгүй)
    flash('Preferences saved.', 'success')
    return redirect(url_for('account.settings'))