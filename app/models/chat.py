"""Advanced Chat System Models"""
from datetime import datetime
from app.extensions import db


class ChatChannel(db.Model):
    __tablename__ = 'chat_channels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    channel_type = db.Column(db.String(30), nullable=False)  # global, guild, party, room, private, admin
    description = db.Column(db.Text, default='')
    is_private = db.Column(db.Boolean, default=False)
    slowmode_seconds = db.Column(db.Integer, default=0)
    max_messages = db.Column(db.Integer, default=1000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    messages = db.relationship('ChatMessage', back_populates='channel', lazy='dynamic')
    members = db.relationship('ChatMember', back_populates='channel', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'channel_type': self.channel_type,
            'description': self.description,
            'is_private': self.is_private,
            'slowmode_seconds': self.slowmode_seconds
        }

    def __repr__(self):
        return f'<ChatChannel {self.name} type={self.channel_type}>'


class ChatMember(db.Model):
    __tablename__ = 'chat_members'
    __table_args__ = (
        db.UniqueConstraint('channel_id', 'user_id',
                            name='uq_chat_member_channel_user'),
    )

    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('chat_channels.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_muted = db.Column(db.Boolean, default=False)
    muted_until = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(20), default='member')  # member, moderator, admin
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_read_at = db.Column(db.DateTime)

    channel = db.relationship('ChatChannel', back_populates='members')
    user = db.relationship('User', backref='chat_memberships')

    def __repr__(self):
        return f'<ChatMember user={self.user_id} channel={self.channel_id}>'


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('chat_channels.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, emoji, gif, sticker, system
    is_edited = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=True)
    is_pinned = db.Column(db.Boolean, default=False)
    pinned_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited_at = db.Column(db.DateTime, nullable=True)

    channel = db.relationship('ChatChannel', back_populates='messages')
    user = db.relationship('User', backref='chat_messages')
    reply_to = db.relationship('ChatMessage', remote_side=[id])
    reactions = db.relationship('ChatReaction', back_populates='message', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'content': self.content,
            'message_type': self.message_type,
            'is_edited': self.is_edited,
            'reply_to_id': self.reply_to_id,
            'is_pinned': self.is_pinned,
            'created_at': self.created_at.isoformat(),
            'reactions_count': self.reactions.count()
        }

    def __repr__(self):
        return f'<ChatMessage channel={self.channel_id} user={self.user_id}>'


class ChatReaction(db.Model):
    __tablename__ = 'chat_reactions'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    emoji = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    message = db.relationship('ChatMessage', back_populates='reactions')
    user = db.relationship('User', backref='chat_reactions')

    def __repr__(self):
        return f'<ChatReaction emoji={self.emoji} message={self.message_id}>'
