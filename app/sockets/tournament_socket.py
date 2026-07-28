"""Tournament Socket.IO Handler"""
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.extensions import socketio, db
from app.models.tournament import Tournament, TournamentParticipant, TournamentMatch
from datetime import datetime


def register_tournament_events(socketio):
    """Register tournament-related socket events"""

    @socketio.on('join_tournament')
    def handle_join_tournament(data):
        """Join a tournament room"""
        tournament_id = data.get('tournament_id')
        if not tournament_id:
            emit('error', {'message': 'Tournament ID required'})
            return

        tournament = Tournament.query.get(tournament_id)
        if not tournament:
            emit('error', {'message': 'Tournament not found'})
            return

        if tournament.status != 'active':
            emit('error', {'message': 'Tournament is not active'})
            return

        room = f'tournament_{tournament_id}'
        join_room(room)

        emit('tournament_joined', {
            'tournament_id': tournament_id,
            'tournament_name': tournament.name,
            'username': current_user.username
        })

    @socketio.on('tournament_ready')
    def handle_ready(data):
        """Mark player as ready"""
        tournament_id = data.get('tournament_id')
        if not tournament_id:
            return

        # Check if player is in this tournament
        participant = TournamentParticipant.query.filter_by(
            tournament_id=tournament_id, user_id=current_user.id
        ).first()

        if not participant:
            emit('error', {'message': 'Not registered for this tournament'})
            return

        room = f'tournament_{tournament_id}'
        emit('player_ready', {
            'username': current_user.username,
            'ready': data.get('ready', True)
        }, room=room)

    @socketio.on('tournament_match_start')
    def handle_match_start(data):
        """Start a tournament match"""
        tournament_id = data.get('tournament_id')
        match_id = data.get('match_id')

        if not tournament_id or not match_id:
            return

        room = f'tournament_{tournament_id}'
        emit('match_started', {
            'tournament_id': tournament_id,
            'match_id': match_id,
            'started_at': datetime.utcnow().isoformat()
        }, room=room)

    @socketio.on('tournament_match_result')
    def handle_match_result(data):
        """Submit match result"""
        tournament_id = data.get('tournament_id')
        match_id = data.get('match_id')
        winner_id = data.get('winner_id')
        score_a = data.get('score_a', 0)
        score_b = data.get('score_b', 0)

        if not tournament_id or not match_id:
            return

        match = TournamentMatch.query.get(match_id)
        if not match:
            emit('error', {'message': 'Match not found'})
            return

        match.status = 'completed'
        match.score_a = score_a
        match.score_b = score_b
        match.winner_id = winner_id
        match.completed_at = datetime.utcnow()

        # Update participants
        if match.player_a:
            if match.player_a.id == winner_id:
                match.player_a.wins += 1
            else:
                match.player_a.losses += 1
                match.player_a.eliminated = True

        if match.player_b:
            if match.player_b.id == winner_id:
                match.player_b.wins += 1
            else:
                match.player_b.losses += 1
                match.player_b.eliminated = True

        db.session.commit()

        room = f'tournament_{tournament_id}'
        emit('match_result', {
            'match_id': match_id,
            'winner_id': winner_id,
            'score_a': score_a,
            'score_b': score_b
        }, room=room)

    @socketio.on('tournament_next_round')
    def handle_next_round(data):
        """Advance to next round"""
        tournament_id = data.get('tournament_id')
        room = f'tournament_{tournament_id}'
        emit('next_round', {
            'tournament_id': tournament_id,
            'message': 'Next round starting...'
        }, room=room)

    @socketio.on('tournament_leave')
    def handle_tournament_leave(data):
        """Leave tournament room"""
        tournament_id = data.get('tournament_id')
        room = f'tournament_{tournament_id}'
        leave_room(room)
