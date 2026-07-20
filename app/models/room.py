"""Room and Game Models"""
from datetime import datetime
from app.extensions import db

class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_private = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(100))
    max_players = db.Column(db.Integer, default=8)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    difficulty = db.Column(db.String(20), default='mixed')
    question_count = db.Column(db.Integer, default=10)
    time_per_question = db.Column(db.Integer, default=20)
    status = db.Column(db.String(20), default='waiting')
    current_question = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    game_mode = db.Column(db.String(20), default='classic')
    survival_lives = db.Column(db.Integer, default=3)
    time_attack_duration = db.Column(db.Integer, default=15)

    host = db.relationship('User', foreign_keys=[host_id])
    players = db.relationship('RoomPlayer', back_populates='room', lazy='dynamic',
                              cascade='all, delete-orphan')
    match = db.relationship('Match', back_populates='room', uselist=False)

    def get_player_count(self):
        return self.players.count()

    def get_ready_count(self):
        return RoomPlayer.query.filter_by(room_id=self.id, is_ready=True).count()

    def is_full(self):
        return self.get_player_count() >= self.max_players

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'host_id': self.host_id,
            'is_private': self.is_private,
            'max_players': self.max_players,
            'player_count': self.get_player_count(),
            'ready_count': self.get_ready_count(),
            'difficulty': self.difficulty,
            'question_count': self.question_count,
            'status': self.status,
            'game_mode': self.game_mode,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Room {self.code}>'


class RoomPlayer(db.Model):
    __tablename__ = 'room_players'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_ready = db.Column(db.Boolean, default=False)
    is_spectator = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    max_streak = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Float, default=0.0)
    survival_lives = db.Column(db.Integer, default=3)  # Survival Mode-д хэрэглэнэ

    room = db.relationship('Room', back_populates='players')
    user = db.relationship('User', back_populates='room_players')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'avatar': self.user.avatar_url if self.user else None,
            'is_ready': self.is_ready,
            'is_spectator': self.is_spectator,
            'score': self.score,
            'correct_answers': self.correct_answers,
            'streak': self.streak,
            'survival_lives': self.survival_lives
        }


class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    difficulty = db.Column(db.String(20))
    question_count = db.Column(db.Integer)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

    room = db.relationship('Room', back_populates='match')
    winner = db.relationship('User', foreign_keys=[winner_id])
    scores = db.relationship('Score', back_populates='match', lazy='dynamic')


class Score(db.Model):
    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    score = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float, default=0.0)
    avg_time = db.Column(db.Float, default=0.0)
    max_streak = db.Column(db.Integer, default=0)

    match = db.relationship('Match', back_populates='scores')
    user = db.relationship('User', back_populates='scores')