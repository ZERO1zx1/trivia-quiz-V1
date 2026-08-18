"""Auction Validators"""
from datetime import datetime, timezone

from app.models.shop import UserInventory

MIN_AUCTION_DURATION_HOURS = 1
MAX_AUCTION_DURATION_HOURS = 168   # 7 days
MIN_STARTING_PRICE = 1
MAX_BUY_NOW_MULTIPLIER = 10        # buy_now may not exceed 10x starting price


def validate_bid(auction, bidder, bid_amount):
    """Return list of error strings (empty = valid)."""
    errors = []
    if auction is None:
        return ['Auction not found.']
    if auction.status != 'active':
        return ['This auction has ended.']
    if auction.ends_at:
        ends_at = auction.ends_at
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        if ends_at <= datetime.now(timezone.utc):
            return ['This auction has ended.']
    if auction.seller_id == bidder.id:
        return ['You cannot bid on your own auction.']
    if bid_amount is None or bid_amount <= 0:
        errors.append('Invalid bid amount.')
    else:
        current_floor = auction.current_bid or auction.starting_price
        if bid_amount <= current_floor:
            errors.append(
                f'Bid must be higher than the current bid ({current_floor} coins).')
        if bidder.coins < bid_amount:
            errors.append('Not enough coins to cover this bid.')
    return errors


def validate_duration(duration_hours):
    if duration_hours is None:
        return 'Duration is required.'
    if not (MIN_AUCTION_DURATION_HOURS <= duration_hours <= MAX_AUCTION_DURATION_HOURS):
        return (f'Duration must be between {MIN_AUCTION_DURATION_HOURS} and '
                f'{MAX_AUCTION_DURATION_HOURS} hours.')
    return None


def validate_item_ownership(owner, item_id):
    """Return (UserInventory item or None, error string or None)."""
    inventory_item = UserInventory.query.filter_by(
        user_id=owner.id, item_id=item_id).first()
    if inventory_item is None:
        return None, 'You do not own this item.'
    if inventory_item.is_equipped:
        return None, 'Cannot auction equipped items.'
    if inventory_item.available_quantity < 1:
        return None, 'This item is already reserved or listed.'
    return inventory_item, None


def validate_auction_price(starting_price, buy_now_price):
    if starting_price is None or starting_price < MIN_STARTING_PRICE:
        return f'Starting price must be at least {MIN_STARTING_PRICE} coins.'
    if buy_now_price and buy_now_price < starting_price:
        return 'Buy-now price must be at least the starting price.'
    if buy_now_price and buy_now_price > starting_price * MAX_BUY_NOW_MULTIPLIER:
        return ('Buy-now price is too high relative to the starting price.')
    return None
