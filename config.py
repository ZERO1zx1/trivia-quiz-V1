"""TriviaVerse Configuration"""
import os
from dotenv import load_dotenv
from datetime import timedelta
from flask import Flask
from flask_mail import Mail

app = Flask(__name__)

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'triviaverse-dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///triviaverse.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'triviaverse-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID')
    DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET')
    DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI') or 'http://localhost:5000/auth/discord/callback'
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = '*'
    QUESTION_TIME_LIMIT = 20
    MAX_PLAYERS_PER_ROOM = 8
    MIN_PLAYERS_TO_START = 2
    DAILY_REWARD_COINS = 100
    WIN_REWARD_COINS = 50
    PERFECT_GAME_BONUS = 200
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'static/uploads'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your-actual-api-key'
    OWNER_USERNAME = os.environ.get('OWNER_USERNAME') or None
    API_BASE_URL = os.environ.get('API_BASE_URL') or 'http://localhost:5000/api'
    DISCORD_ERROR_WEBHOOK = os.environ.get('DISCORD_ERROR_WEBHOOK') or ''
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS') or 'http://localhost:5000'
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI') or 'memory://'
    OWNER_USERNAME = os.environ.get('OWNER_USERNAME') or None
    OWNER_DISCORD_ID = os.environ.get('OWNER_DISCORD_ID') or None
    OWNER_EMAIL = os.environ.get('OWNER_EMAIL') or None

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

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

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your-email@gmail.com'
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your-app-password'
MAIL_DEFAULT_SENDER = ('TriviaVerse', os.environ.get('MAIL_USERNAME') or 'your-email@gmail.com')

# Имэйл илгээх санг холбох
mail = Mail(app)

@app.route('/')
def index():
    return "Имэйл тохиргоо бэлэн боллоо!"

if __name__ == '__main__':
    app.run(debug=True)