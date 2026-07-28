"""Tournament System Models"""
from datetime import datetime
from app.extensions import db


class Tournament(db.Model):
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    type = db.Column(db.String(30), default='bracket')  # bracket, swiss, double_elimination, round_robin
    status = db.Column(db.String(20), default='upcoming')  # upcoming, registration, active, completed
    category = db.Column(db.String(100), default='general')
    difficulty = db.Column(db.String(20), default='mixed')
    max_participants = db.Column(db.Integer, default=32)
    entry_fee = db.Column(db.Integer, default=0)
    prize_pool = db.Column(db.Integer, default=0)
    prize_distribution = db.Column(db.Text, default='')  # JSON string
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    registration_open = db.Column(db.Boolean, default=True)
    registration_close = db.Column(db.DateTime)
    region = db.Column(db.String(10), default='global')
    is_ranked = db.Column(db.Boolean, default=True)
    rules = db.Column(db.Text, default='')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', backref='created_tournaments')
    participants = db.relationship('TournamentParticipant', back_populates='tournament', lazy='dynamic')
    matches = db.relationship('TournamentMatch', back_populates='tournament', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'status': self.status,
            'category': self.category,
            'difficulty': self.difficulty,
            'max_participants': self.max_participants,
            'entry_fee': self.entry_fee,
            'prize_pool': self.prize_pool,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'region': self.region,
            'participants_count': self.participants.count()
        }

    def __repr__(self):
        return f'<Tournament {self.name}>'


class TournamentParticipant(db.Model):
    __tablename__ = 'tournament_participants'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seed = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    eliminated = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    tournament = db.relationship('Tournament', back_populates='participants')
    user = db.relationship('User', backref='tournament_participations')

    def __repr__(self):
        return f'<TournamentParticipant tournament={self.tournament_id} user={self.user_id}>'


class TournamentMatch(db.Model):
    __tablename__ = 'tournament_matches'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    round_number = db.Column(db.Integer, default=1)
    match_number = db.Column(db.Integer, default=1)
    player_a_id = db.Column(db.Integer, db.ForeignKey('tournament_participants.id'), nullable=True)
    player_b_id = db.Column(db.Integer, db.ForeignKey('tournament_participants.id'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('tournament_participants.id'), nullable=True)
    score_a = db.Column(db.Integer, default=0)
    score_b = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    scheduled_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)

    tournament = db.relationship('Tournament', back_populates='matches')
    player_a = db.relationship('TournamentParticipant', foreign_keys=[player_a_id])
    player_b = db.relationship('TournamentParticipant', foreign_keys=[player_b_id])
    winner = db.relationship('TournamentParticipant', foreign_keys=[winner_id])

    def __repr__(self):
        return f'<TournamentMatch round={self.round_number} match={self.match_number}>'


class TournamentHistory(db.Model):
    __tablename__ = 'tournament_history'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    placement = db.Column(db.Integer)
    prize_won = db.Column(db.Integer, default=0)
    mvp_votes = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='tournament_history')
    tournament = db.relationship('Tournament', backref='history_records')

    def __repr__(self):
        return f'<TournamentHistory user={self.user_id} place={self.placement}>'
