"""Premium Cosmetic & Companion System Models"""
from datetime import datetime
from app.extensions import db, utcnow


class Cosmetic(db.Model):
    __tablename__ = 'cosmetics'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100))
    description = db.Column(db.Text, default='')
    cosmetic_type = db.Column(db.String(50), nullable=False)  # avatar, banner, background, cursor, name_effect, gradient_name, glow, particle, profile_music, theme, decoration, emote, badge, aura, pet_skin
    rarity = db.Column(db.String(20), default='common')  # common, rare, epic, legendary, mythic
    price = db.Column(db.Integer, default=0)
    is_premium = db.Column(db.Boolean, default=False)
    is_animated = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(500), default='')
    animation_url = db.Column(db.String(500), default='')
    effect_config = db.Column(db.Text, default='')  # JSON: effect parameters
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    user_cosmetics = db.relationship('UserCosmetic', back_populates='cosmetic', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'cosmetic_type': self.cosmetic_type,
            'rarity': self.rarity,
            'price': self.price,
            'is_premium': self.is_premium,
            'is_animated': self.is_animated,
            'image_url': self.image_url
        }

    def __repr__(self):
        return f'<Cosmetic {self.name} type={self.cosmetic_type}>'


class UserCosmetic(db.Model):
    __tablename__ = 'user_cosmetics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cosmetic_id = db.Column(db.Integer, db.ForeignKey('cosmetics.id'), nullable=False)
    is_equipped = db.Column(db.Boolean, default=False)
    obtained_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship('User', backref='cosmetics_collection')
    cosmetic = db.relationship('Cosmetic', back_populates='user_cosmetics')

    def __repr__(self):
        return f'<UserCosmetic user={self.user_id} cosmetic={self.cosmetic_id}>'


class ProfileTheme(db.Model):
    __tablename__ = 'profile_themes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    music_url = db.Column(db.String(500), default='')
    background_url = db.Column(db.String(500), default='')
    color_scheme = db.Column(db.Text, default='')  # JSON: {"primary": "#7C3AED", "secondary": "#3B82F6"}
    particle_effect = db.Column(db.String(500), default='')
    cursor_url = db.Column(db.String(500), default='')
    price = db.Column(db.Integer, default=500)
    is_premium = db.Column(db.Boolean, default=False)
    rarity = db.Column(db.String(20), default='rare')
    is_active = db.Column(db.Boolean, default=True)

    user_themes = db.relationship('UserProfileTheme', back_populates='theme', lazy='dynamic')

    def __repr__(self):
        return f'<ProfileTheme {self.name}>'


class UserProfileTheme(db.Model):
    __tablename__ = 'user_profile_themes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    theme_id = db.Column(db.Integer, db.ForeignKey('profile_themes.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    obtained_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship('User', backref='profile_themes')
    theme = db.relationship('ProfileTheme', back_populates='user_themes')

    def __repr__(self):
        return f'<UserProfileTheme user={self.user_id} theme={self.theme_id}>'
