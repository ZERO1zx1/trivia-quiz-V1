"""Flask Extensions Initialization"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_babel import Babel
from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """Store timestamps as TIMESTAMPTZ while bridging legacy naive UTC code."""
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


def utcnow():
    """Legacy-compatible UTC clock without deprecated ``utcnow()`` calls.

    The ORM type attaches UTC before binding and PostgreSQL stores
    TIMESTAMPTZ. Returning naive UTC here keeps older Python comparisons safe
    until every in-memory call site has been converted to aware datetimes.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Database & ORM
db = SQLAlchemy()
db.DateTime = UTCDateTime
migrate = Migrate()

# Authentication
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Real-time
socketio = SocketIO()

# Security
csrf = CSRFProtect()

# Email
mail = Mail()

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

# CORS
cors = CORS()

# Internationalization
babel = Babel()
