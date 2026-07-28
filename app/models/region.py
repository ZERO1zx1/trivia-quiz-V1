"""Global Region System Models"""
from datetime import datetime
from app.extensions import db


class Region(db.Model):
    __tablename__ = 'regions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)  # eu, na, asia, mn, jp, kr, ru
    flag_url = db.Column(db.String(500), default='')
    description = db.Column(db.Text, default='')
    player_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    ping_server_url = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    leaderboards = db.relationship('RegionLeaderboard', back_populates='region', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'player_count': self.player_count,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<Region {self.code}: {self.name}>'


class RegionLeaderboard(db.Model):
    __tablename__ = 'region_leaderboards'

    id = db.Column(db.Integer, primary_key=True)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    xp = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float, default=0.0)
    level = db.Column(db.Integer, default=1)
    elo_rating = db.Column(db.Integer, default=1200)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    region = db.relationship('Region', back_populates='leaderboards')
    user = db.relationship('User', backref='region_leaderboard_entries')

    def __repr__(self):
        return f'<RegionLeaderboard region={self.region_id} user={self.user_id} rank={self.rank}>'
