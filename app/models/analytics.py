"""Analytics Models"""
from datetime import datetime
from app.extensions import db


class PlayerAnalytics(db.Model):
    __tablename__ = 'player_analytics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    games_played = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    average_time_per_question = db.Column(db.Float, default=0.0)
    best_combo = db.Column(db.Integer, default=0)
    coins_earned = db.Column(db.Integer, default=0)
    xp_earned = db.Column(db.Integer, default=0)
    play_time_minutes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='analytics')

    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'games_played': self.games_played,
            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'average_time_per_question': self.average_time_per_question,
            'best_combo': self.best_combo,
            'coins_earned': self.coins_earned,
            'xp_earned': self.xp_earned,
            'play_time_minutes': self.play_time_minutes
        }

    def __repr__(self):
        return f'<PlayerAnalytics user={self.user_id} date={self.date}>'


class CategoryAnalytics(db.Model):
    __tablename__ = 'category_analytics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    questions_answered = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    average_time = db.Column(db.Float, default=0.0)
    last_played = db.Column(db.DateTime, default=datetime.utcnow)
    is_weak = db.Column(db.Boolean, default=False)  # accuracy < 50%
    is_strong = db.Column(db.Boolean, default=False)  # accuracy > 85%

    user = db.relationship('User', backref='category_analytics')

    @property
    def accuracy(self):
        if self.questions_answered == 0:
            return 0.0
        return (self.correct_answers / self.questions_answered) * 100

    def __repr__(self):
        return f'<CategoryAnalytics user={self.user_id} category={self.category}>'


class ServerAnalytics(db.Model):
    __tablename__ = 'server_analytics'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    total_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    questions_answered = db.Column(db.Integer, default=0)
    coins_circulated = db.Column(db.Integer, default=0)
    new_registrations = db.Column(db.Integer, default=0)
    revenue_coins = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'total_users': self.total_users,
            'active_users': self.active_users,
            'games_played': self.games_played,
            'new_registrations': self.new_registrations
        }

    def __repr__(self):
        return f'<ServerAnalytics date={self.date}>'
