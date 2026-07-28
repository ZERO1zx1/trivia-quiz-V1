"""Collection Book Models"""
from datetime import datetime
from app.extensions import db


class CollectionItem(db.Model):
    __tablename__ = 'collection_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    collection_type = db.Column(db.String(30), nullable=False)  # badge, frame, title, boss, event, music, anime, movie, country, question, category
    category = db.Column(db.String(100), default='')
    rarity = db.Column(db.String(20), default='common')  # common, rare, epic, legendary, mythic
    image_url = db.Column(db.String(500), default='')
    source = db.Column(db.String(100), default='')  # how to obtain
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    progress_entries = db.relationship('CollectionProgress', back_populates='item', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'collection_type': self.collection_type,
            'category': self.category,
            'rarity': self.rarity,
            'image_url': self.image_url
        }

    def __repr__(self):
        return f'<CollectionItem {self.name} type={self.collection_type}>'


class CollectionProgress(db.Model):
    __tablename__ = 'collection_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('collection_items.id'), nullable=False)
    is_collected = db.Column(db.Boolean, default=False)
    collected_at = db.Column(db.DateTime, nullable=True)
    quantity = db.Column(db.Integer, default=0)
    completion_percentage = db.Column(db.Float, default=0.0)

    user = db.relationship('User', backref='collection_progress')
    item = db.relationship('CollectionItem', back_populates='progress_entries')

    def __repr__(self):
        return f'<CollectionProgress user={self.user_id} item={self.item_id}>'


class CollectionReward(db.Model):
    __tablename__ = 'collection_rewards'

    id = db.Column(db.Integer, primary_key=True)
    collection_type = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    completion_threshold = db.Column(db.Integer, nullable=False)  # e.g., 100 for 100%
    reward_type = db.Column(db.String(50), nullable=False)  # badge, frame, title, coins, xp
    reward_id = db.Column(db.Integer, nullable=True)
    reward_value = db.Column(db.Integer, default=0)
    reward_name = db.Column(db.String(100))

    def __repr__(self):
        return f'<CollectionReward {self.collection_type}/{self.category} at {self.completion_threshold}%>'
