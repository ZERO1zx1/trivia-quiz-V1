"""Room Socket Events"""
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.extensions import db
from app.models.room import Room, RoomPlayer
from app.utils.notify import send_notification

def register_room_events(socketio):

    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            current_user.is_online = True
            db.session.commit()
            emit('connected', {'user_id': current_user.id, 'username': current_user.username})

    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            current_user.is_online = False
            db.session.commit()

    @socketio.on('join_room')
    def handle_join_room(data):
        room_code = data.get('room_code')
        room = Room.query.filter_by(code=room_code).first()
        if not room:
            emit('error', {'message': 'Room not found'})
            return

        player = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()
        if not player:
            emit('error', {'message': 'Not in room'})
            return

        join_room(room_code)
        players = RoomPlayer.query.filter_by(room_id=room.id).all()
        players_data = [p.to_dict() for p in players]

        emit('player_joined', {
            'player': player.to_dict(),
            'players': players_data,
            'player_count': len(players_data)
        }, room=room_code)

        emit('room_joined', {
            'room': room.to_dict(),
            'players': players_data,
            'is_host': room.host_id == current_user.id
        })

    @socketio.on('leave_room_socket')
    def handle_leave_room_socket(data):
        room_code = data.get('room_code')
        room = Room.query.filter_by(code=room_code).first()
        if room:
            leave_room(room_code)
            player = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()
            if player:
                db.session.delete(player)
                if room.host_id == current_user.id:
                    next_player = RoomPlayer.query.filter(
                        RoomPlayer.room_id == room.id,
                        RoomPlayer.user_id != current_user.id
                    ).first()
                    if next_player:
                        room.host_id = next_player.user_id
                    else:
                        db.session.delete(room)
                db.session.commit()
                players = RoomPlayer.query.filter_by(room_id=room.id).all()
                emit('player_left', {
                    'user_id': current_user.id,
                    'players': [p.to_dict() for p in players]
                }, room=room_code)

    @socketio.on('toggle_ready')
    def handle_toggle_ready(data):
        room_code = data.get('room_code')
        room = Room.query.filter_by(code=room_code).first()
        if not room:
            return
        player = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()
        if player:
            player.is_ready = not player.is_ready
            db.session.commit()
            players = RoomPlayer.query.filter_by(room_id=room.id).all()
            emit('player_ready_changed', {
                'user_id': current_user.id,
                'is_ready': player.is_ready,
                'players': [p.to_dict() for p in players],
                'all_ready': all(p.is_ready for p in players) and len(players) >= 2
            }, room=room_code)

    @socketio.on('send_chat')
    def handle_chat(data):
        room_code = data.get('room_code')
        message = data.get('message', '').strip()
        if not message or len(message) > 500:
            return
        room = Room.query.filter_by(code=room_code).first()
        if not room:
            return
        player = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()
        if not player:
            return
        emit('chat_message', {
            'user_id': current_user.id,
            'username': current_user.username,
            'avatar': current_user.avatar_url,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_code)

    @socketio.on('kick_player')
    def handle_kick(data):
        room_code = data.get('room_code')
        user_id = data.get('user_id')
        room = Room.query.filter_by(code=room_code).first()
        if not room or room.host_id != current_user.id:
            emit('error', {'message': 'Unauthorized'})
            return
        player = RoomPlayer.query.filter_by(room_id=room.id, user_id=user_id).first()
        if player:
            db.session.delete(player)
            db.session.commit()
            players = RoomPlayer.query.filter_by(room_id=room.id).all()
            emit('player_kicked', {
                'user_id': user_id,
                'kicked_by': current_user.username,
                'players': [p.to_dict() for p in players]
            }, room=room_code)
            emit('kicked_from_room', {'room_code': room_code}, room=request.sid)

    @socketio.on('invite_to_room')
    def handle_invite(data):
        friend_id = data.get('friend_id')
        room_code = data.get('room_code')
        # Урилгын мэдэгдэл илгээх
        send_notification(
            user_id=friend_id,
            title='Game Invite',
            message=f'{current_user.username} invited you to room {room_code}!',
            notif_type='game_invite'
        )