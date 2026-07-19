"""Achievement Models"""
from datetime import datetime
from app.extensions import db

class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100), default='trophy')
    category = db.Column(db.String(50))
    requirement_type = db.Column(db.String(50))
    requirement_value = db.Column(db.Integer, default=0)
    xp_reward = db.Column(db.Integer, default=0)
    coin_reward = db.Column(db.Integer, default=0)
    rarity = db.Column(db.String(20), default='common')
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_achievements = db.relationship('UserAchievement', back_populates='achievement', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'category': self.category,
            'xp_reward': self.xp_reward,
            'coin_reward': self.coin_reward,
            'rarity': self.rarity
        }

    def check_requirement(self, user):
        """Тухайн хэрэглэгч шаардлагыг хангасан эсэхийг шалгах"""
        if self.requirement_type == 'wins_count':
            return user.wins >= self.requirement_value
        elif self.requirement_type == 'games_count':
            return user.games_played >= self.requirement_value
        elif self.requirement_type == 'accuracy_rate':
            return user.accuracy >= self.requirement_value
        # Бусад төрөл нэмж болно
        return False

    def __repr__(self):
        return f'<Achievement {self.name}>'


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'))
    progress = db.Column(db.Integer, default=0)
    is_unlocked = db.Column(db.Boolean, default=False)
    unlocked_at = db.Column(db.DateTime)

    user = db.relationship('User', back_populates='achievements')
    achievement = db.relationship('Achievement', back_populates='user_achievements')

    def to_dict(self):
        return {
            'id': self.id,
            'achievement': self.achievement.to_dict() if self.achievement else None,
            'progress': self.progress,
            'is_unlocked': self.is_unlocked,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None
        }

    def update_progress(self, value):
        """Прогресс шинэчлэх, шаардлага хангагдсан бол unlock хийх"""
        self.progress = value
        if self.achievement and self.progress >= self.achievement.requirement_value:
            if not self.is_unlocked:
                self.is_unlocked = True
                self.unlocked_at = datetime.utcnow()
                return True  # Шинээр unlock хийгдсэн
        return False

    def __repr__(self):
        return f'<UserAchievement {self.user_id}:{self.achievement_id}>'