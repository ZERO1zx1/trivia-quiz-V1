"""Two-Factor Authentication (2FA) Utility"""
import pyotp
import qrcode
import io
import base64
from flask import current_app, url_for
from app.extensions import db


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
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def enable_2fa_for_user(user, secret):
    """Enable 2FA for a user."""
    from app.models.settings import TwoFactorAuth
    
    existing = TwoFactorAuth.query.filter_by(user_id=user.id).first()
    if existing:
        existing.totp_secret = secret
        existing.is_enabled = True
        existing.updated_at = __import__('datetime').datetime.utcnow()
    else:
        twofa = TwoFactorAuth(
            user_id=user.id,
            totp_secret=secret,
            is_enabled=True
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
        db.session.commit()
    return True


def is_2fa_enabled(user_id):
    """Check if 2FA is enabled for a user."""
    from app.models.settings import TwoFactorAuth
    
    twofa = TwoFactorAuth.query.filter_by(
        user_id=user_id,
        is_enabled=True
    ).first()
    return twofa is not None
