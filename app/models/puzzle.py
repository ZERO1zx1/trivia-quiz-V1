"""Puzzle Mode Models"""
from datetime import datetime
from app.extensions import db


class Puzzle(db.Model):
    __tablename__ = 'puzzles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    puzzle_type = db.Column(db.String(30), nullable=False)  # sudoku, word_search, crossword, logic, memory_card, daily
    description = db.Column(db.Text, default='')
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard, expert
    data = db.Column(db.Text, nullable=False)  # JSON: puzzle data/state
    solution = db.Column(db.Text, default='')  # JSON: solution
    reward_coins = db.Column(db.Integer, default=50)
    reward_xp = db.Column(db.Integer, default=25)
    time_limit_seconds = db.Column(db.Integer, default=600)
    is_daily = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    attempts = db.relationship('PuzzleAttempt', back_populates='puzzle', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'puzzle_type': self.puzzle_type,
            'difficulty': self.difficulty,
            'reward_coins': self.reward_coins,
            'reward_xp': self.reward_xp,
            'time_limit_seconds': self.time_limit_seconds,
            'is_daily': self.is_daily
        }

    def __repr__(self):
        return f'<Puzzle {self.name} type={self.puzzle_type}>'


class PuzzleAttempt(db.Model):
    __tablename__ = 'puzzle_attempts'

    id = db.Column(db.Integer, primary_key=True)
    puzzle_id = db.Column(db.Integer, db.ForeignKey('puzzles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, failed, timeout
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    completion_time_seconds = db.Column(db.Integer, nullable=True)
    moves_count = db.Column(db.Integer, default=0)
    hints_used = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    is_perfect = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    puzzle = db.relationship('Puzzle', back_populates='attempts')
    user = db.relationship('User', backref='puzzle_attempts')

    def __repr__(self):
        return f'<PuzzleAttempt puzzle={self.puzzle_id} user={self.user_id} status={self.status}>'


class PuzzleLeaderboardEntry(db.Model):
    __tablename__ = 'puzzle_leaderboard'

    id = db.Column(db.Integer, primary_key=True)
    puzzle_id = db.Column(db.Integer, db.ForeignKey('puzzles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rank = db.Column(db.Integer)
    completion_time = db.Column(db.Integer)  # seconds
    score = db.Column(db.Integer, default=0)
    hints_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    puzzle = db.relationship('Puzzle', backref='leaderboard_entries')
    user = db.relationship('User', backref='puzzle_leaderboard_entries')

    def __repr__(self):
        return f'<PuzzleLeaderboardEntry puzzle={self.puzzle_id} rank={self.rank}>'
