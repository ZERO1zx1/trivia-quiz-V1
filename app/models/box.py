"""Box and Loot Models"""
from datetime import datetime
from app.extensions import db

class Box(db.Model):
    __tablename__ = 'boxes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    rarity = db.Column(db.String(20), default='common')  # common, rare, epic, legendary
    image_url = db.Column(db.String(255))
    price = db.Column(db.Integer, default=100)  # coin-оор үнэ
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Box {self.name}>'


class UserBox(db.Model):
    __tablename__ = 'user_boxes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    box_id = db.Column(db.Integer, db.ForeignKey('boxes.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    is_opened = db.Column(db.Boolean, default=False)
    opened_at = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('boxes', lazy='dynamic'))
    box = db.relationship('Box')

    def to_dict(self):
        return {
            'id': self.id,
            'box_name': self.box.name if self.box else None,
            'quantity': self.quantity,
            'rarity': self.box.rarity if self.box else None
        }