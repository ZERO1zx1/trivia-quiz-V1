"""TriviaVerse Configuration"""
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'triviaverse-dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///triviaverse.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'triviaverse-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Discord
    DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID')
    DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET')
    DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI') or 'http://localhost:5000/auth/discord/callback'
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

    # SocketIO
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = '*'

    # Game settings
    QUESTION_TIME_LIMIT = 20
    MAX_PLAYERS_PER_ROOM = 8
    MIN_PLAYERS_TO_START = 2
    DAILY_REWARD_COINS = 100
    WIN_REWARD_COINS = 50
    PERFECT_GAME_BONUS = 200

    # Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # AI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your-actual-api-key'

    # Owner
    OWNER_USERNAME = os.environ.get('OWNER_USERNAME') or None
    OWNER_DISCORD_ID = os.environ.get('OWNER_DISCORD_ID') or None
    OWNER_EMAIL = os.environ.get('OWNER_EMAIL') or None
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'

    # API
    API_BASE_URL = os.environ.get('API_BASE_URL') or 'http://localhost:5000/api'
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS') or 'http://localhost:5000'

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI') or 'memory://'

    # Error webhook
    DISCORD_ERROR_WEBHOOK = os.environ.get('DISCORD_ERROR_WEBHOOK') or ''

    # Email (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or '587')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') != 'False'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your-email@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your-app-password'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'TriviaVerse <noreply@triviaverse.com>'
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND') == 'True'

    # Elasticsearch
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or 'http://localhost:9200'

    # Redis / Background jobs
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'

    # Babel (i18n)
    BABEL_DEFAULT_LOCALE = os.environ.get('BABEL_DEFAULT_LOCALE') or 'en'
    BABEL_DEFAULT_TIMEZONE = os.environ.get('BABEL_DEFAULT_TIMEZONE') or 'UTC'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
