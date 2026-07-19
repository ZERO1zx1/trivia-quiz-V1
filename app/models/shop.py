from datetime import datetime
from app.extensions import db

# -------------------------------
#  Дэлгүүрийн бараа
# -------------------------------
class ShopItem(db.Model):
    __tablename__ = 'shop_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Integer, nullable=False)           # coin-оор үнэ
    item_type = db.Column(db.String(50))                    # avatar_frame, title, role, badge гэх мэт
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Хэрэглэгчдийн инвентартэй холбох
    user_inventory = db.relationship('UserInventory', back_populates='item', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'item_type': self.item_type,
            'image_url': self.image_url,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<ShopItem {self.name}>'


# -------------------------------
#  Хэрэглэгчийн инвентар
# -------------------------------
class UserInventory(db.Model):
    __tablename__ = 'user_inventory'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    is_equipped = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='user_inventory_items')
    item = db.relationship('ShopItem', back_populates='user_inventory')

    def to_dict(self):
        return {
            'id': self.id,
            'item': self.item.to_dict() if self.item else None,
            'quantity': self.quantity,
            'is_equipped': self.is_equipped
        }

    def __repr__(self):
        return f'<UserInventory user={self.user_id} item={self.item_id}>'