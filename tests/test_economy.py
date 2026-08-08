"""Economy regression tests (marketplace + auction escrow).

Covers FIX-005..FIX-010, FIX-022: inventory reservation, purchase atomicity,
bid escrow/refund accounting, auction settlement, and listing expiry.
"""
from datetime import timedelta

import pytest
from flask_login import login_user

from app.extensions import db
from app.models.marketplace import Auction, AuctionBid, MarketplaceListing
from app.models.shop import ShopItem, UserInventory
from app.models.user import User
from app.economy.inventory.transactions import (
    CoinError, EconomyError, InventoryError, reserve_inventory,
    release_inventory, transfer_coins, transfer_inventory,
)
from app.economy.marketplace.service import (
    cancel_listing, create_listing, expire_listing, purchase_listing,
)
from app.economy.auction.service import (
    cancel_auction, create_auction, place_bid, settle_auction,
    settle_auctions_job,
)


def _shop_item(name='Test Item', price=100):
    item = ShopItem(name=name, price=price, base_price=price,
                    item_type='badge', is_active=True)
    db.session.add(item)
    db.session.flush()
    return item


def _inv(user, item, quantity=1, equipped=False):
    entry = UserInventory(user_id=user.id, item_id=item.id,
                          quantity=quantity, is_equipped=equipped)
    db.session.add(entry)
    db.session.flush()
    return entry


class TestInventoryReservation:
    def test_reserve_and_release(self, user, db):
        item = _shop_item()
        inv = _inv(user, item, quantity=2)
        reserve_inventory(inv, 1)
        assert inv.available_quantity == 1
        assert inv.locked_quantity == 1
        release_inventory(inv, 1)
        assert inv.available_quantity == 2
        assert inv.locked_quantity == 0

    def test_reserve_more_than_available_fails(self, user, db):
        item = _shop_item()
        inv = _inv(user, item, quantity=1)
        with pytest.raises(InventoryError):
            reserve_inventory(inv, 2)

    def test_cannot_use_locked_inventory(self, user, db):
        item = _shop_item()
        inv = _inv(user, item, quantity=1)
        reserve_inventory(inv, 1)
        with pytest.raises(InventoryError):
            create_listing(user, item.id, 100)


class TestMarketplaceListing:
    def test_create_listing_reserves_inventory(self, seller, db):
        item = _shop_item()
        inv = _inv(seller, item)
        listing = create_listing(seller, item.id, 500)
        db.session.commit()
        assert inv.locked_quantity == 1
        assert inv.available_quantity == 0
        assert listing.status == 'active'
        assert listing.price == 500

    def test_create_listing_non_owner_fails(self, seller, user, db):
        item = _shop_item()
        _inv(seller, item)
        with pytest.raises(EconomyError, match='do not own'):
            create_listing(user, item.id, 500)

    def test_create_listing_equipped_fails(self, seller, db):
        item = _shop_item()
        _inv(seller, item, equipped=True)
        with pytest.raises(EconomyError, match='equipped'):
            create_listing(seller, item.id, 500)

    def test_price_limits(self, seller, db):
        item = _shop_item()
        _inv(seller, item)
        with pytest.raises(EconomyError, match='positive'):
            create_listing(seller, item.id, 0)
        with pytest.raises(EconomyError, match='1,000,000'):
            create_listing(seller, item.id, 1_000_001)

    def test_cancel_releases_inventory(self, seller, db):
        item = _shop_item()
        inv = _inv(seller, item)
        listing = create_listing(seller, item.id, 500)
        db.session.commit()
        cancel_listing(seller, listing)
        db.session.commit()
        assert inv.locked_quantity == 0
        assert listing.status == 'cancelled'

    def test_purchase_transfers_coins_and_item(self, seller, buyer, db):
        item = _shop_item()
        _inv(seller, item)
        listing = create_listing(seller, item.id, 1000)
        db.session.commit()
        seller_start = seller.coins
        buyer_start = buyer.coins

        purchase_listing(buyer, listing)
        db.session.commit()

        # 5% tax: seller nets 950, buyer pays 1000
        assert seller.coins == seller_start + 950
        assert buyer.coins == buyer_start - 1000
        assert listing.status == 'sold'
        assert listing.buyer_id == buyer.id

        buyer_inv = UserInventory.query.filter_by(
            user_id=buyer.id, item_id=item.id).first()
        assert buyer_inv is not None and buyer_inv.quantity == 1

    def test_purchase_insufficient_coins_fails(self, seller, buyer, db):
        buyer.coins = 5
        item = _shop_item()
        _inv(seller, item)
        listing = create_listing(seller, item.id, 1000)
        db.session.commit()
        with pytest.raises(EconomyError, match='Not enough coins'):
            purchase_listing(buyer, listing)

    def test_purchase_sold_listing_rejected(self, seller, buyer, db):
        item = _shop_item()
        _inv(seller, item)
        listing = create_listing(seller, item.id, 500)
        db.session.commit()
        purchase_listing(buyer, listing)
        db.session.commit()
        with pytest.raises(EconomyError, match='no longer available'):
            purchase_listing(buyer, listing)

    def test_purchase_expired_listing_fails_and_marks_expired(self, seller, buyer, db):
        item = _shop_item()
        _inv(seller, item)
        listing = create_listing(seller, item.id, 500)
        listing.expires_at = __import__('datetime').datetime.utcnow() - timedelta(hours=1)
        db.session.commit()
        buyer_start = buyer.coins
        with pytest.raises(EconomyError, match='expired'):
            purchase_listing(buyer, listing)
        assert listing.status == 'expired'
        assert buyer.coins == buyer_start

    def test_expired_listing_releases_inventory(self, seller, db):
        item = _shop_item()
        inv = _inv(seller, item)
        listing = create_listing(seller, item.id, 500)
        listing.expires_at = __import__('datetime').datetime.utcnow() - timedelta(hours=1)
        db.session.commit()
        expire_listing(listing)
        assert inv.locked_quantity == 0
        assert listing.status == 'expired'

    def test_active_listings_excludes_expired(self, seller, db):
        from app.economy.marketplace.service import active_listings_query
        item = _shop_item()
        _inv(seller, item)
        listing = create_listing(seller, item.id, 500)
        listing.expires_at = __import__('datetime').datetime.utcnow() - timedelta(hours=1)
        db.session.commit()
        assert active_listings_query().count() == 0

    def test_self_purchase_rejected(self, seller, db):
        item = _shop_item()
        _inv(seller, item)
        listing = create_listing(seller, item.id, 500)
        db.session.commit()
        with pytest.raises(EconomyError, match='own listing'):
            purchase_listing(seller, listing)


class TestAuctionEscrow:
    def test_create_auction_reserves_and_validates(self, seller, db):
        item = _shop_item()
        inv = _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        db.session.commit()
        assert inv.locked_quantity == 1
        assert auction.inventory_item_id == inv.id
        assert auction.status == 'active'

    def test_bid_escrow_deducts_immediately(self, seller, buyer, db):
        item = _shop_item()
        _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        db.session.commit()
        start = buyer.coins
        place_bid(buyer, auction, 200)
        db.session.commit()
        assert buyer.coins == start - 200
        assert auction.current_bid == 200
        assert auction.current_bidder_id == buyer.id

    def test_outbid_refunds_previous_bidder_exactly_once(self, seller, buyer, user, db):
        item = _shop_item()
        _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        db.session.commit()
        place_bid(buyer, auction, 200)
        db.session.commit()
        buyer_after_first = buyer.coins
        place_bid(user, auction, 300)
        db.session.commit()
        assert buyer.coins == buyer_after_first + 200
        bid = AuctionBid.query.filter_by(auction_id=auction.id,
                                         bidder_id=buyer.id).first()
        assert bid.refunded is True

    def test_duplicate_bidder_rejected(self, seller, buyer, db):
        item = _shop_item()
        _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        db.session.commit()
        place_bid(buyer, auction, 200)
        db.session.commit()
        with pytest.raises(EconomyError, match='higher than the current bid'):
            place_bid(buyer, auction, 150)

    def test_bid_under_floor_rejected(self, seller, buyer, db):
        item = _shop_item()
        _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        db.session.commit()
        with pytest.raises(EconomyError, match='higher than the current bid'):
            place_bid(buyer, auction, 50)

    def test_insufficient_coins_bid_rejected(self, seller, buyer, db):
        buyer.coins = 10
        item = _shop_item()
        _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        db.session.commit()
        with pytest.raises(EconomyError, match='Not enough coins'):
            place_bid(buyer, auction, 200)

    def test_settle_winner_gets_item_and_seller_gets_net(self, seller, buyer, db):
        item = _shop_item()
        _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        auction.ends_at = __import__('datetime').datetime.utcnow() - timedelta(hours=1)
        db.session.commit()
        place_bid(buyer, auction, 500)
        db.session.commit()
        buyer_start = buyer.coins  # 500 after the 500-coin escrow deduction
        seller_start = seller.coins

        settle_auction(auction)
        db.session.commit()

        # Winner paid 500 at bid time (escrow, already deducted); the seller
        # receives 475 after the 5% platform tax.
        buyer_now = User.query.get(buyer.id)
        seller_now = User.query.get(seller.id)
        assert buyer_now.coins == buyer_start  # unchanged after settlement (escrow)
        assert seller_now.coins == seller_start + 475
        assert auction.status == 'ended'
        assert auction.winner_id == buyer.id
        assert auction.final_price == 500

        winner_inv = UserInventory.query.filter_by(
            user_id=buyer.id, item_id=item.id).first()
        assert winner_inv is not None

    def test_settle_no_bids_returns_item(self, seller, db):
        item = _shop_item()
        inv = _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        auction.ends_at = __import__('datetime').datetime.utcnow() - timedelta(hours=1)
        db.session.commit()
        settle_auction(auction)
        db.session.commit()
        assert inv.locked_quantity == 0
        assert auction.status == 'ended'
        assert auction.winner_id is None

    def test_settle_refunds_losing_bids_once(self, seller, buyer, user, db):
        item = _shop_item()
        _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        auction.ends_at = __import__('datetime').datetime.utcnow() - timedelta(hours=1)
        db.session.commit()
        place_bid(buyer, auction, 200)
        db.session.commit()
        buyer_before = buyer.coins  # 800 after the 200-coin escrow deduction
        place_bid(user, auction, 300)
        db.session.commit()
        user_start = user.coins  # 700 after the 300-coin escrow deduction

        settle_auction(auction)
        db.session.commit()

        # Losing bidder is refunded exactly once; winner keeps the escrow
        # deduction (their bid payment).
        # NOTE: re-read from the database to avoid stale session caches.
        buyer_now = User.query.get(buyer.id)
        user_now = User.query.get(user.id)
        seller_now = User.query.get(seller.id)
        assert buyer_now.coins == buyer_before + 200
        assert user_now.coins == user_start  # unchanged after settlement (escrow)

    def test_job_settles_ended_auctions(self, app, db):
        from app.models.user import User as _U

        def _make_user(username, email, coins=1000):
            u = _U(username=username, email=email, display_name=username,
                   coins=coins)
            u.set_password('Tr1v!aVerse99')
            u.is_verified = True
            db.session.add(u)
            db.session.flush()
            return u

        with app.app_context():
            seller = _make_user('job_seller', 'js@example.com')
            buyer = _make_user('job_buyer', 'jb@example.com')
            item = _shop_item()
            _inv(seller, item)
            auction = create_auction(seller, item.id, 100, duration_hours=24)
            auction.ends_at = __import__('datetime').datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            place_bid(buyer, auction, 500)
            db.session.commit()

            settle_auctions_job(app)

            db.session.expire_all()
            a = db.session.get(Auction, auction.id)
            assert a.status == 'ended'
            assert a.winner_id == buyer.id
            assert a.final_price == 500

    def test_cancel_auction_refunds_bidder(self, seller, buyer, db):
        item = _shop_item()
        _inv(seller, item)
        auction = create_auction(seller, item.id, 100, duration_hours=24)
        db.session.commit()
        place_bid(buyer, auction, 200)
        db.session.commit()
        buyer_before = buyer.coins
        cancel_auction(seller, auction)
        db.session.commit()
        assert buyer.coins == buyer_before + 200
        assert auction.status == 'cancelled'

    def test_invalid_duration_rejected(self, seller, db):
        item = _shop_item()
        _inv(seller, item)
        with pytest.raises(EconomyError, match='Duration'):
            create_auction(seller, item.id, 100, duration_hours=1000)

    def test_invalid_price_rejected(self, seller, db):
        item = _shop_item()
        _inv(seller, item)
        with pytest.raises(EconomyError, match='Starting price'):
            create_auction(seller, item.id, 0)
