"""Replay System Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.replay import Replay, ReplayEvent, ReplayLike
from datetime import datetime
import json

replay_bp = Blueprint('replay', __name__, url_prefix='/replay')


@replay_bp.route('/')
def index():
    """Replay browser page"""
    page = request.args.get('page', 1, type=int)
    game_mode = request.args.get('mode', 'all')

    query = Replay.query.filter_by(is_public=True)
    if game_mode != 'all':
        query = query.filter_by(game_mode=game_mode)

    replays = query.order_by(Replay.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('replay/index.html', replays=replays)


@replay_bp.route('/watch/<int:replay_id>')
def watch(replay_id):
    """Watch a replay"""
    replay = Replay.query.get_or_404(replay_id)

    if not replay.is_public and (not current_user.is_authenticated or
                                  current_user.id != replay.user_id):
        flash('This replay is private.', 'warning')
        return redirect(url_for('replay.index'))

    # Increment view count
    replay.view_count += 1
    db.session.commit()

    events = replay.get_events()
    liked = False
    if current_user.is_authenticated:
        liked = ReplayLike.query.filter_by(
            replay_id=replay.id, user_id=current_user.id
        ).first() is not None

    return render_template('replay/watch.html', replay=replay, events=events, liked=liked)


@replay_bp.route('/create', methods=['POST'])
@login_required
def create_replay():
    """Save a replay from a match"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    replay = Replay(
        user_id=current_user.id,
        match_id=data.get('match_id'),
        room_id=data.get('room_id'),
        title=data.get('title', 'Untitled Replay'),
        game_mode=data.get('game_mode', 'classic'),
        category=data.get('category', ''),
        difficulty=data.get('difficulty', 'mixed'),
        duration_seconds=data.get('duration', 0),
        result=data.get('result', ''),
        player_stats=json.dumps(data.get('stats', {})),
        events_data=json.dumps(data.get('events', [])),
        is_public=data.get('is_public', True)
    )
    db.session.add(replay)
    db.session.commit()

    # Save events as separate records
    for event_data in data.get('events', []):
        event = ReplayEvent(
            replay_id=replay.id,
            timestamp_ms=event_data.get('timestamp_ms', 0),
            event_type=event_data.get('event_type', ''),
            player_id=event_data.get('player_id'),
            data=json.dumps(event_data.get('data', {}))
        )
        db.session.add(event)

    db.session.commit()

    return jsonify({'success': True, 'replay_id': replay.id})


@replay_bp.route('/<int:replay_id>/like', methods=['POST'])
@login_required
def like(replay_id):
    """Like a replay"""
    replay = Replay.query.get_or_404(replay_id)

    existing = ReplayLike.query.filter_by(
        replay_id=replay_id, user_id=current_user.id
    ).first()

    if existing:
        db.session.delete(existing)
        replay.like_count = max(0, replay.like_count - 1)
        db.session.commit()
        return jsonify({'liked': False, 'count': replay.like_count})

    like = ReplayLike(replay_id=replay_id, user_id=current_user.id)
    replay.like_count += 1
    db.session.add(like)
    db.session.commit()

    return jsonify({'liked': True, 'count': replay.like_count})


@replay_bp.route('/<int:replay_id>/share', methods=['POST'])
@login_required
def share(replay_id):
    """Share a replay"""
    replay = Replay.query.get_or_404(replay_id)
    replay.share_count += 1
    db.session.commit()
    return jsonify({'success': True, 'share_count': replay.share_count})


@replay_bp.route('/<int:replay_id>/toggle-privacy', methods=['POST'])
@login_required
def toggle_privacy(replay_id):
    """Toggle replay privacy"""
    replay = Replay.query.get_or_404(replay_id)

    if replay.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    replay.is_public = not replay.is_public
    db.session.commit()

    return jsonify({'success': True, 'is_public': replay.is_public})


@replay_bp.route('/my-replays')
@login_required
def my_replays():
    """View user's own replays"""
    page = request.args.get('page', 1, type=int)
    replays = Replay.query.filter_by(
        user_id=current_user.id
    ).order_by(Replay.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('replay/my_replays.html', replays=replays)


# API endpoints
@replay_bp.route('/api/popular')
def api_popular():
    """API: Get popular replays"""
    replays = Replay.query.filter_by(is_public=True).order_by(
        Replay.like_count.desc()
    ).limit(10).all()

    return jsonify({
        'replays': [r.to_dict() for r in replays]
    })


@replay_bp.route('/api/<int:replay_id>/events')
def api_events(replay_id):
    """API: Get replay events"""
    replay = Replay.query.get_or_404(replay_id)
    events = ReplayEvent.query.filter_by(replay_id=replay_id).order_by(
        ReplayEvent.timestamp_ms
    ).all()

    return jsonify({
        'events': [e.to_dict() for e in events]
    })
