"""Tournament System Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.tournament import Tournament, TournamentParticipant, TournamentMatch, TournamentHistory
from app.models.user import User
from app.utils.admin import admin_required
from datetime import datetime, timedelta

tournament_bp = Blueprint('tournament', __name__, url_prefix='/tournament')


@tournament_bp.route('/')
def index():
    """Tournament list page"""
    status = request.args.get('status', 'all')
    region = request.args.get('region', 'global')
    page = request.args.get('page', 1, type=int)

    query = Tournament.query
    if status != 'all':
        query = query.filter_by(status=status)
    if region != 'global':
        query = query.filter_by(region=region)

    tournaments = query.order_by(Tournament.start_time.desc()).paginate(
        page=page, per_page=12, error_out=False
    )

    return render_template('tournament/index.html', tournaments=tournaments)


@tournament_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Create a tournament"""
    if request.method == 'POST':
        tournament = Tournament(
            name=request.form.get('name', '').strip(),
            description=request.form.get('description', ''),
            type=request.form.get('type', 'bracket'),
            category=request.form.get('category', 'general'),
            difficulty=request.form.get('difficulty', 'mixed'),
            max_participants=request.form.get('max_participants', 32, type=int),
            entry_fee=request.form.get('entry_fee', 0, type=int),
            prize_pool=request.form.get('prize_pool', 0, type=int),
            region=request.form.get('region', 'global'),
            is_ranked=request.form.get('is_ranked') == 'on',
            created_by=current_user.id
        )

        start_time = request.form.get('start_time')
        if start_time:
            tournament.start_time = datetime.fromisoformat(start_time)

        end_time = request.form.get('end_time')
        if end_time:
            tournament.end_time = datetime.fromisoformat(end_time)

        registration_close = request.form.get('registration_close')
        if registration_close:
            tournament.registration_close = datetime.fromisoformat(registration_close)

        db.session.add(tournament)
        db.session.commit()

        flash(f'Tournament "{tournament.name}" created!', 'success')
        return redirect(url_for('tournament.detail', tournament_id=tournament.id))

    return render_template('tournament/create.html')


@tournament_bp.route('/<int:tournament_id>')
def detail(tournament_id):
    """Tournament detail page"""
    tournament = Tournament.query.get_or_404(tournament_id)
    participants = tournament.participants.order_by(
        TournamentParticipant.seed
    ).limit(tournament.max_participants).all()
    matches = tournament.matches.order_by(
        TournamentMatch.round_number, TournamentMatch.match_number
    ).all()

    my_participation = None
    if current_user.is_authenticated:
        my_participation = TournamentParticipant.query.filter_by(
            tournament_id=tournament.id, user_id=current_user.id
        ).first()

    return render_template('tournament/detail.html', tournament=tournament,
                           participants=participants, matches=matches,
                           my_participation=my_participation)


@tournament_bp.route('/<int:tournament_id>/bracket')
def bracket(tournament_id):
    """Tournament bracket view"""
    tournament = Tournament.query.get_or_404(tournament_id)
    matches = tournament.matches.order_by(
        TournamentMatch.round_number, TournamentMatch.match_number
    ).all()

    bracket_data = {}
    for match in matches:
        round_num = match.round_number
        if round_num not in bracket_data:
            bracket_data[round_num] = []
        bracket_data[round_num].append({
            'id': match.id,
            'round': match.round_number,
            'match': match.match_number,
            'player_a': match.player_a.user.username if match.player_a and match.player_a.user else 'TBD',
            'player_b': match.player_b.user.username if match.player_b and match.player_b.user else 'TBD',
            'score_a': match.score_a,
            'score_b': match.score_b,
            'status': match.status
        })

    return render_template('tournament/bracket.html', tournament=tournament, bracket_data=bracket_data)


@tournament_bp.route('/<int:tournament_id>/register', methods=['POST'])
@login_required
def register(tournament_id):
    """Register for a tournament"""
    tournament = Tournament.query.get_or_404(tournament_id)

    if tournament.status not in ('upcoming', 'registration'):
        flash('Registration is closed.', 'warning')
        return redirect(url_for('tournament.detail', tournament_id=tournament_id))

    if TournamentParticipant.query.filter_by(
        tournament_id=tournament.id, user_id=current_user.id
    ).first():
        flash('You are already registered.', 'warning')
        return redirect(url_for('tournament.detail', tournament_id=tournament_id))

    if tournament.participants.count() >= tournament.max_participants:
        flash('Tournament is full.', 'danger')
        return redirect(url_for('tournament.detail', tournament_id=tournament_id))

    # Check entry fee
    if tournament.entry_fee > 0 and current_user.coins < tournament.entry_fee:
        flash('Not enough coins for entry fee.', 'danger')
        return redirect(url_for('tournament.detail', tournament_id=tournament_id))

    if tournament.entry_fee > 0:
        current_user.coins -= tournament.entry_fee

    participant = TournamentParticipant(
        tournament_id=tournament.id,
        user_id=current_user.id,
        seed=tournament.participants.count() + 1
    )
    db.session.add(participant)
    db.session.commit()

    flash(f'Registered for {tournament.name}!', 'success')
    return redirect(url_for('tournament.detail', tournament_id=tournament_id))


@tournament_bp.route('/<int:tournament_id>/history')
def history(tournament_id):
    """Tournament history"""
    tournament = Tournament.query.get_or_404(tournament_id)
    records = TournamentHistory.query.filter_by(
        tournament_id=tournament.id
    ).order_by(TournamentHistory.placement).all()

    return render_template('tournament/history.html', tournament=tournament, records=records)


# API endpoints
@tournament_bp.route('/api/list')
def api_list():
    """API: List tournaments"""
    status = request.args.get('status', 'all')
    region = request.args.get('region', 'global')
    page = request.args.get('page', 1, type=int)

    query = Tournament.query
    if status != 'all':
        query = query.filter_by(status=status)
    if region != 'global':
        query = query.filter_by(region=region)

    tournaments = query.order_by(Tournament.start_time.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return jsonify({
        'tournaments': [t.to_dict() for t in tournaments.items],
        'total': tournaments.total,
        'pages': tournaments.pages
    })


@tournament_bp.route('/api/<int:tournament_id>/participants')
def api_participants(tournament_id):
    """API: Tournament participants"""
    tournament = Tournament.query.get_or_404(tournament_id)
    participants = tournament.participants.all()
    return jsonify({
        'participants': [
            {
                'user': p.user.to_dict() if p.user else None,
                'seed': p.seed,
                'wins': p.wins,
                'losses': p.losses,
                'score': p.score,
                'eliminated': p.eliminated
            }
            for p in participants
        ]
    })
