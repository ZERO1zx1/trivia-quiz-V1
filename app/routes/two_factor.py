"""Two-Factor Authentication Routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request, session
from flask_login import login_required, current_user
from app.utils.two_factor import (
    generate_2fa_secret,
    get_2fa_qr_code,
    verify_2fa_code,
    enable_2fa_for_user,
    disable_2fa_for_user,
    is_2fa_enabled
)

two_factor_bp = Blueprint('two_factor', __name__)


@two_factor_bp.route('/setup')
@login_required
def setup():
    """Show 2FA setup page with QR code."""
    secret = generate_2fa_secret()
    session['pending_2fa_secret'] = secret
    qr_code = get_2fa_qr_code(current_user, secret)
    return render_template('auth/two_factor_setup.html', qr_code=qr_code, secret=secret)


@two_factor_bp.route('/enable', methods=['POST'])
@login_required
def enable():
    """Enable 2FA after verifying the code."""
    secret = session.get('pending_2fa_secret')
    code = request.form.get('code', '').strip()

    if not secret:
        flash('Please start the setup process first.', 'danger')
        return redirect(url_for('two_factor.setup'))

    if not code:
        flash('Please enter the 6-digit code.', 'danger')
        return redirect(url_for('two_factor.setup'))

    if verify_2fa_code(secret, code):
        enable_2fa_for_user(current_user, secret)
        session.pop('pending_2fa_secret', None)
        flash('2FA has been enabled! Your account is now more secure.', 'success')
        return redirect(url_for('account.settings'))
    else:
        flash('Invalid code. Please try again.', 'danger')
        return redirect(url_for('two_factor.setup'))


@two_factor_bp.route('/disable', methods=['POST'])
@login_required
def disable():
    """Disable 2FA."""
    code = request.form.get('code', '').strip()

    if not code:
        flash('Please enter the 6-digit code.', 'danger')
        return redirect(url_for('account.settings'))

    # Get user's 2FA secret
    from app.models.settings import TwoFactorAuth
    twofa = TwoFactorAuth.query.filter_by(user_id=current_user.id, is_enabled=True).first()

    if twofa and verify_2fa_code(twofa.totp_secret, code):
        disable_2fa_for_user(current_user)
        flash('2FA has been disabled.', 'info')
        return redirect(url_for('account.settings'))
    else:
        flash('Invalid code.', 'danger')
        return redirect(url_for('account.settings'))


@two_factor_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify 2FA code during login."""
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        user_id = session.get('2fa_user_id')

        if not user_id or not code:
            flash('Invalid request.', 'danger')
            return redirect(url_for('auth.login'))

        from app.models.user import User
        from app.models.settings import TwoFactorAuth

        user = User.query.get(user_id)
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.login'))

        twofa = TwoFactorAuth.query.filter_by(user_id=user.id, is_enabled=True).first()
        if not twofa:
            flash('2FA is not enabled.', 'danger')
            return redirect(url_for('auth.login'))

        if verify_2fa_code(twofa.totp_secret, code):
            from flask_login import login_user
            login_user(user, remember=True)
            session.pop('2fa_user_id', None)
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid 2FA code.', 'danger')
            return render_template('auth/two_factor_verify.html')

    return render_template('auth/two_factor_verify.html')
