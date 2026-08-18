"""Guild Wars & Guild Boss Routes"""
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db, utcnow
from app.models.guild import Guild, GuildMember, GuildWar, GuildBoss, GuildBossDamage
from app.models.user import User

guild_war_bp = Blueprint('guild_war', __name__)


@guild_war_bp.route('/api/guilds/<int:guild_id>/boss')
def get_boss(guild_id):
    """Get the current guild boss status."""
    guild = Guild.query.get_or_404(guild_id)
    boss = GuildBoss.query.filter_by(is_active=True).order_by(
        GuildBoss.spawn_time.desc()
    ).first()

    if not boss:
        return jsonify({'boss': None, 'guild_id': guild_id})

    # Calculate damage dealt by this guild
    guild_damage = GuildBossDamage.query.filter_by(
        boss_id=boss.id, guild_id=guild_id
    ).count()

    return jsonify({
        'boss': {
            'id': boss.id,
            'name': boss.name,
            'hp': boss.hp,
            'max_hp': boss.max_hp,
            'level': boss.level,
            'element': boss.element,
            'is_active': boss.is_active,
            'guild_damage': guild_damage
        },
        'guild_id': guild_id
    })


@guild_war_bp.route('/api/guilds/<int:guild_id>/wars')
def get_wars(guild_id):
    """Get guild war history."""
    guild = Guild.query.get_or_404(guild_id)
    wars = GuildWar.query.filter(
        db.or_(GuildWar.guild_a_id == guild_id, GuildWar.guild_b_id == guild_id)
    ).order_by(GuildWar.started_at.desc()).limit(20).all()

    result = []
    for war in wars:
        result.append({
            'id': war.id,
            'guild_a': {'id': war.guild_a_id, 'name': war.guild_a.name},
            'guild_b': {'id': war.guild_b_id, 'name': war.guild_b.name},
            'status': war.status,
            'score_a': war.score_a,
            'score_b': war.score_b,
            'started_at': war.started_at.isoformat() if war.started_at else None,
            'ended_at': war.ended_at.isoformat() if war.ended_at else None,
            'winner_id': war.winner_id
        })

    return jsonify({'wars': result})


@guild_war_bp.route('/api/guilds/<int:guild_id>/wars/challenge', methods=['POST'])
@login_required
def challenge_guild(guild_id):
    """Challenge another guild to a war."""
    from app.models.user import User as UserModel
    
    data = request.get_json()
    target_guild_id = data.get('target_guild_id')

    if not target_guild_id:
        return jsonify({'error': 'Missing target_guild_id'}), 400

    # Check if user is guild owner
    member = GuildMember.query.filter_by(
        user_id=current_user.id, guild_id=guild_id
    ).first()

    if not member or member.rank.name not in ['Owner', 'Co-Leader']:
        return jsonify({'error': 'Only guild leaders can start wars'}), 403

    target_guild = Guild.query.get(target_guild_id)
    if not target_guild:
        return jsonify({'error': 'Target guild not found'}), 404

    # Check for existing active war
    existing = GuildWar.query.filter(
        db.or_(
            db.and_(GuildWar.guild_a_id == guild_id, GuildWar.guild_b_id == target_guild_id),
            db.and_(GuildWar.guild_a_id == target_guild_id, GuildWar.guild_b_id == guild_id)
        ),
        GuildWar.status == 'active'
    ).first()

    if existing:
        return jsonify({'error': 'Already in an active war with this guild'}), 400

    war = GuildWar(
        guild_a_id=guild_id,
        guild_b_id=target_guild_id,
        status='pending',
        started_at=utcnow()
    )
    db.session.add(war)
    db.session.commit()

    return jsonify({'war_id': war.id, 'message': 'War challenge sent!'})
