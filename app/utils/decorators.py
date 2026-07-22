from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from datetime import datetime
from app.extensions import db

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
        if current_user.premium_expiry and current_user.premium_expiry < datetime.utcnow():
            current_user.is_premium = False
            db.session.commit()
            flash('Your premium has expired.', 'warning')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function