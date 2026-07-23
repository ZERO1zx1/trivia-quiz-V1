from .economy import Transaction, LeaderboardEntry
from .shop import ShopItem, UserInventory
from .user import User, DiscordAccount, Friend
from .notification import Notification
from .achievement import Achievement, UserAchievement
from .box import Box, UserBox
from .profile import ProfileView, UserRespect

def register_blueprints(app):
    app.register_blueprint(social_bp, url_prefix='/social')
    app.register_blueprint(account_bp, url_prefix='/account')