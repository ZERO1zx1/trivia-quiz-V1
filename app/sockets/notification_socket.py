"""Notification Socket Events (Chapter 9, 11)"""
from flask_login import current_user
from flask_socketio import emit, join_room
from app.extensions import db
from app.models.user import User
from app.utils.notify import send_notification


def register_notification_events(socketio):

    @socketio.on('connect', namespace='/notifications')
    def handle_connect():
        if current_user.is_authenticated:
            room = f'user_{current_user.id}'
            join_room(room)
            print(f'User {current_user.id} joined notification room {room}')

    @socketio.on('direct_message', namespace='/notifications')
    def handle_direct_message(data):
        """Handle direct messages between users."""
        if not current_user.is_authenticated:
            return

        to_user_id = data.get('to_user_id')
        message = data.get('message', '').strip()

        if not to_user_id or not message or len(message) > 1000:
            emit('error', {'message': 'Invalid message'}, namespace='/notifications')
            return

        target_user = User.query.get(to_user_id)
        if not target_user:
            emit('error', {'message': 'User not found'}, namespace='/notifications')
            return

        # Store notification
        send_notification(
            user_id=target_user.id,
            title=f'Message from {current_user.username}',
            message=message,
            notif_type='info'
        )

        # Emit to target user's notification room
        emit('direct_message', {
            'from_user_id': current_user.id,
            'from_username': current_user.username,
            'from_avatar': current_user.avatar_url,
            'message': message
        }, room=f'user_{target_user.id}', namespace='/notifications')

        # Confirm to sender
        emit('message_sent', {
            'to_user_id': to_user_id,
            'to_username': target_user.username
        }, namespace='/notifications')
