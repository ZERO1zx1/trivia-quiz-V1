"""Chat System Routes"""
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_login import login_required, current_user
from app.extensions import db, utcnow
from app.models.chat import ChatChannel, ChatMember, ChatMessage, ChatReaction
from datetime import datetime
from app.services.supabase import SupabaseError, SupabaseService

chat_bp = Blueprint('chat', __name__)


def _can_access(channel):
    if channel.channel_type in ('global', 'public'):
        return True
    return ChatMember.query.filter_by(
        channel_id=channel.id, user_id=current_user.id).first() is not None


def _broadcast(channel_id, event, payload):
    if not SupabaseService.enabled():
        return
    try:
        SupabaseService().broadcast(
            f'chat:{channel_id}:messages', event, payload, private=True)
    except SupabaseError:
        current_app.logger.exception('Realtime chat broadcast failed')


@chat_bp.route('/')
def index():
    """Chat channels page"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    channels = ChatChannel.query.filter(
        (ChatChannel.channel_type == 'global') |
        (ChatChannel.channel_type == 'private') |
        (ChatChannel.id.in_(
            db.session.query(ChatMember.channel_id).filter_by(user_id=current_user.id)
        ))
    ).all()

    return render_template('chat/index.html', channels=channels)


@chat_bp.route('/<int:channel_id>')
@login_required
def channel(channel_id):
    """View a chat channel"""
    channel = ChatChannel.query.get_or_404(channel_id)

    # Check access
    if not _can_access(channel):
        flash('Access denied.', 'danger')
        return redirect(url_for('chat.index'))

    # Get messages
    messages = ChatMessage.query.filter_by(
        channel_id=channel.id, is_deleted=False
    ).order_by(ChatMessage.created_at.desc()).limit(100).all()
    messages.reverse()

    members = ChatMember.query.filter_by(channel_id=channel.id).all()

    my_membership = ChatMember.query.filter_by(
        channel_id=channel.id, user_id=current_user.id
    ).first()

    return render_template('chat/channel.html', channel=channel,
                           messages=messages, members=members,
                           my_membership=my_membership)


@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Send a chat message"""
    data = request.get_json() if request.is_json else request.form

    channel_id = data.get('channel_id', type=int)
    content = data.get('content', '').strip()

    if not channel_id or not content:
        return jsonify({'error': 'Channel ID and content required'}), 400

    if len(content) > 2000:
        return jsonify({'error': 'Message too long (max 2000 chars)'}), 400

    channel = ChatChannel.query.get(channel_id)
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    if not _can_access(channel):
        return jsonify({'error': 'Access denied'}), 403

    # Check if muted
    member = ChatMember.query.filter_by(
        channel_id=channel.id, user_id=current_user.id
    ).first()

    if member and member.is_muted:
        if member.muted_until and member.muted_until > utcnow():
            return jsonify({'error': 'You are muted'}), 403

    message = ChatMessage(
        channel_id=channel.id,
        user_id=current_user.id,
        content=content,
        message_type=data.get('type', 'text')
    )
    db.session.add(message)
    db.session.commit()

    payload = message.to_dict()
    payload['avatar_url'] = current_user.avatar_url
    _broadcast(channel.id, 'message_created', payload)

    return jsonify({
        'success': True,
        'message': payload
    })


@chat_bp.route('/<int:message_id>/edit', methods=['POST'])
@login_required
def edit_message(message_id):
    """Edit a chat message"""
    message = ChatMessage.query.get_or_404(message_id)

    if message.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    new_content = request.form.get('content', '').strip()
    if not new_content:
        return jsonify({'error': 'Content required'}), 400

    message.content = new_content
    message.is_edited = True
    message.edited_at = utcnow()
    db.session.commit()

    _broadcast(message.channel_id, 'message_edited', {
        'id': message.id, 'content': message.content,
        'edited_at': message.edited_at.isoformat()})

    return jsonify({'success': True})


@chat_bp.route('/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    """Delete a chat message"""
    message = ChatMessage.query.get_or_404(message_id)

    if message.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    message.is_deleted = True
    db.session.commit()

    _broadcast(message.channel_id, 'message_deleted', {'id': message.id})

    return jsonify({'success': True})


@chat_bp.route('/<int:message_id>/react', methods=['POST'])
@login_required
def react(message_id):
    """React to a message"""
    message = ChatMessage.query.get_or_404(message_id)
    emoji = request.form.get('emoji', '👍')

    existing = ChatReaction.query.filter_by(
        message_id=message.id, user_id=current_user.id, emoji=emoji
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})

    reaction = ChatReaction(
        message_id=message.id,
        user_id=current_user.id,
        emoji=emoji
    )
    db.session.add(reaction)
    db.session.commit()

    return jsonify({'success': True, 'action': 'added'})


@chat_bp.route('/<int:message_id>/pin', methods=['POST'])
@login_required
def pin_message(message_id):
    """Pin a message (admin/moderator only)"""
    message = ChatMessage.query.get_or_404(message_id)

    if not current_user.is_admin:
        return jsonify({'error': 'Admin required'}), 403

    message.is_pinned = not message.is_pinned
    if message.is_pinned:
        message.pinned_at = utcnow()
    db.session.commit()

    return jsonify({'success': True, 'pinned': message.is_pinned})


# API endpoints
@chat_bp.route('/api/channels')
@login_required
def api_channels():
    """API: List user's channels"""
    channels = ChatChannel.query.filter(
        (ChatChannel.channel_type == 'global') |
        (ChatChannel.channel_type == 'guild') |
        (ChatChannel.id.in_(
            db.session.query(ChatMember.channel_id).filter_by(user_id=current_user.id)
        ))
    ).all()

    return jsonify({
        'channels': [c.to_dict() for c in channels]
    })


@chat_bp.route('/api/<int:channel_id>/messages')
@login_required
def api_messages(channel_id):
    """API: Get channel messages"""
    limit = request.args.get('limit', 50, type=int)
    before = request.args.get('before', type=int)

    query = ChatMessage.query.filter_by(
        channel_id=channel_id, is_deleted=False
    )

    if before:
        query = query.filter(ChatMessage.id < before)

    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    messages.reverse()

    return jsonify({
        'messages': [m.to_dict() for m in messages]
    })
