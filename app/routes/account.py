from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash
from app.extensions import db, utcnow
from app.models.user import User
from app.models.profile import ProfileView
from app.services.auth_sessions import access_token
from app.services.supabase import SupabaseError, SupabaseService
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import secrets
import os
from werkzeug.utils import secure_filename

account_bp = Blueprint('account', __name__)


def _normalized_image(upload):
    """Decode and re-encode uploads so active/metadata payloads are removed."""
    raw = upload.stream.read(6 * 1024 * 1024 + 1)
    if not raw or len(raw) > 6 * 1024 * 1024:
        raise ValueError('Image must be 6 MB or smaller.')
    try:
        image = Image.open(BytesIO(raw))
        image.verify()
        image = Image.open(BytesIO(raw))
        image.thumbnail((2048, 2048))
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA' if 'transparency' in image.info else 'RGB')
        output = BytesIO()
        image.save(output, format='WEBP', quality=88, method=6)
        return output.getvalue(), 'image/webp'
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError('Upload a valid PNG, JPEG, GIF, or WebP image.') from exc


def _store_profile_image(upload, bucket):
    data, content_type = _normalized_image(upload)
    object_name = f'{secrets.token_urlsafe(18)}.webp'
    if SupabaseService.enabled():
        if not current_user.auth_user_id:
            raise ValueError('Your account is not linked to Supabase Auth.')
        token = access_token()
        if not token:
            raise ValueError('Authentication session expired. Sign in again.')
        object_path = f'{current_user.auth_user_id}/{object_name}'
        return SupabaseService().upload_image(
            bucket, object_path, data, content_type, token)

    # Local-only fallback for development. Production never stores durable
    # uploads on the container filesystem.
    target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], bucket)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, object_name)
    with open(target_path, 'wb') as output:
        output.write(data)
    return f'/static/uploads/{bucket}/{object_name}'

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
    if not last_view or (utcnow() - last_view.viewed_at) > timedelta(hours=24):
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

    try:
        if 'avatar' in request.files and request.files['avatar'].filename:
            current_user.avatar_url = _store_profile_image(
                request.files['avatar'],
                current_app.config['SUPABASE_STORAGE_AVATAR_BUCKET'])

        if (current_user.is_premium and 'banner' in request.files
                and request.files['banner'].filename):
            current_user.banner_url = _store_profile_image(
                request.files['banner'],
                current_app.config['SUPABASE_STORAGE_BANNER_BUCKET'])
    except (ValueError, SupabaseError) as exc:
        current_app.logger.info('Profile image rejected for user id=%s: %s',
                                current_user.id, exc)
        flash(str(exc), 'danger')
        return redirect(url_for('account.profile'))

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

    if SupabaseService.enabled():
        try:
            SupabaseService().sign_in(current_user.email, current_password)
        except SupabaseError:
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('account.settings'))
    elif not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('account.settings'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('account.settings'))

    # FIX-023: canonical password policy (shared with auth flow)
    from app.shared.password_policy import validate_password
    policy_errors = validate_password(new_password)
    if policy_errors:
        flash(policy_errors[0], 'danger')
        return redirect(url_for('account.settings'))

    if SupabaseService.enabled():
        token = access_token()
        if not token:
            flash('Authentication session expired. Please sign in again.',
                  'warning')
            return redirect(url_for('auth.login'))
        try:
            SupabaseService().update_password(token, new_password)
        except SupabaseError:
            current_app.logger.exception('Supabase password change failed')
            flash('Password could not be changed.', 'danger')
            return redirect(url_for('account.settings'))
        current_user.password_hash = None
    else:
        current_user.set_password(new_password)
    db.session.commit()
    
    # Send email notification for password change
    from app.utils.email import send_email
    send_email(
        subject='[TriviaVerse] Password Changed',
        recipients=[current_user.email],
        body=f"Hello {current_user.username},\n\nYour TriviaVerse account password was recently changed. If you did not make this change, please contact support immediately."
    )
    
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
    
    # Support notification preferences from JS toggles
    if 'email_notif_security' in data:
        current_user.email_notif_security = data['email_notif_security']
    if 'email_notif_social' in data:
        current_user.email_notif_social = data['email_notif_social']
    if 'email_notif_promo' in data:
        current_user.email_notif_promo = data['email_notif_promo']
        
    db.session.commit()
    return jsonify({'success': True})

@account_bp.route('/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    """Мэдэгдлийн тохиргоог хадгалах (Form submission)"""
    current_user.email_notif_security = True # Security always True
    current_user.email_notif_social = 'email_notif_social' in request.form
    current_user.email_notif_promo = 'email_notif_promo' in request.form
    
    db.session.commit()
    flash('Notification preferences updated!', 'success')
    return redirect(url_for('account.settings'))

@account_bp.route('/settings/theme', methods=['POST'])
@login_required
def update_theme():
    data = request.get_json()
    theme = data.get('theme')
    if theme in ('dark', 'light'):
        from flask import session
        session['theme'] = theme
        current_user.theme = theme
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400
