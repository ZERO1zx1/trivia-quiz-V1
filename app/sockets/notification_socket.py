"""Notification Socket Events"""
from flask_login import current_user
from flask_socketio import join_room

def register_notification_events(socketio):

    @socketio.on('connect', namespace='/notifications')
    def handle_connect():
        if current_user.is_authenticated:
            room = f'user_{current_user.id}'
            join_room(room)
            print(f'User {current_user.id} joined notification room {room}')