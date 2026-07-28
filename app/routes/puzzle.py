"""Puzzle Mode Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.puzzle import Puzzle, PuzzleAttempt, PuzzleLeaderboardEntry
from datetime import datetime

puzzle_bp = Blueprint('puzzle', __name__, url_prefix='/puzzle')


@puzzle_bp.route('/')
def index():
    """Puzzle mode main page"""
    daily = Puzzle.query.filter_by(is_daily=True, is_active=True).first()
    puzzles = Puzzle.query.filter_by(is_daily=False, is_active=True).order_by(
        Puzzle.difficulty
    ).all()

    # Get user's progress
    attempts = None
    if current_user.is_authenticated:
        attempts = PuzzleAttempt.query.filter_by(
            user_id=current_user.id
        ).order_by(PuzzleAttempt.created_at.desc()).limit(10).all()

    return render_template('puzzle/index.html', daily=daily, puzzles=puzzles, attempts=attempts)


@puzzle_bp.route('/daily')
def daily():
    """Daily puzzle page"""
    daily = Puzzle.query.filter_by(is_daily=True, is_active=True).first()

    if not daily:
        flash('No daily puzzle available today.', 'info')
        return redirect(url_for('puzzle.index'))

    attempt = None
    if current_user.is_authenticated:
        attempt = PuzzleAttempt.query.filter_by(
            puzzle_id=daily.id, user_id=current_user.id,
            status='in_progress'
        ).first()

    return render_template('puzzle/daily.html', puzzle=daily, attempt=attempt)


@puzzle_bp.route('/<int:puzzle_id>/play')
@login_required
def play(puzzle_id):
    """Play a puzzle"""
    puzzle = Puzzle.query.get_or_404(puzzle_id)

    # Create attempt
    attempt = PuzzleAttempt(
        puzzle_id=puzzle.id,
        user_id=current_user.id,
        status='in_progress'
    )
    db.session.add(attempt)
    db.session.commit()

    return render_template('puzzle/play.html', puzzle=puzzle, attempt=attempt)


@puzzle_bp.route('/<int:puzzle_id>/submit', methods=['POST'])
@login_required
def submit_puzzle(puzzle_id):
    """Submit puzzle solution"""
    puzzle = Puzzle.query.get_or_404(puzzle_id)
    data = request.get_json()

    attempt = PuzzleAttempt.query.filter_by(
        puzzle_id=puzzle.id, user_id=current_user.id, status='in_progress'
    ).first_or_404()

    is_correct = data.get('correct', False)
    completion_time = data.get('completion_time', 0)
    moves = data.get('moves', 0)
    hints = data.get('hints_used', 0)

    if is_correct:
        attempt.status = 'completed'
        attempt.completion_time_seconds = completion_time
        attempt.moves_count = moves
        attempt.hints_used = hints
        attempt.end_time = datetime.utcnow()

        # Calculate score (fewer moves, fewer hints, faster = higher score)
        base_score = 1000
        time_penalty = min(completion_time * 2, 500)
        hint_penalty = hints * 50
        move_penalty = min(moves * 5, 300)
        attempt.score = max(100, base_score - time_penalty - hint_penalty - move_penalty)
        attempt.is_perfect = (hints == 0 and attempt.score >= 800)

        # Grant rewards
        current_user.coins += puzzle.reward_coins
        current_user.add_xp(puzzle.reward_xp)

        # Update leaderboard
        entry = PuzzleLeaderboardEntry(
            puzzle_id=puzzle.id,
            user_id=current_user.id,
            completion_time=completion_time,
            score=attempt.score,
            hints_used=hints
        )
        db.session.add(entry)
    else:
        attempt.status = 'failed'
        attempt.end_time = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'success': True,
        'score': attempt.score,
        'is_perfect': attempt.is_perfect,
        'coins_earned': puzzle.reward_coins if is_correct else 0,
        'xp_earned': puzzle.reward_xp if is_correct else 0
    })


@puzzle_bp.route('/<int:puzzle_id>/leaderboard')
def leaderboard(puzzle_id):
    """Puzzle leaderboard"""
    puzzle = Puzzle.query.get_or_404(puzzle_id)
    entries = PuzzleLeaderboardEntry.query.filter_by(
        puzzle_id=puzzle.id
    ).order_by(PuzzleLeaderboardEntry.score.desc()).limit(50).all()

    return render_template('puzzle/leaderboard.html', puzzle=puzzle, entries=entries)


@puzzle_bp.route('/<int:attempt_id>/hint', methods=['POST'])
@login_required
def get_hint(attempt_id):
    """Get a hint for a puzzle"""
    attempt = PuzzleAttempt.query.get_or_404(attempt_id)

    if attempt.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    attempt.hints_used += 1
    attempt.score = max(0, attempt.score - 50)
    db.session.commit()

    # Return a hint (simplified)
    puzzle = attempt.puzzle
    return jsonify({
        'success': True,
        'hint': puzzle.data,  # In production, return partial data
        'hints_used': attempt.hints_used,
        'score_penalty': 50
    })


# API endpoints
@puzzle_bp.route('/api/daily')
def api_daily():
    """API: Get today's daily puzzle"""
    daily = Puzzle.query.filter_by(is_daily=True, is_active=True).first()
    if not daily:
        return jsonify({'error': 'No daily puzzle'}), 404

    data = daily.to_dict()
    # Don't include solution in API response
    return jsonify(data)


@puzzle_bp.route('/api/<int:puzzle_id>/attempts')
@login_required
def api_attempts(puzzle_id):
    """API: Get user's attempts for a puzzle"""
    attempts = PuzzleAttempt.query.filter_by(
        puzzle_id=puzzle_id, user_id=current_user.id
    ).order_by(PuzzleAttempt.created_at.desc()).all()

    return jsonify({
        'attempts': [
            {
                'id': a.id,
                'status': a.status,
                'score': a.score,
                'completion_time': a.completion_time_seconds,
                'hints_used': a.hints_used,
                'is_perfect': a.is_perfect,
                'created_at': a.created_at.isoformat()
            }
            for a in attempts
        ]
    })
