"""Marketplace Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.marketplace import MarketplaceListing, MarketplaceTransaction, Auction, AuctionBid
from app.models.shop import UserInventory
from datetime import datetime, timedelta

marketplace_bp = Blueprint('marketplace', __name__, url_prefix='/marketplace')


@marketplace_bp.route('/')
def index():
    """Marketplace listing page"""
    item_type = request.args.get('type', 'all')
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)

    query = MarketplaceListing.query.filter_by(status='active')
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

    listings = query.paginate(page=page, per_page=24, error_out=False)

    return render_template('marketplace/index.html', listings=listings,
                           item_type=item_type, sort_by=sort_by)


@marketplace_bp.route('/list', methods=['POST'])
@login_required
def create_listing():
    """Create a marketplace listing"""
    item_id = request.form.get('item_id', type=int)
    price = request.form.get('price', type=int)

    if not item_id or not price or price <= 0:
        flash('Invalid listing parameters.', 'danger')
        return redirect(url_for('marketplace.index'))

    if price > 1000000:
        flash('Maximum listing price is 1,000,000 coins.', 'danger')
        return redirect(url_for('marketplace.index'))

    # Check if user owns the item
    inventory_item = UserInventory.query.filter_by(
        user_id=current_user.id, item_id=item_id
    ).first()

    if not inventory_item:
        flash('You do not own this item.', 'danger')
        return redirect(url_for('marketplace.index'))

    if inventory_item.is_equipped:
        flash('Cannot list equipped items.', 'warning')
        return redirect(url_for('marketplace.index'))

    listing = MarketplaceListing(
        seller_id=current_user.id,
        item_type=inventory_item.item.item_type if inventory_item.item else 'other',
        item_id=item_id,
        item_name=inventory_item.item.name if inventory_item.item else 'Unknown',
        item_image=inventory_item.item.image_url if inventory_item.item else '',
        price=price,
        rarity=inventory_item.item.rarity if hasattr(inventory_item.item, 'rarity') else 'common',
        quantity=inventory_item.quantity,
        expires_at=datetime.utcnow() + timedelta(hours=72)
    )

    db.session.add(listing)
    db.session.commit()

    flash('Listing created successfully!', 'success')
    return redirect(url_for('marketplace.index'))


@marketplace_bp.route('/<int:listing_id>/buy', methods=['POST'])
@login_required
def buy(listing_id):
    """Buy a marketplace listing"""
    listing = MarketplaceListing.query.get_or_404(listing_id)

    if listing.status != 'active':
        flash('This listing is no longer available.', 'warning')
        return redirect(url_for('marketplace.index'))

    if listing.seller_id == current_user.id:
        flash('You cannot buy your own listing.', 'warning')
        return redirect(url_for('marketplace.index'))

    if current_user.coins < listing.price:
        flash('Not enough coins.', 'danger')
        return redirect(url_for('marketplace.index'))

    # Transaction
    tax = int(listing.price * 0.05)  # 5% marketplace tax
    net_amount = listing.price - tax

    current_user.coins -= listing.price
    seller = listing.seller
    seller.coins += net_amount

    listing.status = 'sold'
    listing.sold_at = datetime.utcnow()
    listing.buyer_id = current_user.id

    transaction = MarketplaceTransaction(
        listing_id=listing.id,
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
        price=listing.price,
        tax=tax,
        net_seller_amount=net_amount
    )
    db.session.add(transaction)
    db.session.commit()

    flash(f'Purchased {listing.item_name} for {listing.price} coins!', 'success')
    return redirect(url_for('marketplace.index'))


@marketplace_bp.route('/<int:listing_id>/cancel', methods=['POST'])
@login_required
def cancel(listing_id):
    """Cancel a marketplace listing"""
    listing = MarketplaceListing.query.get_or_404(listing_id)

    if listing.seller_id != current_user.id:
        flash('You can only cancel your own listings.', 'danger')
        return redirect(url_for('marketplace.index'))

    listing.status = 'cancelled'
    db.session.commit()

    flash('Listing cancelled.', 'info')
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
def create_auction():
    """Create an auction"""
    item_id = request.form.get('item_id', type=int)
    starting_price = request.form.get('starting_price', type=int)
    buy_now_price = request.form.get('buy_now_price', type=int)
    duration = request.form.get('duration', 24, type=int)

    auction = Auction(
        seller_id=current_user.id,
        item_type='item',
        item_id=item_id,
        item_name=f'Item #{item_id}',
        starting_price=starting_price,
        buy_now_price=buy_now_price if buy_now_price else None,
        duration_hours=duration,
        ends_at=datetime.utcnow() + timedelta(hours=duration)
    )
    db.session.add(auction)
    db.session.commit()

    flash('Auction created!', 'success')
    return redirect(url_for('marketplace.index'))


@marketplace_bp.route('/auction/<int:auction_id>/bid', methods=['POST'])
@login_required
def place_bid(auction_id):
    """Place a bid on an auction"""
    auction = Auction.query.get_or_404(auction_id)

    if auction.status != 'active':
        flash('This auction has ended.', 'warning')
        return redirect(url_for('marketplace.index'))

    if auction.seller_id == current_user.id:
        flash('You cannot bid on your own auction.', 'warning')
        return redirect(url_for('marketplace.index'))

    bid_amount = request.form.get('amount', type=int)
    min_bid = (auction.current_bid or auction.starting_price) + 10

    if bid_amount < min_bid:
        flash(f'Minimum bid is {min_bid} coins.', 'danger')
        return redirect(url_for('marketplace.index'))

    if current_user.coins < bid_amount:
        flash('Not enough coins.', 'danger')
        return redirect(url_for('marketplace.index'))

    # Refund previous bidder
    if auction.current_bidder_id:
        prev_bidder = User.query.get(auction.current_bidder_id)
        if prev_bidder:
            prev_bidder.coins += auction.current_bid

    bid = AuctionBid(
        auction_id=auction.id,
        bidder_id=current_user.id,
        amount=bid_amount
    )
    auction.current_bid = bid_amount
    auction.current_bidder_id = current_user.id
    db.session.add(bid)
    db.session.commit()

    flash(f'Bid of {bid_amount} coins placed!', 'success')
    return redirect(url_for('marketplace.index'))


# API endpoints
@marketplace_bp.route('/api/listings')
def api_listings():
    """API: List marketplace items"""
    page = request.args.get('page', 1, type=int)
    item_type = request.args.get('type', 'all')

    query = MarketplaceListing.query.filter_by(status='active')
    if item_type != 'all':
        query = query.filter_by(item_type=item_type)

    listings = query.order_by(MarketplaceListing.created_at.desc()).paginate(
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
                'bid_count': len(a.bids)
            }
            for a in auctions
        ]
    })
