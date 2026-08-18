from functools import wraps
import hmac

from flask import abort, current_app, flash, jsonify, redirect, request, url_for
from flask_login import current_user
from datetime import datetime
from app.extensions import db, utcnow

def discord_api_required(f):
    """Require the shared service token used by the Discord bot.

    Legacy bot endpoints mutate user balances and relationships. They must not
    trust a caller-supplied Discord ID as authentication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        expected = current_app.config.get('DISCORD_API_TOKEN', '')
        supplied = request.headers.get('X-Discord-API-Key', '')
        if not expected:
            current_app.logger.error('DISCORD_API_TOKEN is not configured')
            return jsonify({'error': 'Discord API is not configured'}), 503
        if not supplied or not hmac.compare_digest(supplied, expected):
            return jsonify({'error': 'Invalid Discord service credentials'}), 401
        return f(*args, **kwargs)
    return decorated_function


def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        # Premium эсэхийг шалгах
        if not current_user.is_premium:
            flash('This feature requires a premium account.', 'warning')
            return redirect(url_for('dashboard.index'))
        # Хугацаа дууссан эсэхийг шалгах
        if current_user.premium_expiry and current_user.premium_expiry < utcnow():
            current_user.is_premium = False
            db.session.commit()
            flash('Your premium has expired.', 'warning')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function