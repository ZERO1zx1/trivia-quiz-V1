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
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your-api-key'

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

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('TriviaVerse', app.config['MAIL_USERNAME'])

# Имэйл илгээх санг холбох
mail = Mail(app)

@app.route('/')
def index():
    return "Имэйл тохиргоо бэлэн боллоо!"

if __name__ == '__main__':
    app.run(debug=True)