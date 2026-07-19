from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.shop import UserInventory

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
@login_required
def inventory():
    items = current_user.user_inventory_items.all()
    return render_template('inventory/index.html', items=items)

@inventory_bp.route('/inventory/equip/<int:inv_id>', methods=['POST'])
@login_required
def equip_item(inv_id):
    inv = UserInventory.query.get_or_404(inv_id)
    if inv.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('inventory.inventory'))

    # Энгийн equip/unequip toggle (бүгдийг нь unequip хийх)
    if inv.is_equipped:
        inv.is_equipped = False
    else:
        # Ижил төрлийн барааг бүгдийг unequip (хэрэв хүсвэл)
        same_type_items = UserInventory.query.join(ShopItem).filter(
            UserInventory.user_id == current_user.id,
            ShopItem.item_type == inv.item.item_type
        ).all()
        for s in same_type_items:
            s.is_equipped = False
        inv.is_equipped = True

    db.session.commit()
    flash('Equipment updated!', 'success')
    return redirect(url_for('inventory.inventory'))