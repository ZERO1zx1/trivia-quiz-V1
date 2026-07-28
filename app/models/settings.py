"""Settings & Security 2.0 Models"""
from datetime import datetime
from app.extensions import db


class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    language = db.Column(db.String(5), default='en')
    theme = db.Column(db.String(20), default='dark')  # dark, light, auto
    font_size = db.Column(db.String(10), default='medium')  # small, medium, large
    audio_enabled = db.Column(db.Boolean, default=True)
    sfx_enabled = db.Column(db.Boolean, default=True)
    music_enabled = db.Column(db.Boolean, default=True)
    animation_enabled = db.Column(db.Boolean, default=True)
    performance_mode = db.Column(db.Boolean, default=False)
    notifications_enabled = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    discord_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    privacy_show_profile = db.Column(db.Boolean, default=True)
    privacy_show_stats = db.Column(db.Boolean, default=True)
    privacy_show_inventory = db.Column(db.Boolean, default=True)
    privacy_show_online = db.Column(db.Boolean, default=True)
    privacy_allow_duels = db.Column(db.Boolean, default=True)
    privacy_allow_gifts = db.Column(db.Boolean, default=True)
    accessibility_high_contrast = db.Column(db.Boolean, default=False)
    accessibility_reduce_motion = db.Column(db.Boolean, default=False)
    keybinds = db.Column(db.Text, default='')  # JSON: custom keybindings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='settings', uselist=False)

    def to_dict(self):
        return {
            'language': self.language,
            'theme': self.theme,
            'font_size': self.font_size,
            'audio_enabled': self.audio_enabled,
            'sfx_enabled': self.sfx_enabled,
            'music_enabled': self.music_enabled,
            'animation_enabled': self.animation_enabled,
            'performance_mode': self.performance_mode,
            'notifications_enabled': self.notifications_enabled,
            'privacy_show_profile': self.privacy_show_profile,
            'privacy_show_stats': self.privacy_show_stats,
            'privacy_show_inventory': self.privacy_show_inventory,
            'privacy_show_online': self.privacy_show_online
        }

    def __repr__(self):
        return f'<UserSettings user={self.user_id}>'


class DeviceHistory(db.Model):
    __tablename__ = 'device_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_name = db.Column(db.String(200))
    browser = db.Column(db.String(100))
    os = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    location = db.Column(db.String(200))
    is_current = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='device_history')

    def __repr__(self):
        return f'<DeviceHistory user={self.user_id} device={self.device_name}>'


class TwoFactorAuth(db.Model):
    __tablename__ = 'two_factor_auth'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    is_enabled = db.Column(db.Boolean, default=False)
    secret_key = db.Column(db.String(100))
    backup_codes = db.Column(db.Text, default='')  # JSON array of backup codes
    method = db.Column(db.String(20), default='app')  # app (TOTP), email
    enabled_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='two_factor')

    def __repr__(self):
        return f'<TwoFactorAuth user={self.user_id} enabled={self.is_enabled}>'


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(500), unique=True, nullable=False)
    device_info = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='sessions')

    def __repr__(self):
        return f'<Session user={self.user_id} active={self.is_active}>'


class BanAppeal(db.Model):
    __tablename__ = 'ban_appeals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ban_type = db.Column(db.String(20), default='ban')  # ban, mute, shadow_ban
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, denied
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review_notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f'<BanAppeal user={self.user_id} status={self.status}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text, default='')  # JSON: additional details
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    actor = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog action={self.action} actor={self.actor_id}>'


class FeatureToggle(db.Model):
    __tablename__ = 'feature_toggles'

    id = db.Column(db.Integer, primary_key=True)
    feature_name = db.Column(db.String(100), unique=True, nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, default='')
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FeatureToggle {self.feature_name} enabled={self.is_enabled}>'
