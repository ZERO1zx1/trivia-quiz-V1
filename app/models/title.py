from app.extensions import db

class Title(db.Model):
    __tablename__ = 'titles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(50))
    color = db.Column(db.String(7), default='#FFFFFF')
    icon = db.Column(db.String(10))
    requirement = db.Column(db.String(100))
    rarity = db.Column(db.String(20), default='common')