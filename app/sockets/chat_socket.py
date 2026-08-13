"""Chat Socket.IO Handler"""
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.extensions import socketio, db, utcnow
from app.models.chat import ChatMessage, ChatChannel, ChatMember
from datetime import datetime


def register_chat_events(socketio):
    """Register chat-related socket events"""

    @socketio.on('join_chat')
    def handle_join_chat(data):
        """Join a chat channel"""
        channel_id = data.get('channel_id')
        if not channel_id:
            emit('error', {'message': 'Channel ID required'})
            return

        channel = db.session.get(ChatChannel, channel_id)
        member = ChatMember.query.filter_by(
            channel_id=channel_id, user_id=current_user.id).first()
        if not channel or (channel.is_private and not member):
            emit('error', {'message': 'Access denied'})
            return
        room = f'chat_{channel_id}'
        join_room(room)
        emit('joined', {'channel_id': channel_id, 'username': current_user.username})

    @socketio.on('leave_chat')
    def handle_leave_chat(data):
        """Leave a chat channel"""
        channel_id = data.get('channel_id')
        if not channel_id:
            return

        room = f'chat_{channel_id}'
        leave_room(room)

    @socketio.on('send_message')
    def handle_send_message(data):
        """Send a chat message"""
        channel_id = data.get('channel_id')
        content = data.get('content', '').strip()

        if not channel_id or not content:
            emit('error', {'message': 'Invalid message'})
            return

        if len(content) > 2000:
            emit('error', {'message': 'Message too long'})
            return

        channel = db.session.get(ChatChannel, channel_id)
        if not channel:
            emit('error', {'message': 'Channel not found'})
            return

        message = ChatMessage(
            channel_id=channel_id,
            user_id=current_user.id,
            content=content,
            message_type=data.get('type', 'text')
        )
        db.session.add(message)
        db.session.commit()

        room = f'chat_{channel_id}'
        emit('new_message', {
            'id': message.id,
            'user_id': current_user.id,
            'username': current_user.username,
            'avatar_url': current_user.avatar_url,
            'content': message.content,
            'message_type': message.message_type,
            'created_at': message.created_at.isoformat()
        }, room=room)

    @socketio.on('typing')
    def handle_typing(data):
        """User is typing indicator"""
        channel_id = data.get('channel_id')
        room = f'chat_{channel_id}'
        emit('user_typing', {
            'username': current_user.username,
            'is_typing': data.get('is_typing', True)
        }, room=room, include_self=False)

    @socketio.on('delete_message')
    def handle_delete_message(data):
        """Delete a chat message"""
        message_id = data.get('message_id')
        message = db.session.get(ChatMessage, message_id)

        if not message:
            emit('error', {'message': 'Message not found'})
            return

        if message.user_id != current_user.id and not current_user.is_admin:
            emit('error', {'message': 'Access denied'})
            return

        message.is_deleted = True
        db.session.commit()

        channel_id = message.channel_id
        room = f'chat_{channel_id}'
        emit('message_deleted', {
            'message_id': message_id,
            'channel_id': channel_id
        }, room=room)

    @socketio.on('edit_message')
    def handle_edit_message(data):
        """Edit a chat message"""
        message_id = data.get('message_id')
        new_content = data.get('content', '').strip()

        if not new_content:
            emit('error', {'message': 'Content required'})
            return

        message = db.session.get(ChatMessage, message_id)
        if not message:
            emit('error', {'message': 'Message not found'})
            return

        if message.user_id != current_user.id:
            emit('error', {'message': 'Access denied'})
            return

        message.content = new_content
        message.is_edited = True
        message.edited_at = utcnow()
        db.session.commit()

        channel_id = message.channel_id
        room = f'chat_{channel_id}'
        emit('message_edited', {
            'message_id': message_id,
            'new_content': message.content,
            'edited_at': message.edited_at.isoformat()
        }, room=room)
