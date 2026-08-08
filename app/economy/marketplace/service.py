"""Marketplace Service

Business logic for listings and purchases. All mutating operations run
inside a single transaction with FOR UPDATE row locks (FIX-005..FIX-008).
"""
from datetime import datetime, timedelta

from flask import current_app

from app.extensions import db
from app.models.marketplace import (MarketplaceListing, MarketplaceTransaction)
from app.models.shop import UserInventory
from app.economy.inventory.transactions import (
    EconomyError,
    InventoryError,
    deduct_coins,
    release_inventory,
    reserve_inventory,
    tax_transfer,
    transfer_inventory,
)

MAX_LISTING_PRICE = 1_000_000
DEFAULT_LISTING_DURATION_HOURS = 72
LISTING_TAX_RATE = 0.05


def validate_listing_input(item_id, price):
    """Return a list of error strings (empty = valid)."""
    errors = []
    if not item_id or price is None:
        errors.append('Invalid listing parameters.')
    elif price <= 0:
        errors.append('Price must be positive.')
    elif price > MAX_LISTING_PRICE:
        errors.append('Maximum listing price is 1,000,000 coins.')
    return errors


def create_listing(seller, item_id, price, duration_hours=None):
    """Reserve the seller's inventory item and publish a listing.

    Raises InventoryError / EconomyError with a human message on failure.
    """
    errors = validate_listing_input(item_id, price)
    if errors:
        raise EconomyError(errors[0])

    hours = duration_hours or DEFAULT_LISTING_DURATION_HOURS
    inventory_item = UserInventory.query.filter_by(
        user_id=seller.id, item_id=item_id).first()
    if inventory_item is None:
        raise InventoryError('You do not own this item.')
    if inventory_item.is_equipped:
        raise InventoryError('Cannot list equipped items.')

    # Reserve the exact quantity so no other listing/transfer can use it.
    reserve_inventory(inventory_item, 1)

    listing = MarketplaceListing(
        seller_id=seller.id,
        item_type=inventory_item.item.item_type if inventory_item.item else 'other',
        item_id=item_id,
        item_name=inventory_item.item.name if inventory_item.item else 'Unknown',
        item_image=inventory_item.item.image_url if inventory_item.item else '',
        price=price,
        rarity=inventory_item.item.rarity if hasattr(inventory_item.item, 'rarity') else 'common',
        quantity=1,
        duration_hours=hours,
        expires_at=datetime.utcnow() + timedelta(hours=hours),
    )
    db.session.add(listing)
    db.session.flush()
    return listing


def purchase_listing(buyer, listing):
    """Atomically purchase an active listing. Caller commits the session.

    Idempotent against the listing's state: re-purchase of the same listing
    is rejected by the status check at the start.
    """
    if listing.status != 'active':
        raise EconomyError('This listing is no longer available.')
    if listing.is_expired():
        listing.status = 'expired'
        raise EconomyError('This listing has expired.')
    if listing.seller_id == buyer.id:
        raise EconomyError('You cannot buy your own listing.')
    if buyer.coins < listing.price:
        raise EconomyError('Not enough coins.')

    seller = db.session.get(type(buyer), listing.seller_id)

    tax = int(listing.price * LISTING_TAX_RATE)
    net_amount = listing.price - tax

    # Move coins with row locks on both users.
    # The buyer pays the full price; the seller receives the net amount,
    # and the tax is withdrawn from circulation.
    deduct_coins(buyer, listing.price,
                 reason=f'marketplace purchase #{listing.id}')
    seller.coins = (seller.coins or 0) + net_amount
    tax_transfer(tax)

    # Resolve the reserved inventory item and transfer it to the buyer.
    inventory_item = UserInventory.query.filter_by(
        user_id=listing.seller_id, item_id=listing.item_id).first()
    if inventory_item is None or inventory_item.locked_quantity < 1:
        raise EconomyError(
            'The sold item could not be located in inventory. '
            'Please contact support.')
    transfer_inventory(inventory_item, buyer, 1)

    listing.status = 'sold'
    listing.sold_at = datetime.utcnow()
    listing.buyer_id = buyer.id

    db.session.add(MarketplaceTransaction(
        listing_id=listing.id,
        buyer_id=buyer.id,
        seller_id=listing.seller_id,
        price=listing.price,
        tax=tax,
        net_seller_amount=net_amount,
    ))
    current_app.logger.info(
        f'Marketplace purchase: listing={listing.id} buyer={buyer.id} '
        f'price={listing.price}')


def cancel_listing(seller, listing):
    """Cancel a listing and release the reserved inventory."""
    if listing.seller_id != seller.id:
        raise EconomyError('You can only cancel your own listings.')
    if listing.status != 'active':
        raise EconomyError('Listing is not active.')

    inventory_item = UserInventory.query.filter_by(
        user_id=listing.seller_id, item_id=listing.item_id).first()
    if inventory_item is not None and (inventory_item.locked_quantity or 0) >= 1:
        release_inventory(inventory_item, 1)

    listing.status = 'cancelled'


def expire_listing(listing):
    """Mark an expired listing as expired and release its reservation."""
    if listing.status != 'active' or not listing.is_expired():
        return
    inventory_item = UserInventory.query.filter_by(
        user_id=listing.seller_id, item_id=listing.item_id).first()
    if inventory_item is not None and (inventory_item.locked_quantity or 0) >= 1:
        release_inventory(inventory_item, 1)
    listing.status = 'expired'


def expire_listings_job(app):
    """Background job: expire listings whose window has closed (FIX-008)."""
    with app.app_context():
        try:
            expired = MarketplaceListing.query.filter(
                MarketplaceListing.status == 'active',
                MarketplaceListing.expires_at < datetime.utcnow(),
            ).all()
            for listing in expired:
                expire_listing(listing)
            db.session.commit()
            app.logger.info(f'Expired {len(expired)} marketplace listings.')
        except Exception as exc:
            db.session.rollback()
            app.logger.error(f'expire_listings job failed: {exc}')


def active_listings_query(item_type='all', sort_by='newest'):
    """Query for listable (active AND non-expired) listings.

    FIX-024: eager-load the seller relationship — Listing.to_dict() renders
    seller info for every row, so a lazy load would issue N extra queries.
    """
    from sqlalchemy.orm import joinedload
    query = MarketplaceListing.query.options(
        joinedload(MarketplaceListing.seller)).filter(
        MarketplaceListing.status == 'active',
        db.or_(
            MarketplaceListing.expires_at.is_(None),
            MarketplaceListing.expires_at >= datetime.utcnow(),
        ),
    )
    if item_type != 'all':
        query = query.filter_by(item_type=item_type)

    if sort_by == 'price_low':
        query = query.order_by(MarketplaceListing.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(MarketplaceListing.price.desc())
    elif sort_by == 'rarity':
        query = query.order_by(
            db.case(
                (MarketplaceListing.rarity == 'mythic', 1),
                (MarketplaceListing.rarity == 'legendary', 2),
                (MarketplaceListing.rarity == 'epic', 3),
                (MarketplaceListing.rarity == 'rare', 4),
                else_=5
            )
        )
    else:
        query = query.order_by(MarketplaceListing.created_at.desc())
    return query
