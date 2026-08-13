"""Two-Factor Authentication Routes

Security fixes applied:
- FIX-003: helpers write to the canonical model fields.
- FIX-004: login-stage verification validates the pending-login token set by
  the auth flow, and failed attempts are rate limited (5 per 10 minutes).
- Setup requires confirmation with a valid TOTP code before enabling.
"""
from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required

import jwt
from uuid import UUID

from app.utils.two_factor import (
    generate_2fa_secret,
    get_2fa_qr_code,
    verify_2fa_code,
    enable_2fa_for_user,
    disable_2fa_for_user,
    is_2fa_enabled
)
from app.extensions import db
from app.services.auth_sessions import (
    access_token, replace_auth_tokens)
from app.services.supabase import SupabaseError, SupabaseService

two_factor_bp = Blueprint('two_factor', __name__)

TF_RATE_LIMIT = 5           # max failed attempts per 10 minutes
TF_RATE_WINDOW = 600        # seconds


@two_factor_bp.route('/setup')
@login_required
def setup():
    """Show 2FA setup page with QR code."""
    if SupabaseService.enabled():
        token = access_token()
        if not token:
            flash('Authentication session expired. Please sign in again.',
                  'warning')
            return redirect(url_for('auth.login'))
        try:
            payload = SupabaseService().enroll_totp(
                token, f'TriviaVerse:{current_user.username}')
            factor = payload.get('factor') or payload
            totp = factor.get('totp') or {}
            factor_id = factor.get('id')
            if not factor_id or not totp.get('qr_code'):
                raise SupabaseError('MFA enrollment response was incomplete')
            session['pending_supabase_factor_id'] = factor_id
            return render_template(
                'auth/two_factor_setup.html',
                qr_code=totp['qr_code'], secret=totp.get('secret', ''))
        except SupabaseError:
            current_app.logger.exception('Supabase MFA enrollment failed')
            flash('2FA setup is temporarily unavailable.', 'danger')
            return redirect(url_for('account.settings'))

    secret = generate_2fa_secret()
    session['pending_2fa_secret'] = secret
    qr_code = get_2fa_qr_code(current_user, secret)
    return render_template('auth/two_factor_setup.html', qr_code=qr_code, secret=secret)


@two_factor_bp.route('/enable', methods=['POST'])
@login_required
def enable():
    """Enable 2FA after verifying the code."""
    if SupabaseService.enabled():
        factor_id = session.get('pending_supabase_factor_id')
        code = request.form.get('code', '').strip()
        token = access_token()
        if not factor_id or not code or not token:
            flash('Please restart the 2FA setup process.', 'danger')
            return redirect(url_for('two_factor.setup'))
        try:
            service = SupabaseService()
            challenge_id = service.challenge_totp(token, factor_id)
            tokens = service.verify_totp(
                token, factor_id, challenge_id, code)
            replace_auth_tokens(tokens)
        except SupabaseError:
            flash('Invalid code. Please try again.', 'danger')
            return redirect(url_for('two_factor.setup'))

        from app.models.settings import TwoFactorAuth
        twofa = TwoFactorAuth.query.filter_by(
            user_id=current_user.id).first()
        if not twofa:
            twofa = TwoFactorAuth(user_id=current_user.id)
            db.session.add(twofa)
        twofa.is_enabled = True
        twofa.auth_factor_id = UUID(str(factor_id))
        twofa.secret_key = None
        twofa.method = 'supabase_totp'
        session.pop('pending_supabase_factor_id', None)
        db.session.commit()
        flash('2FA has been enabled with Supabase Auth.', 'success')
        return redirect(url_for('account.settings'))

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

    flash('Invalid code. Please try again.', 'danger')
    return redirect(url_for('two_factor.setup'))


@two_factor_bp.route('/disable', methods=['POST'])
@login_required
def disable():
    """Disable 2FA. Requires a valid current TOTP code."""
    code = request.form.get('code', '').strip()

    if not code:
        flash('Please enter the 6-digit code.', 'danger')
        return redirect(url_for('account.settings'))

    # Get user's 2FA secret
    from app.models.settings import TwoFactorAuth
    twofa = TwoFactorAuth.query.filter_by(user_id=current_user.id).first()

    if (SupabaseService.enabled() and twofa and twofa.is_enabled
            and twofa.auth_factor_id):
        token = access_token()
        if not token:
            flash('Authentication session expired. Please sign in again.',
                  'warning')
            return redirect(url_for('auth.login'))
        try:
            service = SupabaseService()
            challenge_id = service.challenge_totp(
                token, str(twofa.auth_factor_id))
            tokens = service.verify_totp(
                token, str(twofa.auth_factor_id), challenge_id, code)
            replace_auth_tokens(tokens)
            elevated_token = access_token(refresh_if_needed=False)
            service.unenroll_factor(
                elevated_token, str(twofa.auth_factor_id))
        except SupabaseError:
            flash('Invalid code.', 'danger')
            return redirect(url_for('account.settings'))
        twofa.is_enabled = False
        twofa.auth_factor_id = None
        twofa.method = 'supabase_totp'
        db.session.commit()
        flash('2FA has been disabled.', 'info')
        return redirect(url_for('account.settings'))

    if not twofa or not twofa.is_enabled or not twofa.secret_key:
        flash('2FA is not enabled on this account.', 'warning')
        return redirect(url_for('account.settings'))

    if verify_2fa_code(twofa.secret_key, code):
        disable_2fa_for_user(current_user)
        flash('2FA has been disabled.', 'info')
        return redirect(url_for('account.settings'))

    flash('Invalid code.', 'danger')
    return redirect(url_for('account.settings'))


def _verify_attempts_key():
    return '2fa_verify_attempts'


def _record_attempt(failed):
    """Simple in-memory-per-session rate tracking for 2FA verify attempts."""
    import time
    entry = session.get(_verify_attempts_key())
    now = time.time()
    if not entry or now - entry.get('since', 0) > TF_RATE_WINDOW:
        entry = {'since': now, 'fails': 0}
    if failed:
        entry['fails'] += 1
    session[_verify_attempts_key()] = entry
    return entry['fails']


@two_factor_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify 2FA code during login. Requires the pending-login token set by
    the auth flow (FIX-004)."""
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        user_id = session.get('2fa_user_id')

        if not user_id or not code:
            session.pop('2fa_user_id', None)
            session.pop('2fa_pending_token', None)
            flash('Invalid request.', 'danger')
            return redirect(url_for('auth.login'))

        # FIX-004: rate limit failed 2FA attempts
        fails = _record_attempt(failed=False)
        if fails > TF_RATE_LIMIT:
            session.pop('2fa_user_id', None)
            session.pop('2fa_pending_token', None)
            flash('Too many failed 2FA attempts. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))

        from app.models.user import User
        from app.models.settings import TwoFactorAuth

        user = db.session.get(User, user_id)
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.login'))

        twofa = TwoFactorAuth.query.filter_by(user_id=user.id, is_enabled=True).first()
        if not twofa:
            flash('2FA is not enabled.', 'danger')
            return redirect(url_for('auth.login'))

        verified = False
        if (SupabaseService.enabled() and twofa.auth_factor_id
                and twofa.method == 'supabase_totp'):
            token = access_token()
            try:
                if not token:
                    raise SupabaseError('Authentication session expired')
                service = SupabaseService()
                challenge_id = service.challenge_totp(
                    token, str(twofa.auth_factor_id))
                tokens = service.verify_totp(
                    token, str(twofa.auth_factor_id), challenge_id, code)
                replace_auth_tokens(tokens)
                verified = True
            except SupabaseError:
                verified = False
        else:
            verified = verify_2fa_code(twofa.secret_key, code)

        if verified:
            from app.routes.auth import _complete_login
            response = _complete_login(user)
            if response is not None:
                return response
            session.pop('2fa_user_id', None)
            session.pop(_verify_attempts_key(), None)
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard.index'))

        _record_attempt(failed=True)
        flash('Invalid 2FA code.', 'danger')
        return render_template('auth/two_factor_verify.html')

    return render_template('auth/two_factor_verify.html')
