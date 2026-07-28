"""Marketplace System Models"""
from datetime import datetime
from app.extensions import db


class MarketplaceListing(db.Model):
    __tablename__ = 'marketplace_listings'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # badge, frame, title, aura, box, pet, emote, music, theme
    item_id = db.Column(db.Integer, nullable=False)  # reference to the item in shop_items or specific table
    item_name = db.Column(db.String(100), nullable=False)
    item_image = db.Column(db.String(500), default='')
    price = db.Column(db.Integer, nullable=False)  # in coins
    original_price = db.Column(db.Integer, nullable=True)  # for discount display
    rarity = db.Column(db.String(20), default='common')
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='active')  # active, sold, expired, cancelled
    quantity = db.Column(db.Integer, default=1)
    duration_hours = db.Column(db.Integer, default=72)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    sold_at = db.Column(db.DateTime)

    seller = db.relationship('User', backref='marketplace_listings', foreign_keys=[seller_id])

    def to_dict(self):
        return {
            'id': self.id,
            'seller': self.seller.to_dict() if self.seller else None,
            'item_type': self.item_type,
            'item_name': self.item_name,
            'item_image': self.item_image,
            'price': self.price,
            'original_price': self.original_price,
            'rarity': self.rarity,
            'quantity': self.quantity,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<MarketplaceListing {self.item_name} by user={self.seller_id}>'


class MarketplaceTransaction(db.Model):
    __tablename__ = 'marketplace_transactions'

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('marketplace_listings.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    tax = db.Column(db.Integer, default=0)  # marketplace tax (e.g., 5%)
    net_seller_amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    buyer = db.relationship('User', foreign_keys=[buyer_id])
    seller = db.relationship('User', foreign_keys=[seller_id])

    def __repr__(self):
        return f'<MarketplaceTransaction listing={self.listing_id} price={self.price}>'


class Auction(db.Model):
    __tablename__ = 'auctions'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    starting_price = db.Column(db.Integer, nullable=False)
    current_bid = db.Column(db.Integer, nullable=True)
    current_bidder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    buy_now_price = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, ended, cancelled
    duration_hours = db.Column(db.Integer, default=24)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ends_at = db.Column(db.DateTime)
    winner_id = db.Column(db.Integer, nullable=True)
    final_price = db.Column(db.Integer, nullable=True)

    seller = db.relationship('User', backref='auctions', foreign_keys=[seller_id])
    current_bidder = db.relationship('User', foreign_keys=[current_bidder_id])

    def __repr__(self):
        return f'<Auction {self.item_name} current_bid={self.current_bid}>'


class AuctionBid(db.Model):
    __tablename__ = 'auction_bids'

    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id'), nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    auction = db.relationship('Auction', backref='bids')
    bidder = db.relationship('User', backref='auction_bids')

    def __repr__(self):
        return f'<AuctionBid auction={self.auction_id} amount={self.amount}>'
