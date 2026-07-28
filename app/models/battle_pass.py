"""Battle Pass & Season System Models"""
from datetime import datetime
from app.extensions import db


class Season(db.Model):
    __tablename__ = 'seasons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.Integer, nullable=False, unique=True)
    theme = db.Column(db.String(100), default='')
    banner_url = db.Column(db.String(500), default='')
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    battle_passes = db.relationship('BattlePass', back_populates='season', lazy='dynamic')

    def __repr__(self):
        return f'<Season {self.number}: {self.name}>'


class BattlePass(db.Model):
    __tablename__ = 'battle_passes'

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), nullable=False)
    tier = db.Column(db.String(20), default='free')  # free, premium
    name = db.Column(db.String(100), nullable=False)
    max_level = db.Column(db.Integer, default=50)
    price = db.Column(db.Integer, default=0)  # coins for premium
    premium_price = db.Column(db.Integer, default=1500)  # real money equivalent
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    season = db.relationship('Season', back_populates='battle_passes')
    rewards = db.relationship('BattlePassReward', back_populates='battle_pass', lazy='dynamic')

    def __repr__(self):
        return f'<BattlePass {self.name} Tier={self.tier}>'


class BattlePassReward(db.Model):
    __tablename__ = 'battle_pass_rewards'

    id = db.Column(db.Integer, primary_key=True)
    battle_pass_id = db.Column(db.Integer, db.ForeignKey('battle_passes.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    tier = db.Column(db.String(20), default='free')  # free, premium
    reward_type = db.Column(db.String(50), nullable=False)  # coins, xp, box, badge, frame, title, aura, pet, emote
    reward_id = db.Column(db.Integer, nullable=True)  # reference to the actual reward item
    reward_value = db.Column(db.Integer, default=0)  # coins amount, xp amount, etc.
    reward_name = db.Column(db.String(100))
    is_claimed = db.Column(db.Boolean, default=False)

    battle_pass = db.relationship('BattlePass', back_populates='rewards')

    def __repr__(self):
        return f'<BattlePassReward Level={self.level} Type={self.reward_type}>'


class BattlePassProgress(db.Model):
    __tablename__ = 'battle_pass_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    battle_pass_id = db.Column(db.Integer, db.ForeignKey('battle_passes.id'), nullable=False)
    current_level = db.Column(db.Integer, default=0)
    xp = db.Column(db.Integer, default=0)
    xp_needed = db.Column(db.Integer, default=100)
    is_premium = db.Column(db.Boolean, default=False)
    claimed_levels = db.Column(db.Text, default='')  # JSON array of claimed levels
    last_claimed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='battle_pass_progress')
    battle_pass = db.relationship('BattlePass', backref='user_progress')

    def to_dict(self):
        return {
            'current_level': self.current_level,
            'xp': self.xp,
            'xp_needed': self.xp_needed,
            'is_premium': self.is_premium,
            'claimed_levels': self.claimed_levels
        }

    def __repr__(self):
        return f'<BattlePassProgress user={self.user_id} level={self.current_level}>'
