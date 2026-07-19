"""User Model"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
import jwt
from time import time
from flask import current_app
from app.models import Transaction
from app.models.shop import UserInventory

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    avatar_url = db.Column(db.String(500), default='/static/avatars/default.png')
    banner_url = db.Column(db.String(500), default='/static/backgrounds/default-banner.jpg')
    bio = db.Column(db.Text, default='')
    country = db.Column(db.String(100), default='')
    display_name = db.Column(db.String(100))
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    coins = db.Column(db.Integer, default=500)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    total_correct = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    average_time = db.Column(db.Float, default=0.0)
    accuracy = db.Column(db.Float, default=0.0)
    is_online = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_daily_reward = db.Column(db.DateTime)

    # Relationships
    discord_account = db.relationship('DiscordAccount', back_populates='user', uselist=False)
    room_players = db.relationship('RoomPlayer', back_populates='user', lazy='dynamic')
    scores = db.relationship('Score', back_populates='user', lazy='dynamic')
    achievements = db.relationship('UserAchievement', back_populates='user', lazy='dynamic')
    user_inventory_items = db.relationship('UserInventory', back_populates='user', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')
    sent_friends = db.relationship('Friend', foreign_keys='Friend.user_id', back_populates='user', lazy='dynamic')
    received_friends = db.relationship('Friend', foreign_keys='Friend.friend_id', back_populates='friend', lazy='dynamic')
    transactions = db.relationship('Transaction', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(id)

    def calculate_level(self):
        import math
        return int(math.floor(math.sqrt(self.xp / 100))) + 1

    def add_xp(self, amount):
        """XP нэмэх, шаардлагатай бол level up хийх"""
        self.xp += amount
        new_level = self.calculate_level()
        if new_level > self.level:
            old_level = self.level
            self.level = new_level
            # Level up хийсэн тохиолдолд урамшуулал өгөх
            self.coins += 50
            # Мэдэгдэл илгээх
            from app.utils.notify import send_notification
            send_notification(
                user_id=self.id,
                title='Level Up! 🎉',
                message=f'You are now level {new_level}!',
                notif_type='success'
            )
            return True, old_level, self.level
        return False, self.level, self.level

    def add_coins(self, amount, reason=''):
        self.coins += amount
        tx = Transaction(user_id=self.id, amount=amount, type='credit', reason=reason)
        db.session.add(tx)

    def update_accuracy(self):
        if self.total_questions > 0:
            self.accuracy = (self.total_correct / self.total_questions) * 100

    def get_friends(self):
        sent = Friend.query.filter_by(user_id=self.id, status='accepted').all()
        received = Friend.query.filter_by(friend_id=self.id, status='accepted').all()
        friends = []
        for f in sent:
            friends.append(f.friend)
        for f in received:
            friends.append(f.user)
        return friends

    def get_unread_notifications_count(self):
        from app.models.notification import Notification
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    def __repr__(self):
        return f'<User {self.username}>'


class DiscordAccount(db.Model):
    __tablename__ = 'discord_accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    discord_id = db.Column(db.String(64), unique=True, nullable=False)
    discord_username = db.Column(db.String(100))
    discord_avatar = db.Column(db.String(500))
    access_token = db.Column(db.String(500))
    refresh_token = db.Column(db.String(500))
    token_expires_at = db.Column(db.DateTime)

    # Заавал back_populates таарах ёстой
    user = db.relationship('User', back_populates='discord_account')

    def __repr__(self):
        return f'<DiscordAccount {self.discord_username}>'


class Friend(db.Model):
    __tablename__ = 'friends'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], back_populates='sent_friends')
    friend = db.relationship('User', foreign_keys=[friend_id], back_populates='received_friends')