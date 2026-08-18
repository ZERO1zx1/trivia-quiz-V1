"""Replay System Models"""
from datetime import datetime
from app.extensions import db, utcnow
import json


class Replay(db.Model):
    __tablename__ = 'replays'

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default='')
    game_mode = db.Column(db.String(30), default='classic')
    category = db.Column(db.String(100), default='')
    difficulty = db.Column(db.String(20), default='mixed')
    duration_seconds = db.Column(db.Integer, default=0)
    result = db.Column(db.String(20), default='')  # win, loss, draw
    player_stats = db.Column(db.Text, default='')  # JSON: accuracy, score, combo_max, etc.
    events_data = db.Column(db.Text, default='')  # JSON: list of replay events
    is_public = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship('User', backref='replays')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'game_mode': self.game_mode,
            'category': self.category,
            'difficulty': self.difficulty,
            'duration_seconds': self.duration_seconds,
            'result': self.result,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat()
        }

    def get_events(self):
        return json.loads(self.events_data) if self.events_data else []

    def __repr__(self):
        return f'<Replay {self.title} mode={self.game_mode}>'


class ReplayEvent(db.Model):
    __tablename__ = 'replay_events'

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey('replays.id'), nullable=False)
    timestamp_ms = db.Column(db.Integer, default=0)  # milliseconds from start
    event_type = db.Column(db.String(50), nullable=False)  # question_shown, answer_submitted, correct, wrong, combo, elimination
    player_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    data = db.Column(db.Text, default='')  # JSON: event-specific data
    created_at = db.Column(db.DateTime, default=utcnow)

    replay = db.relationship('Replay', backref='events')
    player = db.relationship('User', foreign_keys=[player_id])

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp_ms': self.timestamp_ms,
            'event_type': self.event_type,
            'player_id': self.player_id,
            'data': self.data
        }

    def __repr__(self):
        return f'<ReplayEvent type={self.event_type} ts={self.timestamp_ms}>'


class ReplayLike(db.Model):
    __tablename__ = 'replay_likes'

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey('replays.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    replay = db.relationship('Replay', backref='likes')
    user = db.relationship('User', backref='replay_likes')

    def __repr__(self):
        return f'<ReplayLike replay={self.replay_id} user={self.user_id}>'
