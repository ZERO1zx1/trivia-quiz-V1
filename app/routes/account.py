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