"""Admin utilities and decorators"""
from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """Backward-compatible admin check"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Restrict access to specific roles (owner always has access)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            # owner-д бүх эрх нээлттэй
            if current_user.role == 'owner':
                return f(*args, **kwargs)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator