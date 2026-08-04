"""Guild System 2.0 Models"""
from datetime import datetime
from app.extensions import db


class Guild(db.Model):
    __tablename__ = 'guilds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    tag = db.Column(db.String(10), unique=True, nullable=False)  # [TAG]
    description = db.Column(db.Text, default='')
    banner_url = db.Column(db.String(500), default='')
    icon_url = db.Column(db.String(500), default='')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    coins = db.Column(db.Integer, default=0)  # Guild Treasury
    member_count = db.Column(db.Integer, default=1)
    max_members = db.Column(db.Integer, default=50)
    region = db.Column(db.String(10), default='global')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    members = db.relationship('GuildMember', back_populates='guild', lazy='dynamic')
    ranks = db.relationship('GuildRank', back_populates='guild', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'tag': self.tag,
            'description': self.description,
            'banner_url': self.banner_url,
            'icon_url': self.icon_url,
            'level': self.level,
            'xp': self.xp,
            'coins': self.coins,
            'member_count': self.member_count,
            'region': self.region,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Guild {self.name}>'


class GuildMember(db.Model):
    __tablename__ = 'guild_members'

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rank_id = db.Column(db.Integer, db.ForeignKey('guild_ranks.id'), nullable=False)
    coins_contributed = db.Column(db.Integer, default=0)
    xp_contributed = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned = db.Column(db.Boolean, default=False)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    guild = db.relationship('Guild', back_populates='members')
    user = db.relationship('User', backref='guild_memberships', lazy='joined')
    rank = db.relationship('GuildRank', back_populates='members')

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict() if self.user else None,
            'rank': self.rank.name if self.rank else None,
            'coins_contributed': self.coins_contributed,
            'xp_contributed': self.xp_contributed,
            'joined_at': self.joined_at.isoformat()
        }

    def __repr__(self):
        return f'<GuildMember user={self.user_id} guild={self.guild_id}>'


class GuildRank(db.Model):
    __tablename__ = 'guild_ranks'

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # Owner, Co-Leader, Leader, Officer, Member, Recruit
    color = db.Column(db.String(7), default='#FFFFFF')
    icon = db.Column(db.String(50), default='')
    permissions = db.Column(db.Text, default='')  # JSON string of permissions
    order = db.Column(db.Integer, default=0)

    guild = db.relationship('Guild', back_populates='ranks')
    members = db.relationship('GuildMember', back_populates='rank', lazy='dynamic')

    def __repr__(self):
        return f'<GuildRank {self.name}>'


class GuildSkill(db.Model):
    __tablename__ = 'guild_skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    level = db.Column(db.Integer, default=0)
    max_level = db.Column(db.Integer, default=10)
    cost = db.Column(db.Integer, default=100)  # Guild coins cost per level
    effect = db.Column(db.Text, default='')  # JSON string describing the effect
    category = db.Column(db.String(50), default='general')

    def __repr__(self):
        return f'<GuildSkill {self.name} Lv.{self.level}>'


class GuildQuest(db.Model):
    __tablename__ = 'guild_quests'

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    requirement = db.Column(db.String(500))  # e.g., "win_10_matches", "collect_5000_coins"
    reward_xp = db.Column(db.Integer, default=100)
    reward_coins = db.Column(db.Integer, default=500)
    progress = db.Column(db.Integer, default=0)
    target = db.Column(db.Integer, default=10)
    is_completed = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guild = db.relationship('Guild', backref='quests', lazy='joined')

    def __repr__(self):
        return f'<GuildQuest {self.title}>'


class GuildWar(db.Model):
    __tablename__ = 'guild_wars'

    id = db.Column(db.Integer, primary_key=True)
    guild_a_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    guild_b_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, active, completed
    score_a = db.Column(db.Integer, default=0)
    score_b = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    winner_id = db.Column(db.Integer, nullable=True)

    guild_a = db.relationship('Guild', foreign_keys=[guild_a_id], backref='wars_as_a')
    guild_b = db.relationship('Guild', foreign_keys=[guild_b_id], backref='wars_as_b')

    def __repr__(self):
        return f'<GuildWar {self.guild_a_id} vs {self.guild_b_id}>'


class GuildBoss(db.Model):
    __tablename__ = 'guild_bosses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hp = db.Column(db.Integer, default=10000)
    max_hp = db.Column(db.Integer, default=10000)
    level = db.Column(db.Integer, default=1)
    element = db.Column(db.String(20), default='none')  # fire, water, earth, air, light, dark
    reward_pool = db.Column(db.Text, default='')  # JSON string
    is_active = db.Column(db.Boolean, default=True)
    spawn_time = db.Column(db.DateTime)
    defeated_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<GuildBoss {self.name} HP={self.hp}/{self.max_hp}>'


class GuildBossDamage(db.Model):
    """Tracks damage dealt to guild boss by guild members."""
    __tablename__ = 'guild_boss_damage'

    id = db.Column(db.Integer, primary_key=True)
    boss_id = db.Column(db.Integer, db.ForeignKey('guild_bosses.id'), nullable=False)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    damage = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    boss = db.relationship('GuildBoss', backref='damage_log')
    guild = db.relationship('Guild', backref='boss_damage_log')
    user = db.relationship('User')

    def __repr__(self):
        return f'<GuildBossDamage boss={self.boss_id} user={self.user_id} dmg={self.damage}>'
