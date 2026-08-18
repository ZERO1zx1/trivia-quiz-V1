"""Marketplace Routes

All mutating operations are delegated to the economy service layer, which
owns validation, inventory locking, escrow accounting and settlement.
Route URLs and response shapes are preserved for compatibility.
"""
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db, utcnow
from app.models.marketplace import Auction, AuctionBid, MarketplaceListing
from app.models.shop import UserInventory
from app.economy.inventory.transactions import EconomyError
from app.economy.marketplace.service import (
    MAX_LISTING_PRICE,
    active_listings_query,
    cancel_listing,
    create_listing,
    expire_listing,
    purchase_listing,
)
from app.economy.auction.service import (
    cancel_auction,
    create_auction,
    place_bid,
    settle_auction,
)
from app.economy.auction.validators import validate_duration

marketplace_bp = Blueprint('marketplace', __name__, url_prefix='/marketplace')


def _handle_economy_error(exc):
    flash(str(exc), 'danger')


@marketplace_bp.route('/')
def index():
    """Marketplace listing page (only active, non-expired listings)."""
    item_type = request.args.get('type', 'all')
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)

    # On-the-fly expiry check for listings without a scheduler process.
    expired = MarketplaceListing.query.filter(
        MarketplaceListing.status == 'active',
        MarketplaceListing.expires_at < utcnow(),
    ).all()
    for listing in expired:
        expire_listing(listing)
    if expired:
        db.session.commit()

    listings = active_listings_query(item_type, sort_by).paginate(
        page=page, per_page=24, error_out=False)

    return render_template('marketplace/index.html', listings=listings,
                           item_type=item_type, sort_by=sort_by)


@marketplace_bp.route('/list', methods=['POST'])
@login_required
def create_listing_route():
    """Create a marketplace listing"""
    item_id = request.form.get('item_id', type=int)
    price = request.form.get('price', type=int)

    if not item_id or price is None:
        flash('Invalid listing parameters.', 'danger')
        return redirect(url_for('marketplace.index'))

    try:
        create_listing(current_user._get_current_object(), item_id, price)
        db.session.commit()
        flash('Listing created successfully!', 'success')
    except EconomyError as exc:
        db.session.rollback()
        _handle_economy_error(exc)
    return redirect(url_for('marketplace.index'))


@marketplace_bp.route('/<int:listing_id>/buy', methods=['POST'])
@login_required
def buy(listing_id):
    """Buy a marketplace listing"""
    listing = MarketplaceListing.query.get_or_404(listing_id)

    try:
        purchase_listing(current_user._get_current_object(), listing)
        db.session.commit()
        flash(f'Purchased {listing.item_name} for {listing.price} coins!', 'success')
    except EconomyError as exc:
        db.session.rollback()
        _handle_economy_error(exc)

    return redirect(url_for('marketplace.index'))


@marketplace_bp.route('/<int:listing_id>/cancel', methods=['POST'])
@login_required
def cancel(listing_id):
    """Cancel a marketplace listing"""
    listing = MarketplaceListing.query.get_or_404(listing_id)

    try:
        cancel_listing(current_user._get_current_object(), listing)
        db.session.commit()
        flash('Listing cancelled.', 'info')
    except EconomyError as exc:
        db.session.rollback()
        _handle_economy_error(exc)

    return redirect(url_for('marketplace.index'))


@marketplace_bp.route('/my-listings')
@login_required
def my_listings():
    """View user's own listings"""
    listings = MarketplaceListing.query.filter_by(
        seller_id=current_user.id
    ).order_by(MarketplaceListing.created_at.desc()).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=20, error_out=False
    )
    return render_template('marketplace/my_listings.html', listings=listings)


# Auction endpoints
@marketplace_bp.route('/auction/create', methods=['POST'])
@login_required
def create_auction_route():
    """Create an auction"""
    item_id = request.form.get('item_id', type=int)
    starting_price = request.form.get('starting_price', type=int)
    buy_now_price = request.form.get('buy_now_price', type=int)
    duration = request.form.get('duration', 24, type=int)

    if not item_id:
        flash('Invalid auction parameters.', 'danger')
        return redirect(url_for('marketplace.index'))

    try:
        create_auction(current_user._get_current_object(), item_id,
                       starting_price, buy_now_price, duration)
        db.session.commit()
        flash('Auction created!', 'success')
    except EconomyError as exc:
        db.session.rollback()
        _handle_economy_error(exc)
    return redirect(url_for('marketplace.index'))


@marketplace_bp.route('/auction/<int:auction_id>/bid', methods=['POST'])
@login_required
def place_bid_route(auction_id):
    """Place a bid on an auction"""
    auction = Auction.query.get_or_404(auction_id)
    bid_amount = request.form.get('amount', type=int)

    if bid_amount is None:
        flash('Invalid bid amount.', 'danger')
        return redirect(url_for('marketplace.index'))

    try:
        place_bid(current_user._get_current_object(), auction, bid_amount)
        db.session.commit()
        flash(f'Bid of {bid_amount} coins placed!', 'success')
    except EconomyError as exc:
        db.session.rollback()
        _handle_economy_error(exc)

    return redirect(url_for('marketplace.index'))


@marketplace_bp.route('/auction/<int:auction_id>/cancel', methods=['POST'])
@login_required
def cancel_auction_route(auction_id):
    """Cancel an active auction (seller only)."""
    auction = Auction.query.get_or_404(auction_id)

    try:
        cancel_auction(current_user._get_current_object(), auction)
        db.session.commit()
        flash('Auction cancelled.', 'info')
    except EconomyError as exc:
        db.session.rollback()
        _handle_economy_error(exc)

    return redirect(url_for('marketplace.index'))


# API endpoints
@marketplace_bp.route('/api/listings')
def api_listings():
    """API: List marketplace items"""
    page = request.args.get('page', 1, type=int)
    item_type = request.args.get('type', 'all')

    listings = active_listings_query(item_type).order_by(
        MarketplaceListing.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return jsonify({
        'listings': [l.to_dict() for l in listings.items],
        'total': listings.total,
        'pages': listings.pages
    })


@marketplace_bp.route('/api/auctions')
def api_auctions():
    """API: List active auctions"""
    # FIX-024: use a SQL COUNT() instead of len(a.bids), which would load
    # every bid row for every auction (N+1 and unbounded memory growth).
    bid_counts = db.session.query(
        AuctionBid.auction_id, db.func.count(AuctionBid.id)
    ).filter(
        AuctionBid.auction_id.in_(
            db.session.query(Auction.id).filter_by(status='active'))
    ).group_by(AuctionBid.auction_id).all()
    bid_map = dict(bid_counts)
    auctions = Auction.query.filter_by(status='active').order_by(
        Auction.ends_at
    ).limit(50).all()
    return jsonify({
        'auctions': [
            {
                'id': a.id,
                'item_name': a.item_name,
                'starting_price': a.starting_price,
                'current_bid': a.current_bid,
                'buy_now_price': a.buy_now_price,
                'ends_at': a.ends_at.isoformat() if a.ends_at else None,
                'bid_count': bid_map.get(a.id, 0)
            }
            for a in auctions
        ]
    })
