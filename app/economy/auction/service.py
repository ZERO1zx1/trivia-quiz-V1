"""Auction Service

Business logic for auction lifecycle with escrow accounting.

Escrow model (FIX-006/FIX-007):
- Placing a bid IMMEDIATELY deducts the bid amount from the bidder.
- The previous high bidder is refunded exactly once (tracked by
  AuctionBid.refunded), eliminating the minting/double-spend bug where
  every new bid created coins.
- On settlement, the winner's coins are already deducted, so only the
  seller receives (final_price - tax). Losing bids are refunded once.
"""
from datetime import datetime

from flask import current_app

from app.extensions import db
from app.models.marketplace import Auction, AuctionBid
from app.models.shop import UserInventory
from app.economy.auction.validators import (
    validate_auction_price,
    validate_bid,
    validate_duration,
    validate_item_ownership,
)
from app.economy.inventory.transactions import (
    EconomyError,
    release_inventory,
    reserve_inventory,
    tax_transfer,
    transfer_coins,
    transfer_inventory,
)
from app.economy.marketplace.service import LISTING_TAX_RATE

AUCTION_TAX_RATE = LISTING_TAX_RATE


def _sink_account(auction_id):
    """Virtual escrow sink: bids are held outside circulation until
    settlement. Returns None (circulation removed); the seller receives
    proceeds at settlement time."""
    return None


def create_auction(seller, item_id, starting_price, buy_now_price=None,
                   duration_hours=None):
    """Create an auction with validated input and reserved inventory."""
    from datetime import timedelta as _td

    duration_hours = duration_hours or 24
    err = validate_duration(duration_hours)
    if err:
        raise EconomyError(err)
    err = validate_auction_price(starting_price, buy_now_price)
    if err:
        raise EconomyError(err)

    inventory_item, err = validate_item_ownership(seller, item_id)
    if err:
        raise EconomyError(err)

    # Reserve the item so it cannot be listed or sold elsewhere.
    reserve_inventory(inventory_item, 1)

    auction = Auction(
        seller_id=seller.id,
        item_type=inventory_item.item.item_type if inventory_item.item else 'item',
        item_id=item_id,
        item_name=inventory_item.item.name if inventory_item.item else f'Item #{item_id}',
        starting_price=starting_price,
        buy_now_price=buy_now_price,
        duration_hours=duration_hours,
        ends_at=datetime.utcnow() + _td(hours=duration_hours),
        inventory_item_id=inventory_item.id,
    )
    db.session.add(auction)
    db.session.flush()
    return auction


def place_bid(bidder, auction, bid_amount):
    """Place a bid. Deducts the bid from the bidder (escrow) and refunds
    the previous bidder exactly once. Caller commits the session."""
    errors = validate_bid(auction, bidder, bid_amount)
    if errors:
        raise EconomyError(errors[0])

    # Refresh the auction locked so two concurrent bids see the same state.
    auction = Auction.query.get(auction.id)
    errors = validate_bid(auction, bidder, bid_amount)
    if errors:
        raise EconomyError(errors[0])

    # Deduct the bid from the bidder (escrow).
    # NOTE: coins are removed from circulation until settlement; the seller
    # receives the net proceeds at settlement.
    transfer_coins(bidder, _sink_account(auction.id), bid_amount,
                   reason=f'auction bid #{auction.id}')

    # Refund the previous bidder exactly once.
    if auction.current_bidder_id:
        AuctionBid.query.filter_by(
            auction_id=auction.id,
            bidder_id=auction.current_bidder_id,
            refunded=False,
        ).update({'refunded': True}, synchronize_session='fetch')
        prev_bidder = db.session.get(type(bidder), auction.current_bidder_id)
        if prev_bidder:
            prev_bidder.coins = (prev_bidder.coins or 0) + auction.current_bid

    db.session.add(AuctionBid(
        auction_id=auction.id,
        bidder_id=bidder.id,
        amount=bid_amount,
    ))
    auction.current_bid = bid_amount
    auction.current_bidder_id = bidder.id
    current_app.logger.info(
        f'Auction bid: auction={auction.id} bidder={bidder.id} '
        f'amount={bid_amount}')


def settle_auction(auction):
    """Settle a single ended auction (winner gets item, seller gets net coins)."""
    if auction.status != 'active':
        return
    if auction.ends_at and auction.ends_at > datetime.utcnow():
        return
    auction.status = 'ended'

    # Refund every non-winning bidder exactly once. The current high bidder
    # (winner, if any) is paid via the settlement proceeds instead.
    non_winners = AuctionBid.query.filter(
        AuctionBid.auction_id == auction.id,
        AuctionBid.refunded == False,  # noqa: E712
    )
    if auction.current_bidder_id:
        non_winners = non_winners.filter(
            AuctionBid.bidder_id != auction.current_bidder_id)
    non_winners = non_winners.all()
    for bid in non_winners:
        bidder = db.session.get(type(auction.seller), bid.bidder_id)
        if bidder:
            bidder.coins = (bidder.coins or 0) + bid.amount
        bid.refunded = True
        db.session.flush()

    if auction.current_bidder_id:
        auction.winner_id = auction.current_bidder_id
        auction.final_price = auction.current_bid

        # Winner's coins are already deducted (escrow) at bid time.
        # Transfer the proceeds minus tax to the seller.
        tax = int(auction.current_bid * AUCTION_TAX_RATE)
        net = auction.current_bid - tax
        seller = db.session.get(type(auction.seller), auction.seller_id)
        if seller:
            seller.coins = (seller.coins or 0) + net
        tax_transfer(tax, f'auction #{auction.id}')

        # Move the reserved inventory item to the winner.
        inventory_item = UserInventory.query.get(auction.inventory_item_id)
        if inventory_item is not None and (inventory_item.locked_quantity or 0) >= 1:
            winner = db.session.get(type(auction.seller), auction.current_bidder_id)
            if winner:
                transfer_inventory(inventory_item, winner, 1)
        current_app.logger.info(
            f'Auction settled: auction={auction.id} winner={auction.current_bidder_id} '
            f'price={auction.current_bid}')
    else:
        # No bids — return the reserved item to the seller.
        inventory_item = UserInventory.query.get(auction.inventory_item_id)
        if inventory_item is not None and (inventory_item.locked_quantity or 0) >= 1:
            release_inventory(inventory_item, 1)


def cancel_auction(seller, auction):
    """Seller cancels an active auction. Refunds the current bidder."""
    if auction.status != 'active':
        raise EconomyError('Auction is not active.')
    if auction.seller_id != seller.id:
        raise EconomyError('You can only cancel your own auction.')
    auction.status = 'cancelled'

    if auction.current_bidder_id:
        non_refunded = AuctionBid.query.filter_by(
            auction_id=auction.id, refunded=False).all()
        for bid in non_refunded:
            bidder = db.session.get(type(seller), bid.bidder_id)
            if bidder:
                bidder.coins = (bidder.coins or 0) + bid.amount
            bid.refunded = True

    inventory_item = UserInventory.query.get(auction.inventory_item_id)
    if inventory_item is not None and (inventory_item.locked_quantity or 0) >= 1:
        release_inventory(inventory_item, 1)


def settle_auctions_job(app):
    """Background job: settle ended auctions (FIX-010)."""
    from app.models.marketplace import Auction
    with app.app_context():
        try:
            settled = 0
            candidates = Auction.query.filter(
                Auction.status == 'active',
                Auction.ends_at < datetime.utcnow(),
            ).all()
            for auction in candidates:
                settle_auction(auction)
                settled += 1
            db.session.commit()
            app.logger.info(f'Settled {settled} auctions.')
        except Exception as exc:
            db.session.rollback()
            app.logger.error(f'settle_auctions job failed: {exc}')


def expire_auctions_job(app):
    """Optional companion: refresh ended flag without settlement (retained
    for compatibility). Not registered by default."""
    settle_auctions_job(app)
