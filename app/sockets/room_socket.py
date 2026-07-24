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
            print(f"User {current_user.username} connected")

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

        # Socket.IO room-д нэгдэх
        join_room(room_code)

        players = RoomPlayer.query.filter_by(room_id=room.id).all()
        players_data = [p.to_dict() for p in players]

        # Өрөөнд байгаа бүх хүмүүст мэдэгдэх
        emit('player_joined', {
            'player': player.to_dict(),
            'players': players_data,
            'player_count': len(players_data)
        }, room=room_code)

        # Холбогдсон хэрэглэгчид мэдэгдэх
        emit('room_joined', {
            'room': room.to_dict(),
            'players': players_data,
            'is_host': room.host_id == current_user.id
        })

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
            players_data = [p.to_dict() for p in players]
            all_ready = all(p.is_ready for p in players) and len(players) >= 2

            emit('player_ready_changed', {
                'user_id': current_user.id,
                'is_ready': player.is_ready,
                'players': players_data,
                'all_ready': all_ready
            }, room=room_code)

    @socketio.on('start_game_lobby')
    def handle_start_game(data):
        """Host starts the game from the lobby. Redirects players to quiz page.
        
        NOTE: Renamed from 'start_game' to avoid conflict with game_socket.py's
        'start_game' which handles actual game state initialization.
        """
        room_code = data.get('room_code')
        room = Room.query.filter_by(code=room_code).first()
        if not room or room.host_id != current_user.id:
            emit('error', {'message': 'Only the host can start the game.'})
            return

        players = RoomPlayer.query.filter_by(room_id=room.id).all()
        if len(players) < 2:
            emit('error', {'message': 'Need at least 2 players.'})
            return

        if not all(p.is_ready for p in players):
            emit('error', {'message': 'All players must be ready.'})
            return

        # Тоглоом эхлүүлэх
        room.status = 'playing'
        room.started_at = datetime.utcnow()
        db.session.commit()

        # Бүх хэрэглэгчийг quiz хуудас руу чиглүүлэх
        emit('game_started', {
            'room_code': room_code,
            'redirect_url': f'/quiz/play/{room_code}'
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
        target_id = data.get('user_id')
        room = Room.query.filter_by(code=room_code).first()
        if not room or room.host_id != current_user.id:
            emit('error', {'message': 'Unauthorized'})
            return

        player = RoomPlayer.query.filter_by(room_id=room.id, user_id=target_id).first()
        if player:
            db.session.delete(player)
            db.session.commit()
            players = RoomPlayer.query.filter_by(room_id=room.id).all()
            emit('player_kicked', {
                'user_id': target_id,
                'kicked_by': current_user.username,
                'players': [p.to_dict() for p in players]
            }, room=room_code)

    @socketio.on('leave_room')
    def handle_leave_room(data):
        room_code = data.get('room_code')
        room = Room.query.filter_by(code=room_code).first()
        if not room:
            return

        player = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()
        if player:
            if room.host_id == current_user.id:
                # Transfer host or delete room
                next_player = RoomPlayer.query.filter(
                    RoomPlayer.room_id == room.id,
                    RoomPlayer.user_id != current_user.id
                ).first()
                if next_player:
                    room.host_id = next_player.user_id
                else:
                    db.session.delete(room)
            db.session.delete(player)
            db.session.commit()

            leave_room(room_code)
            remaining = RoomPlayer.query.filter_by(room_id=room.id).all()
            emit('player_left', {
                'user_id': current_user.id,
                'players': [p.to_dict() for p in remaining],
                'player_count': len(remaining)
            }, room=room_code)
