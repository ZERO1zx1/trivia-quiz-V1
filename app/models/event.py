"""Event System Models"""
from datetime import datetime
from app.extensions import db, utcnow


class GameEvent(db.Model):
    __tablename__ = 'game_events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    event_type = db.Column(db.String(30), nullable=False)  # seasonal, holiday, limited, special_boss, anniversary
    theme = db.Column(db.String(100), default='')
    banner_url = db.Column(db.String(500), default='')
    icon_url = db.Column(db.String(500), default='')
    status = db.Column(db.String(20), default='upcoming')  # upcoming, active, ended
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    region = db.Column(db.String(10), default='global')
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    rewards = db.relationship('EventReward', back_populates='event', lazy='dynamic')
    participants = db.relationship('EventParticipant', back_populates='event', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'event_type': self.event_type,
            'status': self.status,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_featured': self.is_featured
        }

    def __repr__(self):
        return f'<GameEvent {self.name}>'


class EventReward(db.Model):
    __tablename__ = 'event_rewards'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('game_events.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    reward_type = db.Column(db.String(50), nullable=False)  # badge, frame, title, aura, pet, coins, xp, box
    item_id = db.Column(db.Integer, nullable=True)
    rarity = db.Column(db.String(20), default='common')
    image_url = db.Column(db.String(500), default='')
    requirement = db.Column(db.Text, default='')  # JSON: e.g., {"type": "score", "value": 1000}
    is_limited = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    event = db.relationship('GameEvent', back_populates='rewards')

    def __repr__(self):
        return f'<EventReward {self.name} for event={self.event_id}>'


class EventParticipant(db.Model):
    __tablename__ = 'event_participants'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('game_events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    progress = db.Column(db.Integer, default=0)
    rewards_claimed = db.Column(db.Text, default='')  # JSON array of claimed reward IDs
    joined_at = db.Column(db.DateTime, default=utcnow)

    event = db.relationship('GameEvent', back_populates='participants')
    user = db.relationship('User', backref='event_participations')

    def __repr__(self):
        return f'<EventParticipant event={self.event_id} user={self.user_id} score={self.score}>'
