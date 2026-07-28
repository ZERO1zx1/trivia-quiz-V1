"""TriviaVerse Configuration - Enterprise Edition v3.0"""
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

    # ================= ENTERPRISE SYSTEMS =================

    # Guild System
    GUILD_CREATION_COST = 1000
    GUILD_MAX_MEMBERS = 50
    GUILD_MAX_GUILDS_PER_USER = 1
    GUILD_XP_PER_LEVEL = 1000
    GUILD_LEVEL_CAP = 100
    GUILD_INVITE_EXPIRY_HOURS = 48

    # Tournament System
    TOURNAMENT_MAX_PARTICIPANTS = 128
    TOURNAMENT_MIN_PARTICIPANTS = 4
    TOURNAMENT_TYPES = ['bracket', 'round_robin', 'ladder']
    TOURNAMENT_CATEGORIES = ['general', 'science', 'history', 'geography', 'entertainment', 'sports']
    TOURNAMENT_DIFFICULTIES = ['mixed', 'easy', 'medium', 'hard']
    TOURNAMENT_ELO_GAIN_BASE = 25
    TOURNAMENT_ELO_LOSS_BASE = 20

    # Battle Pass
    BATTLE_PASS_SEASON_LENGTH_DAYS = 90
    BATTLE_PASS_FREE_TIER_COUNT = 30
    BATTLE_PASS_PREMIUM_TIER_COUNT = 30
    BATTLE_PASS_PREMIUM_COST = 500

    # Pet System
    PET_MAX_ENERGY = 100
    PET_MAX_HAPPINESS = 100
    PET_ENERGY_DRAIN_RATE = 5  # per hour
    PET_HAPPINESS_DRAIN_RATE = 3  # per hour
    PET_FEED_ENERGY_RESTORE = 20
    PET_FEED_HAPPINESS_RESTORE = 10
    PET_EVOLUTION_LEVEL = 10

    # Crafting System
    CRAFT_MATERIAL_PER_HOUR = 1
    CRAFT_STORAGE_CAPACITY = 1000
    CRAFT_XP_PER_CRAFT = 50

    # Mail System
    MAIL_MAX_ATTACHMENT_SIZE = 5  # MB
    MAIL_ATTACHMENT_EXPIRY_DAYS = 7
    MAIL_STORAGE_LIMIT = 100

    # Marketplace
    MARKETPLACE_LISTING_FEE_PERCENT = 5  # 5% platform fee
    MARKETPLACE_MAX_PRICE = 100000
    MARKETPLACE_MIN_PRICE = 1
    MARKETPLACE_LISTING_DURATION_DAYS = 14

    # Chat System
    CHAT_MESSAGE_LIMIT = 2000  # characters per message
    CHAT_RATE_LIMIT = 5  # messages per minute
    CHAT_MUTE_DURATION = 300  # seconds for rate limit violation
    CHAT_HISTORY_LIMIT = 1000

    # Event System
    EVENT_MAX_REWARDS = 10
    EVENT_PARTICIPATION_LIMIT = 5  # max concurrent events
    EVENT_REWARD_EXPIRY_DAYS = 3

    # Region System
    REGION_LEADERBOARD_SIZE = 100
    REGION_STATS_UPDATE_INTERVAL = 3600  # seconds

    # Collection Book
    COLLECTION_BOOK_MAX_ITEMS = 500
    COLLECTION_REWARD_COINS = 100

    # Community Forum
    FORUM_POST_LIMIT_PER_DAY = 10
    FORUM_COMMENT_LIMIT_PER_DAY = 50
    FORUM_POST_EDIT_TIME_LIMIT = 300  # seconds

    # Puzzle Mode
    PUZZLE_DAILY_RESET_HOUR = 0  # UTC
    PUZZLE_MAX_HINTS = 3
    PUZZLE_HINT_COST = 50
    PUZZLE_TIME_BONUS_MULTIPLIER = 2

    # Replay System
    REPLAY_MAX_DURATION = 300  # seconds
    REPLAY_STORAGE_LIMIT = 50  # per user
    REPLAY_SHARE_COOLDOWN = 300  # seconds

    # AI Question Generator
    AI_GENERATION_COST_COINS = 10
    AI_MAX_QUESTIONS_PER_DAY = 20

    # Voice Quiz
    VOICE_QUIZ_MAX_DURATION = 30  # seconds per audio
    VOICE_QUIZ_AUDIO_FORMATS = ['mp3', 'wav', 'ogg']

    # Image Quiz
    IMAGE_QUIZ_MAX_SIZE = 5 * 1024 * 1024  # 5MB
    IMAGE_QUIZ_FORMATS = ['png', 'jpg', 'jpeg', 'webp']

    # Video Quiz
    VIDEO_QUIZ_MAX_DURATION = 60  # seconds
    VIDEO_QUIZ_MAX_SIZE = 50 * 1024 * 1024  # 50MB

    # Music Quiz
    MUSIC_QUIZ_CLIP_DURATION = 15  # seconds
    MUSIC_QUIZ_FORMATS = ['mp3', 'wav', 'ogg']

    # Community System
    COMMUNITY_POST_RATE_LIMIT = 5  # per hour
    COMMUNITY_COMMENT_RATE_LIMIT = 20  # per hour
    COMMUNITY_MAX_BOOKMARKS = 100

    # Learning System
    LEARNING_PATH_DURATION_DAYS = 30
    LEARNING_MODULE_DURATION_HOURS = 4
    LEARNING_DAILY_LIMIT = 3  # modules per day

    # Analytics
    ANALYTICS_RETENTION_DAYS = 365
    ANALYTICS_BATCH_SIZE = 1000

    # Companion/Pet Premium
    COMPANION_PET_SLOTS = 3
    COMPANION_SKIN_SLOTS = 10
    COMPANION_PREMIUM_COST = 2000

    # Settings / Security
    TOTP_ISSUER_NAME = 'TriviaVerse'
    SESSION_DURATION_DAYS = 30
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128

    # PvP Ranked
    ELO_INITIAL = 1200
    ELO_K_FACTOR = 32
    ELO_GAIN_PER_WIN = 25
    ELO_LOSS_PER_DEFEAT = 20

    # Premium Cosmetics
    PREMIUM_COSMETIC_TIERS = ['standard', 'premium', 'ultimate']

    # Inventory 2.0
    INVENTORY_STACK_SIZE = 999
    INVENTORY_TABS = 10
    INVENTORY_ITEMS_PER_TAB = 50

    # Economy 2.0
    ECONOMY_INFLATION_RATE = 0.02  # 2% per season
    ECONOMY_TAX_RATE = 0.05  # 5% on transactions

    # Reward System
    REWARD_DAILY_LOGIN_BASE = 50
    REWARD_DAILY_LOGIN_INCREMENT = 10
    REWARD_MAX_STREAK_MULTIPLIER = 3

    # Achievement 2.0
    ACHIEVEMENT_POINTS_PER_TIER = 100
    ACHIEVEMENT_SHOWCASE_SLOTS = 6

    # Event System
    EVENT_TYPES = ['seasonal', 'limited', 'recurring', 'special', 'daily_challenge', 'weekly_challenge', 'global_event']

    # Admin Dashboard
    ADMIN_DASHBOARD_REFRESH_INTERVAL = 300  # seconds
    ADMIN_METRICS_RETENTION_DAYS = 90

    # DevOps
    HEALTH_CHECK_INTERVAL = 60  # seconds
    BACKUP_FREQUENCY_HOURS = 24
    LOG_RETENTION_DAYS = 30
    CDN_BASE_URL = os.environ.get('CDN_BASE_URL') or ''

    # API Rate Limits
    API_RATE_LIMIT_PER_MINUTE = 60
    API_RATE_LIMIT_PER_HOUR = 1000
    API_RATE_LIMIT_PER_DAY = 10000

    # Premium Features
    PREMIUM_COIN_MULTIPLIER = 1.5
    PREMIUM_XP_MULTIPLIER = 1.5
    PREMIUM_SKIN_SLOTS = 5
    PREMIUM_AVATAR_SLOTS = 10


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'


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
