"""Mail System Models"""
from datetime import datetime, timedelta
from app.extensions import db, utcnow


class Mail(db.Model):
    __tablename__ = 'mails'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sender_type = db.Column(db.String(20), default='system')  # system, user, guild, admin
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, default='')
    mail_type = db.Column(db.String(30), default='system')  # system, reward, trade, gift, guild, tournament
    is_read = db.Column(db.Boolean, default=False)
    is_claimed = db.Column(db.Boolean, default=False)
    has_attachments = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, default=lambda: utcnow() + timedelta(days=30))
    created_at = db.Column(db.DateTime, default=utcnow)

    sender_user = db.relationship('User', foreign_keys=[sender_id], backref='sent_mails')
    user = db.relationship('User', foreign_keys=[user_id], backref='received_mails')
    attachments = db.relationship('MailAttachment', back_populates='mail', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'sender_type': self.sender_type,
            'subject': self.subject,
            'body': self.body,
            'mail_type': self.mail_type,
            'is_read': self.is_read,
            'is_claimed': self.is_claimed,
            'has_attachments': self.has_attachments,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Mail {self.subject} to user={self.user_id}>'


class MailAttachment(db.Model):
    __tablename__ = 'mail_attachments'

    id = db.Column(db.Integer, primary_key=True)
    mail_id = db.Column(db.Integer, db.ForeignKey('mails.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # coins, xp, box, badge, frame, title, item
    item_id = db.Column(db.Integer, nullable=True)  # reference to the item
    quantity = db.Column(db.Integer, default=1)
    is_claimed = db.Column(db.Boolean, default=False)

    mail = db.relationship('Mail', back_populates='attachments')

    def to_dict(self):
        return {
            'id': self.id,
            'item_type': self.item_type,
            'item_id': self.item_id,
            'quantity': self.quantity,
            'is_claimed': self.is_claimed
        }

    def __repr__(self):
        return f'<MailAttachment mail={self.mail_id} type={self.item_type}>'
