"""Pet System Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.pet import PetSpecies, Pet, PetEvolution, PetEquipment

pet_bp = Blueprint('pet', __name__, url_prefix='/pet')


@pet_bp.route('/')
def index():
    """Pet collection page"""
    if current_user.is_authenticated:
        pets = Pet.query.filter_by(user_id=current_user.id).all()
        active_pet = Pet.query.filter_by(user_id=current_user.id, is_active=True).first()
    else:
        pets = []
        active_pet = None

    species = PetSpecies.query.filter_by(is_active=True).all()

    return render_template('pet/index.html', pets=pets, active_pet=active_pet, species=species)


@pet_bp.route('/<int:pet_id>')
def detail(pet_id):
    """Pet detail page"""
    pet = Pet.query.get_or_404(pet_id)

    if current_user.is_authenticated and pet.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    evolution_log = pet.evolution_log.order_by(PetEvolution.evolved_at).all()

    return render_template('pet/detail.html', pet=pet, evolution_log=evolution_log)


@pet_bp.route('/<int:pet_id>/rename', methods=['POST'])
@login_required
def rename(pet_id):
    """Rename a pet"""
    pet = Pet.query.get_or_404(pet_id)

    if pet.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    new_name = request.form.get('name', '').strip()
    if not new_name or len(new_name) > 50:
        flash('Name must be 1-50 characters.', 'danger')
        return redirect(url_for('pet.detail', pet_id=pet_id))

    pet.name = new_name
    db.session.commit()

    flash('Pet renamed!', 'success')
    return redirect(url_for('pet.detail', pet_id=pet_id))


@pet_bp.route('/<int:pet_id>/equip', methods=['POST'])
@login_required
def equip(pet_id):
    """Equip a pet"""
    pet = Pet.query.get_or_404(pet_id)

    if pet.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    # Unequip current pet
    Pet.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})

    pet.is_active = True
    db.session.commit()

    flash(f'{pet.name or pet.species.name} equipped!', 'success')
    return redirect(url_for('pet.index'))


@pet_bp.route('/<int:pet_id>/feed', methods=['POST'])
@login_required
def feed(pet_id):
    """Feed a pet to increase happiness"""
    pet = Pet.query.get_or_404(pet_id)

    if pet.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    pet.happiness = min(100, pet.happiness + 10)
    pet.energy = min(100, pet.energy + 20)
    pet.xp += 5
    pet.last_interacted = db.func.now()

    # Check for level up
    xp_needed = pet.level * 100
    if pet.xp >= xp_needed:
        pet.level += 1
        pet.xp -= xp_needed

    db.session.commit()

    return jsonify({'success': True, 'happiness': pet.happiness, 'level': pet.level, 'xp': pet.xp})


@pet_bp.route('/<int:pet_id>/evolve', methods=['POST'])
@login_required
def evolve(pet_id):
    """Evolve a pet"""
    pet = Pet.query.get_or_404(pet_id)

    if pet.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    new_species = pet.species
    if not new_species.evolves_to:
        flash('This pet cannot evolve.', 'warning')
        return redirect(url_for('pet.detail', pet_id=pet_id))

    if pet.level < (new_species.evolution_level or 999):
        flash(f'Reach level {new_species.evolution_level} to evolve.', 'warning')
        return redirect(url_for('pet.detail', pet_id=pet_id))

    new_species_id = new_species.evolves_to

    evolution = PetEvolution(
        pet_id=pet.id,
        from_species_id=pet.species_id,
        to_species_id=new_species_id,
        level_at_evolution=pet.level
    )

    pet.species_id = new_species_id
    pet.level = 1
    pet.xp = 0

    db.session.add(evolution)
    db.session.commit()

    flash(f'Your pet evolved to {pet.species.name}!', 'success')
    return redirect(url_for('pet.detail', pet_id=pet_id))


@pet_bp.route('/equipment')
def equipment():
    """Pet equipment shop"""
    items = PetEquipment.query.filter_by(is_active=True).all()
    return render_template('pet/equipment.html', items=items)


# API endpoints
@pet_bp.route('/api/species')
def api_species():
    """API: List pet species"""
    species = PetSpecies.query.filter_by(is_active=True).all()
    return jsonify({'species': [s.to_dict() for s in species]})


@pet_bp.route('/api/<int:pet_id>/stats')
@login_required
def api_stats(pet_id):
    """API: Pet stats"""
    pet = Pet.query.get_or_404(pet_id)
    if pet.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    return jsonify(pet.to_dict())
