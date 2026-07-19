from datetime import datetime, date
from app.extensions import db

class DailyQuest(db.Model):
    __tablename__ = 'daily_quests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quest_type = db.Column(db.String(50), nullable=False)  # play_games, win_games, correct_answers
    target_value = db.Column(db.Integer, nullable=False)
    current_value = db.Column(db.Integer, default=0)
    reward_coins = db.Column(db.Integer, default=50)
    reward_xp = db.Column(db.Integer, default=25)
    is_completed = db.Column(db.Boolean, default=False)
    is_claimed = db.Column(db.Boolean, default=False)
    date_assigned = db.Column(db.Date, nullable=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('daily_quests', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'quest_type': self.quest_type,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'reward_coins': self.reward_coins,
            'reward_xp': self.reward_xp,
            'is_completed': self.is_completed,
            'is_claimed': self.is_claimed,
            'progress': int((self.current_value / self.target_value) * 100) if self.target_value > 0 else 0
        }