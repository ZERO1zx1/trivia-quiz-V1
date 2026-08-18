"""Crafting System Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db, utcnow
from app.models.craft import CraftRecipe, CraftingMaterial, UserCraftingProgress
from datetime import datetime

craft_bp = Blueprint('craft', __name__, url_prefix='/craft')


@craft_bp.route('/')
def index():
    """Crafting workshop page"""
    recipes = CraftRecipe.query.filter_by(is_active=True).all()
    materials = CraftingMaterial.query.filter_by(is_active=True).all()

    # Get user's active crafting
    active_crafts = None
    if current_user.is_authenticated:
        active_crafts = UserCraftingProgress.query.filter_by(
            user_id=current_user.id, status='in_progress'
        ).all()

    return render_template('craft/index.html', recipes=recipes,
                           materials=materials, active_crafts=active_crafts)


@craft_bp.route('/<int:recipe_id>/start', methods=['POST'])
@login_required
def start_crafting(recipe_id):
    """Start a crafting session"""
    recipe = CraftRecipe.query.get_or_404(recipe_id)

    if not recipe.is_active:
        flash('This recipe is no longer available.', 'warning')
        return redirect(url_for('craft.index'))

    # Check coins
    if current_user.coins < recipe.coins_required:
        flash('Not enough coins.', 'danger')
        return redirect(url_for('craft.index'))

    # Create crafting progress
    progress = UserCraftingProgress(
        user_id=current_user.id,
        recipe_id=recipe.id,
        status='in_progress'
    )
    current_user.coins -= recipe.coins_required
    db.session.add(progress)
    db.session.commit()

    flash(f'Started crafting {recipe.name}!', 'info')
    return redirect(url_for('craft.index'))


@craft_bp.route('/<int:progress_id>/complete', methods=['POST'])
@login_required
def complete_crafting(progress_id):
    """Complete a crafting session"""
    progress = UserCraftingProgress.query.get_or_404(progress_id)

    if progress.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    if progress.status != 'in_progress':
        return jsonify({'error': 'Already processed'}), 400

    recipe = progress.recipe
    import random
    success = random.random() * 100 <= recipe.success_rate

    if success:
        progress.status = 'completed'
        progress.completed_at = utcnow()
        progress.result_item_id = recipe.output_item_id
        flash(f'Successfully crafted {recipe.name}!', 'success')
    else:
        progress.status = 'failed'
        progress.completed_at = utcnow()
        flash('Crafting failed!', 'danger')

    db.session.commit()
    return redirect(url_for('craft.index'))


@craft_bp.route('/recipes')
def recipes():
    """View all crafting recipes"""
    category = request.args.get('category', 'all')
    query = CraftRecipe.query.filter_by(is_active=True)
    if category != 'all':
        query = query.filter_by(recipe_type=category)

    recipes = query.order_by(CraftRecipe.rarity).all()
    return jsonify({
        'recipes': [r.to_dict() for r in recipes]
    })


@craft_bp.route('/materials')
def materials():
    """View all crafting materials"""
    materials = CraftingMaterial.query.filter_by(is_active=True).all()
    return jsonify({
        'materials': [
            {'id': m.id, 'name': m.name, 'rarity': m.rarity, 'source': m.source}
            for m in materials
        ]
    })
