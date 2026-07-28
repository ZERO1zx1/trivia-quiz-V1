"""Guild Socket.IO Handler"""
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.extensions import socketio, db
from app.models.guild import Guild, GuildMember
from datetime import datetime


def register_guild_events(socketio):
    """Register guild-related socket events"""

    @socketio.on('join_guild')
    def handle_join_guild(data):
        """Join guild room"""
        guild_id = data.get('guild_id')
        if not guild_id:
            emit('error', {'message': 'Guild ID required'})
            return

        member = GuildMember.query.filter_by(
            guild_id=guild_id, user_id=current_user.id
        ).first()

        if not member:
            emit('error', {'message': 'Not a member of this guild'})
            return

        room = f'guild_{guild_id}'
        join_room(room)

        emit('guild_joined', {
            'guild_id': guild_id,
            'username': current_user.username
        })

    @socketio.on('guild_chat')
    def handle_guild_chat(data):
        """Send guild chat message"""
        guild_id = data.get('guild_id')
        content = data.get('content', '').strip()

        if not guild_id or not content:
            emit('error', {'message': 'Invalid message'})
            return

        member = GuildMember.query.filter_by(
            guild_id=guild_id, user_id=current_user.id
        ).first()

        if not member:
            emit('error', {'message': 'Not a member'})
            return

        room = f'guild_{guild_id}'
        emit('guild_message', {
            'username': current_user.username,
            'avatar_url': current_user.avatar_url,
            'content': content,
            'rank': member.rank.name if member.rank else 'Member',
            'timestamp': datetime.utcnow().isoformat()
        }, room=room)

    @socketio.on('guild_boss_attack')
    def handle_boss_attack(data):
        """Attack guild boss"""
        from app.models.guild import GuildBoss
        guild_id = data.get('guild_id')
        damage = data.get('damage', 0)

        if not guild_id or damage <= 0:
            emit('error', {'message': 'Invalid attack'})
            return

        member = GuildMember.query.filter_by(
            guild_id=guild_id, user_id=current_user.id
        ).first()

        if not member:
            emit('error', {'message': 'Not a member'})
            return

        boss = GuildBoss.query.filter_by(is_active=True).first()
        if not boss:
            emit('error', {'message': 'No active boss'})
            return

        boss.hp = max(0, boss.hp - damage)
        member.xp_contributed += damage

        if boss.hp <= 0:
            boss.defeated_at = datetime.utcnow()
            boss.is_active = False

        db.session.commit()

        room = f'guild_{guild_id}'
        emit('boss_damage', {
            'username': current_user.username,
            'damage': damage,
            'boss_hp': boss.hp,
            'boss_max_hp': boss.max_hp,
            'defeated': boss.hp <= 0
        }, room=room)

    @socketio.on('guild_war_start')
    def handle_war_start(data):
        """Start guild war"""
        from app.models.guild import GuildWar
        guild_id = data.get('guild_id')
        target_guild_id = data.get('target_guild_id')

        room = f'guild_{guild_id}'
        emit('war_started', {
            'guild_id': guild_id,
            'target_guild_id': target_guild_id,
            'message': 'Guild War has begun!'
        }, room=room)

    @socketio.on('leave_guild')
    def handle_leave_guild(data):
        """Leave guild room"""
        guild_id = data.get('guild_id')
        room = f'guild_{guild_id}'
        leave_room(room)
