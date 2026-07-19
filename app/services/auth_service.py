"""Authentication Service"""
import re
from app.models.user import User
from app.extensions import db

class AuthService:
    @staticmethod
    def validate_username(username):
        if not username or len(username) < 3 or len(username) > 30:
            return False, 'Username must be 3-30 characters'
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, 'Username can only contain letters, numbers, and underscores'
        return True, None

    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, 'Invalid email format'
        return True, None

    @staticmethod
    def validate_password(password):
        if len(password) < 6:
            return False, 'Password must be at least 6 characters'
        return True, None
