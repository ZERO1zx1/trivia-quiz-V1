"""Two-Factor Authentication (2FA) Utility

FIX-003: all helpers use the canonical model fields (`secret_key`,
`updated_at`). The old `totp_secret` attribute access still works because
the model exposes it as a synced alias.
"""
import datetime

import pyotp
import qrcode
import io
import base64
from flask import current_app
from app.extensions import db, utcnow


def generate_2fa_secret():
    """Generate a new TOTP secret key."""
    return pyotp.random_base32()


def get_2fa_qr_code(user, secret):
    """Generate QR code for Google Authenticator as base64 image."""
    issuer = current_app.config.get('TOTP_ISSUER_NAME', 'TriviaVerse')
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name=issuer
    )

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(otp_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color='white', back_color='#1a1a2e')

    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format='PNG')
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return f'data:image/png;base64,{img_str}'


def verify_2fa_code(secret, code):
    """Verify a 2FA TOTP code."""
    if not secret or not code:
        return False
    try:
        int(code)
    except ValueError:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def enable_2fa_for_user(user, secret):
    """Enable 2FA for a user."""
    from app.models.settings import TwoFactorAuth

    existing = TwoFactorAuth.query.filter_by(user_id=user.id).first()
    if existing:
        existing.secret_key = secret
        existing.is_enabled = True
        existing.updated_at = utcnow()
        existing.enabled_at = existing.enabled_at or utcnow()
    else:
        twofa = TwoFactorAuth(
            user_id=user.id,
            secret_key=secret,
            is_enabled=True,
            enabled_at=utcnow(),
        )
        db.session.add(twofa)

    db.session.commit()
    return True


def disable_2fa_for_user(user):
    """Disable 2FA for a user."""
    from app.models.settings import TwoFactorAuth

    twofa = TwoFactorAuth.query.filter_by(user_id=user.id).first()
    if twofa:
        twofa.is_enabled = False
        twofa.secret_key = None
        db.session.commit()
    return True


def is_2fa_enabled(user_id):
    """Check if 2FA is enabled for a user."""
    from app.models.settings import TwoFactorAuth

    twofa = TwoFactorAuth.query.filter_by(
        user_id=user_id,
        is_enabled=True
    ).first()
    return twofa is not None and bool(twofa.secret_key)
