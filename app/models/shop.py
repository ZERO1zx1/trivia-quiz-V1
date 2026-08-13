from datetime import datetime
from app.extensions import db

# -------------------------------
#  Дэлгүүрийн бараа
# -------------------------------
class ShopItem(db.Model):
    __tablename__ = 'shop_items'
    __table_args__ = (
        db.CheckConstraint('price >= 0', name='ck_shop_items_price'),
        db.CheckConstraint('base_price >= 0', name='ck_shop_items_base_price'),
        db.CheckConstraint('stock >= -1', name='ck_shop_items_stock'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Integer, nullable=False)           # coin-оор үнэ
    base_price = db.Column(db.Integer, nullable=False, default=100)
    item_type = db.Column(db.String(50))                    # avatar_frame, title, role, badge, lifeline гэх мэт
    stock = db.Column(db.Integer, default=-1)               # -1 for infinite
    total_sold = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    premium_only = db.Column(db.Boolean, default=False)

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
    __table_args__ = (
        db.UniqueConstraint('user_id', 'item_id',
                            name='uq_user_inventory_user_item'),
        db.CheckConstraint('quantity >= 0',
                           name='ck_user_inventory_quantity'),
        db.CheckConstraint('locked_quantity >= 0',
                           name='ck_user_inventory_locked_nonnegative'),
        db.CheckConstraint('locked_quantity <= quantity',
                           name='ck_user_inventory_locked_lte_quantity'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    locked_quantity = db.Column(db.Integer, default=0)  # escrow / pending transfers
    is_equipped = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='user_inventory_items')
    item = db.relationship('ShopItem', back_populates='user_inventory')

    @property
    def available_quantity(self):
        """Quantity that can still be listed / transferred."""
        return max(0, (self.quantity or 0) - (self.locked_quantity or 0))

    def to_dict(self):
        return {
            'id': self.id,
            'item': self.item.to_dict() if self.item else None,
            'quantity': self.quantity,
            'is_equipped': self.is_equipped
        }

    def __repr__(self):
        return f'<UserInventory user={self.user_id} item={self.item_id}>'
