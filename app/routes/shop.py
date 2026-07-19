from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.shop import ShopItem, UserInventory

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/shop')
@login_required
def shop():
    items = ShopItem.query.filter_by(is_active=True).all()
    return render_template('shop/index.html', items=items)

@shop_bp.route('/shop/buy/<int:item_id>', methods=['POST'])
@login_required
def buy_item(item_id):
    item = ShopItem.query.get_or_404(item_id)
    if current_user.coins < item.price:
        flash('Not enough coins!', 'error')
        return redirect(url_for('shop.shop'))

    # Хэрэглэгчийн зоос хасах, бүртгэл нэмэх
    current_user.coins -= item.price
    inventory_entry = UserInventory.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if inventory_entry:
        inventory_entry.quantity += 1
    else:
        inventory_entry = UserInventory(user_id=current_user.id, item_id=item_id)
        db.session.add(inventory_entry)

    # Гүйлгээ бүртгэх (заавал биш)
    from app.models.economy import Transaction
    tx = Transaction(user_id=current_user.id, amount=-item.price, type='debit', reason=f'Purchased {item.name}')
    db.session.add(tx)

    db.session.commit()
    flash(f'Successfully purchased {item.name}!', 'success')
    return redirect(url_for('shop.shop'))