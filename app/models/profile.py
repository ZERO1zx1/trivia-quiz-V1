"""Profile related models"""
from datetime import datetime
from app.extensions import db

class ProfileView(db.Model):
    __tablename__ = 'profile_views'

    id = db.Column(db.Integer, primary_key=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    viewer = db.relationship('User', foreign_keys=[viewer_id], backref='viewed_profiles')
    profile = db.relationship('User', foreign_keys=[profile_id], backref='profile_visitors')


class UserRespect(db.Model):
    __tablename__ = 'user_respects'

    id = db.Column(db.Integer, primary_key=True)
    giver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    giver = db.relationship('User', foreign_keys=[giver_id], backref='given_respects')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_respects')


class GameChallenge(db.Model):
    __tablename__ = 'game_challenges'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_challenges')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_challenges')


class GiftTransaction(db.Model):
    __tablename__ = 'gift_transactions'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gift_type = db.Column(db.String(50))  # coffee, crown, xp_boost
    coin_amount = db.Column(db.Integer, default=0)
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_gifts')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_gifts')