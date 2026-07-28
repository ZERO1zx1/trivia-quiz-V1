"""Pet / Companion System Models"""
from datetime import datetime
from app.extensions import db


class PetSpecies(db.Model):
    __tablename__ = 'pet_species'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100))
    description = db.Column(db.Text, default='')
    image_url = db.Column(db.String(500), default='')
    rarity = db.Column(db.String(20), default='common')  # common, rare, epic, legendary, mythic
    element = db.Column(db.String(20), default='none')  # fire, water, earth, air, light, dark
    base_stats = db.Column(db.Text, default='')  # JSON: {"attack": 10, "defense": 5, "speed": 15}
    evolves_to = db.Column(db.Integer, db.ForeignKey('pet_species.id'), nullable=True)
    evolution_level = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pets = db.relationship('Pet', back_populates='species', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'rarity': self.rarity,
            'element': self.element,
            'image_url': self.image_url
        }

    def __repr__(self):
        return f'<PetSpecies {self.name}>'


class Pet(db.Model):
    __tablename__ = 'pets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    species_id = db.Column(db.Integer, db.ForeignKey('pet_species.id'), nullable=False)
    name = db.Column(db.String(50), default='')
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)  # currently equipped
    is_bonded = db.Column(db.Boolean, default=False)
    happiness = db.Column(db.Integer, default=100)
    energy = db.Column(db.Integer, default=100)
    equipped_items = db.Column(db.Text, default='')  # JSON: {"head": id, "body": id, "accessory": id}
    buffs = db.Column(db.Text, default='')  # JSON: active buffs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_interacted = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='pets')
    species = db.relationship('PetSpecies', back_populates='pets')
    evolution_log = db.relationship('PetEvolution', back_populates='pet', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name or self.species.name,
            'species': self.species.to_dict() if self.species else None,
            'level': self.level,
            'xp': self.xp,
            'is_active': self.is_active,
            'happiness': self.happiness,
            'energy': self.energy
        }

    def __repr__(self):
        return f'<Pet {self.name} Lv.{self.level}>'


class PetEvolution(db.Model):
    __tablename__ = 'pet_evolution_log'

    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)
    from_species_id = db.Column(db.Integer, db.ForeignKey('pet_species.id'), nullable=False)
    to_species_id = db.Column(db.Integer, db.ForeignKey('pet_species.id'), nullable=False)
    level_at_evolution = db.Column(db.Integer)
    evolved_at = db.Column(db.DateTime, default=datetime.utcnow)

    pet = db.relationship('Pet', back_populates='evolution_log')

    def __repr__(self):
        return f'<PetEvolution pet={self.pet_id}>'


class PetEquipment(db.Model):
    __tablename__ = 'pet_equipment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slot = db.Column(db.String(20), nullable=False)  # head, body, accessory, weapon
    buff_type = db.Column(db.String(50), default='')
    buff_value = db.Column(db.Integer, default=0)
    rarity = db.Column(db.String(20), default='common')
    price = db.Column(db.Integer, default=100)
    image_url = db.Column(db.String(500), default='')
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<PetEquipment {self.name} Slot={self.slot}>'
