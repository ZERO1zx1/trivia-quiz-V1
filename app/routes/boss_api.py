from flask import Blueprint, jsonify, request
from app.extensions import db, utcnow
from app.models.boss import Boss
from app.utils.decorators import discord_api_required
from datetime import datetime

boss_api_bp = Blueprint('boss_api', __name__)

@boss_api_bp.route('/spawn', methods=['POST'])
@discord_api_required
def spawn_boss():
    data = request.get_json(silent=True) or {}
    hp = data.get('hp', 100000)
    if not isinstance(hp, int) or hp <= 0:
        return jsonify({'error': 'hp must be a positive integer'}), 400
    boss = Boss(name=data.get('name', 'World Boss'), max_hp=hp,
                current_hp=hp)
    db.session.add(boss)
    db.session.commit()
    return jsonify({'id': boss.id, 'name': boss.name, 'max_hp': boss.max_hp, 'status': boss.status}), 201

@boss_api_bp.route('/damage', methods=['POST'])
@discord_api_required
def deal_damage():
    data = request.get_json(silent=True) or {}
    boss_id = data.get('boss_id')
    damage = data.get('damage')
    if not isinstance(boss_id, int) or not isinstance(damage, int) \
            or damage <= 0:
        return jsonify({'error': 'boss_id and positive damage are required'}), 400
    boss = db.session.get(Boss, boss_id)
    if not boss or boss.status != 'active':
        return jsonify({'error': 'Boss not active'}), 404

    boss.current_hp -= damage
    if boss.current_hp <= 0:
        boss.current_hp = 0
        boss.status = 'defeated'
        boss.end_time = utcnow()
        # TODO: Топ 3-т шагнал олгох логик
    db.session.commit()
    return jsonify({'current_hp': boss.current_hp, 'defeated': boss.status == 'defeated'})
