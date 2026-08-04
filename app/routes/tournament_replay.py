"""Tournament Replay - Watch past tournament matches"""
from flask import Blueprint, jsonify, request, render_template
from app.extensions import db
from app.models.tournament import Tournament, TournamentMatch

tournament_replay_bp = Blueprint('tournament_replay', __name__, url_prefix='/tournament-replay')


@tournament_replay_bp.route('/tournament/<int:tournament_id>')
def view_replay(tournament_id):
    """View tournament replay page."""
    tournament = Tournament.query.get_or_404(tournament_id)
    return render_template('tournament/replay.html', tournament=tournament)


@tournament_replay_bp.route('/api/tournaments/<int:tournament_id>/replay')
def get_replay(tournament_id):
    """Get tournament replay data for a specific tournament."""
    tournament = Tournament.query.get_or_404(tournament_id)

    if tournament.status not in ['completed', 'ongoing']:
        return jsonify({'error': 'No replay data available'}), 404

    matches = TournamentMatch.query.filter_by(
        tournament_id=tournament_id
    ).order_by(TournamentMatch.round_number, TournamentMatch.match_order).all()

    matches_data = []
    for match in matches:
        matches_data.append({
            'id': match.id,
            'round': match.round_number,
            'order': match.match_order,
            'player_a': {
                'id': match.player_a_id,
                'username': match.player_a.username if match.player_a else 'Unknown'
            },
            'player_b': {
                'id': match.player_b_id,
                'username': match.player_b.username if match.player_b else 'Unknown'
            },
            'score_a': match.score_a,
            'score_b': match.score_b,
            'winner_id': match.winner_id,
            'is_completed': match.is_completed
        })

    return jsonify({
        'tournament': {
            'id': tournament.id,
            'name': tournament.name,
            'status': tournament.status,
            'max_participants': tournament.max_participants
        },
        'matches': matches_data
    })
