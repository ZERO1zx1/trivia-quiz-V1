"""Economy and Shop Models"""
from datetime import datetime
from app.extensions import db

# -------------------------------
#  Санхүүгийн гүйлгээ
# -------------------------------
class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Integer, nullable=False)          # эерэг=орлого, сөрөг=зарлага
    type = db.Column(db.String(20), nullable=False)         # 'credit' / 'debit'
    reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'type': self.type,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Transaction {self.type} {self.amount}>'


# -------------------------------
#  Манлайлагчдын самбар
# -------------------------------
class LeaderboardEntry(db.Model):
    __tablename__ = 'leaderboard_entries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    period = db.Column(db.String(20), default='alltime')   # daily, weekly, monthly, alltime
    score = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'period': self.period,
            'score': self.score,
            'wins': self.wins,
            'games_played': self.games_played,
            'accuracy': self.accuracy
        }

    def __repr__(self):
        return f'<LeaderboardEntry {self.user_id} {self.period}>'