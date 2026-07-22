from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.boss import Boss
from datetime import datetime

boss_api_bp = Blueprint('boss_api', __name__)

@boss_api_bp.route('/spawn', methods=['POST'])
def spawn_boss():
    data = request.json
    boss = Boss(name=data.get('name', 'World Boss'), max_hp=data.get('hp', 100000), current_hp=data.get('hp', 100000))
    db.session.add(boss)
    db.session.commit()
    return jsonify({'id': boss.id, 'name': boss.name, 'max_hp': boss.max_hp, 'status': boss.status}), 201

@boss_api_bp.route('/damage', methods=['POST'])
def deal_damage():
    data = request.json
    boss = Boss.query.get(data['boss_id'])
    if not boss or boss.status != 'active':
        return jsonify({'error': 'Boss not active'}), 404

    boss.current_hp -= data['damage']
    if boss.current_hp <= 0:
        boss.current_hp = 0
        boss.status = 'defeated'
        boss.end_time = datetime.utcnow()
        # TODO: Топ 3-т шагнал олгох логик
    db.session.commit()
    return jsonify({'current_hp': boss.current_hp, 'defeated': boss.status == 'defeated'})