from datetime import datetime
from app.extensions import db

class Boss(db.Model):
    __tablename__ = 'bosses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    max_hp = db.Column(db.Integer, default=100000)
    current_hp = db.Column(db.Integer, default=100000)
    status = db.Column(db.String(20), default='active')  # active, defeated
    spawn_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)