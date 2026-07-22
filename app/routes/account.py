import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db

account_bp = Blueprint('account', __name__)

@account_bp.route('/profile')
@login_required
def profile():
    return render_template('account/profile.html')

@account_bp.route('/settings')
@login_required
def settings():
    return render_template('account/settings.html')

@account_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    # Avatar зураг хадгалах
    if 'avatar' in request.files and request.files['avatar'].filename:
        file = request.files['avatar']
        filename = secure_filename(file.filename)
        avatar_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        file.save(os.path.join(avatar_dir, filename))
        current_user.avatar_url = '/static/uploads/avatars/' + filename

    # Текст талбарууд
    current_user.display_name = request.form.get('display_name', current_user.display_name).strip()
    current_user.bio = request.form.get('bio', current_user.bio).strip()
    current_user.country = request.form.get('country', current_user.country)

    try:
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating profile.', 'error')
        current_app.logger.error(f'Profile update failed: {e}')

    current_user.nickname_effect = request.form.get('nickname_effect', current_user.nickname_effect)
    current_user.profile_theme_music = request.form.get('profile_theme_music', current_user.profile_theme_music)
    db.session.commit()
    flash('Profile updated!', 'success')
    return redirect(url_for('account.profile'))

@account_bp.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    # TODO: бодит нууц үг солих логик (одоогоор заглуушка)
    flash('Password change not yet implemented.', 'info')
    return redirect(url_for('account.settings'))

@account_bp.route('/settings/preferences', methods=['POST'])
@login_required
def update_preferences():
    # TODO: бодит тохиргоо хадгалах логик (одоогоор заглуушка)
    flash('Preferences saved (not yet implemented).', 'info')
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

@account_bp.route('/update-showcase-badges', methods=['POST'])
@login_required
def update_showcase_badges():
    data = request.json
    current_user.showcase_badge_ids = ','.join(data.get('badge_ids', []))
    db.session.commit()
    return jsonify({'success': True})

@account_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile_json():
    data = request.json
    if 'nickname_effect' in data:
        if current_user.is_premium:
            current_user.nickname_effect = data['nickname_effect']
        else:
            return jsonify({'error': 'Premium required'}), 403
    if 'profile_theme_music' in data:
        if current_user.is_premium:
            current_user.profile_theme_music = data['profile_theme_music']
        else:
            return jsonify({'error': 'Premium required'}), 403
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