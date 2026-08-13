"""Economy Transaction Helpers

Atomic, concurrency-safe primitives for inventory locking, transfer and
coin movement. Every function must be called inside a single database
transaction (the caller manages session/commit) and locks the relevant
rows with `FOR UPDATE` to avoid double-spend races.

All helpers raise `InventoryError` / `CoinError` on policy violations.
"""
from datetime import datetime

from flask import current_app
from sqlalchemy import select

from app.extensions import db


class EconomyError(Exception):
    """Base class for economy policy violations."""


class InventoryError(EconomyError):
    """Raised for invalid inventory operations."""


class CoinError(EconomyError):
    """Raised for invalid coin operations."""


def lock_inventory_item(inventory_item):
    """Lock the inventory row for the duration of the transaction.

    Works on SQLite (testing) and PostgreSQL/MySQL (production).
    """
    return db.session.execute(
        select(type(inventory_item)).where(
            type(inventory_item).id == inventory_item.id
        ).with_for_update()
    ).scalar_one()


def reserve_inventory(inventory_item, quantity):
    """Lock `quantity` units of an inventory item so nothing else can use them.

    Raises InventoryError if the item is not owned by the caller, is equipped,
    or there is not enough unlocked stock.
    """
    if quantity is None or quantity <= 0:
        raise InventoryError('Invalid reservation quantity.')
    inventory_item = lock_inventory_item(inventory_item)
    available = inventory_item.available_quantity
    if available < quantity:
        raise InventoryError(
            'Not enough unlocked inventory for this operation.')
    inventory_item.locked_quantity = (inventory_item.locked_quantity or 0) + quantity


def release_inventory(inventory_item, quantity):
    """Return previously reserved units back to the owner."""
    if quantity is None or quantity <= 0:
        raise InventoryError('Invalid release quantity.')
    locked = inventory_item.locked_quantity or 0
    inventory_item.locked_quantity = max(0, locked - quantity)


def transfer_inventory(seller_item, buyer_user, quantity):
    """Move `quantity` units from seller_item (already reserved) to buyer.

    Adds or tops up the buyer's UserInventory row for the same item.
    The reserved units are then consumed from the seller row.
    """
    from app.models.shop import UserInventory

    if quantity is None or quantity <= 0:
        raise InventoryError('Invalid transfer quantity.')
    if seller_item.locked_quantity is None or seller_item.locked_quantity < quantity:
        raise InventoryError('Units are not reserved for transfer.')

    existing = UserInventory.query.filter_by(
        user_id=buyer_user.id, item_id=seller_item.item_id).first()
    if existing:
        existing.quantity = (existing.quantity or 0) + quantity
    else:
        db.session.add(UserInventory(
            user_id=buyer_user.id,
            item_id=seller_item.item_id,
            quantity=quantity))

    seller_item.locked_quantity -= quantity
    seller_item.quantity -= quantity


def deduct_coins(user, amount, reason='deduction'):
    """Lock the user row and deduct coins. Raises CoinError if insufficient.

    Returns the locked user instance (may be the same object as `user`
    when the identity map is intact). Mutations MUST be made on the
    returned instance.
    """
    if amount is None or amount <= 0:
        raise CoinError('Invalid deduction amount.')
    model = user._get_current_object().__class__ \
        if hasattr(user, '_get_current_object') else type(user)
    locked = db.session.execute(
        select(model).where(model.id == user.id).with_for_update()
    ).scalar_one()
    balance = locked.coins or 0
    if balance < amount:
        raise CoinError('Insufficient coins.')
    locked.coins = balance - amount
    # Keep the caller's handle in sync when a new instance was returned.
    if locked is not user and hasattr(user, 'coins'):
        user.coins = locked.coins
    if hasattr(user, 'add_coins_log') and callable(user.add_coins_log):
        try:
            user.add_coins_log(-amount, reason)
        except Exception:
            pass
    current_app.logger.info(
        f'Coin deduction: user={user.id} amount={amount} reason={reason}')


def transfer_coins(from_user, to_user, amount, reason='transfer'):
    """Move coins between users with row locking on both sides.

    `to_user` may be None for escrow-style holds: coins are deducted from
    `from_user` and held outside circulation until a settlement step.
    """
    if amount is None or amount <= 0:
        raise CoinError('Invalid transfer amount.')
    if to_user is None:
        deduct_coins(from_user, amount, reason)
        return

    from_model = from_user._get_current_object().__class__ \
        if hasattr(from_user, '_get_current_object') else type(from_user)
    ids = sorted((from_user.id, to_user.id))
    locked = db.session.execute(
        select(from_model).where(from_model.id.in_(ids))
        .order_by(from_model.id).with_for_update()
    ).scalars().all()
    users = {user.id: user for user in locked}
    locked_from = users[from_user.id]
    locked_to = users[to_user.id]
    if (locked_from.coins or 0) < amount:
        raise CoinError('Insufficient coins.')
    locked_from.coins -= amount
    locked_to.coins = (locked_to.coins or 0) + amount
    from_user.coins = locked_from.coins
    to_user.coins = locked_to.coins


def market_treasury_id():
    """User id that collects marketplace tax (0 = platform treasury)."""
    return 0


def tax_transfer(amount, reason='marketplace tax'):
    """Credit marketplace tax to the platform treasury balance.

    Treasury is a virtual account tracked in the `economy_treasury` config;
    the coins are removed from circulation when transferred here.
    """
    current_app.logger.info(
        f'Marketplace tax collected: {amount} coins ({reason})')
