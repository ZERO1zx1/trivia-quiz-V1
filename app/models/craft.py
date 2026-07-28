"""Crafting System Models"""
from datetime import datetime
from app.extensions import db


class CraftRecipe(db.Model):
    __tablename__ = 'craft_recipes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    recipe_type = db.Column(db.String(30), nullable=False)  # badge, frame, aura, title, enchant, fusion
    output_type = db.Column(db.String(50), nullable=False)  # badge, frame, aura, title
    output_item_id = db.Column(db.Integer, nullable=True)  # reference to shop_items
    rarity = db.Column(db.String(20), default='common')
    ingredients = db.Column(db.Text, nullable=False)  # JSON: [{"item_id": 1, "quantity": 3}, ...]
    coins_required = db.Column(db.Integer, default=0)
    craft_time_seconds = db.Column(db.Integer, default=300)
    success_rate = db.Column(db.Float, default=100.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'recipe_type': self.recipe_type,
            'output_type': self.output_type,
            'rarity': self.rarity,
            'ingredients': self.ingredients,
            'coins_required': self.coins_required,
            'success_rate': self.success_rate
        }

    def __repr__(self):
        return f'<CraftRecipe {self.name}>'


class CraftingMaterial(db.Model):
    __tablename__ = 'crafting_materials'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    rarity = db.Column(db.String(20), default='common')
    source = db.Column(db.String(100), default='')  # drop, shop, event, quest
    drop_rate = db.Column(db.Float, default=0.0)
    image_url = db.Column(db.String(500), default='')
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<CraftingMaterial {self.name}>'


class UserCraftingProgress(db.Model):
    __tablename__ = 'user_crafting_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('craft_recipes.id'), nullable=False)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    result_item_id = db.Column(db.Integer, nullable=True)

    user = db.relationship('User', backref='crafting_progress')
    recipe = db.relationship('CraftRecipe', backref='user_crafting')

    def __repr__(self):
        return f'<UserCraftingProgress user={self.user_id} recipe={self.recipe_id}>'
