"""Event System Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.event import GameEvent, EventReward, EventParticipant
from datetime import datetime

event_bp = Blueprint('event', __name__, url_prefix='/event')


@event_bp.route('/')
def index():
    """Active events page"""
    active_events = GameEvent.query.filter_by(
        status='active'
    ).order_by(GameEvent.end_date).all()

    upcoming_events = GameEvent.query.filter_by(
        status='upcoming'
    ).order_by(GameEvent.start_date).limit(5).all()

    return render_template('event/index.html',
                           active_events=active_events,
                           upcoming_events=upcoming_events)


@event_bp.route('/<int:event_id>')
def detail(event_id):
    """Event detail page"""
    event = GameEvent.query.get_or_404(event_id)
    rewards = event.rewards.all()

    my_participation = None
    if current_user.is_authenticated:
        my_participation = EventParticipant.query.filter_by(
            event_id=event.id, user_id=current_user.id
        ).first()

    return render_template('event/detail.html', event=event,
                           rewards=rewards, my_participation=my_participation)


@event_bp.route('/<int:event_id>/join', methods=['POST'])
@login_required
def join_event(event_id):
    """Join an event"""
    event = GameEvent.query.get_or_404(event_id)

    if event.status != 'active':
        flash('This event is not currently active.', 'warning')
        return redirect(url_for('event.detail', event_id=event_id))

    existing = EventParticipant.query.filter_by(
        event_id=event.id, user_id=current_user.id
    ).first()

    if existing:
        flash('Already participating.', 'info')
        return redirect(url_for('event.detail', event_id=event_id))

    participant = EventParticipant(
        event_id=event.id,
        user_id=current_user.id
    )
    db.session.add(participant)
    db.session.commit()

    flash(f'Joined {event.name}!', 'success')
    return redirect(url_for('event.detail', event_id=event_id))


@event_bp.route('/<int:event_id>/claim-reward/<int:reward_id>', methods=['POST'])
@login_required
def claim_reward(event_id, reward_id):
    """Claim an event reward"""
    event = GameEvent.query.get_or_404(event_id)
    reward = EventReward.query.get_or_404(reward_id)

    if reward.event_id != event.id:
        return jsonify({'error': 'Invalid reward'}), 400

    participant = EventParticipant.query.filter_by(
        event_id=event.id, user_id=current_user.id
    ).first()

    if not participant:
        return jsonify({'error': 'Not participating'}), 400

    # Check if already claimed
    import json
    claimed = json.loads(participant.rewards_claimed) if participant.rewards_claimed else []

    if reward_id in claimed:
        return jsonify({'error': 'Already claimed'}), 400

    # Check requirement
    # In production, parse reward.requirement JSON and validate

    # Grant reward
    if reward.reward_type == 'coins':
        current_user.coins += (reward.item_id or 100)
    elif reward.reward_type == 'xp':
        current_user.add_xp(reward.item_id or 50)

    claimed.append(reward_id)
    participant.rewards_claimed = json.dumps(claimed)
    db.session.commit()

    return jsonify({'success': True, 'reward': reward.name})


@event_bp.route('/<int:event_id>/leaderboard')
def leaderboard(event_id):
    """Event leaderboard"""
    event = GameEvent.query.get_or_404(event_id)
    participants = EventParticipant.query.filter_by(
        event_id=event.id
    ).order_by(EventParticipant.score.desc()).limit(100).all()

    return render_template('event/leaderboard.html', event=event, participants=participants)


# API endpoints
@event_bp.route('/api/active')
def api_active():
    """API: Get active events"""
    events = GameEvent.query.filter_by(status='active').all()
    return jsonify({
        'events': [e.to_dict() for e in events]
    })


@event_bp.route('/api/<int:event_id>/progress')
@login_required
def api_progress(event_id):
    """API: Get event progress"""
    participant = EventParticipant.query.filter_by(
        event_id=event_id, user_id=current_user.id
    ).first()

    if not participant:
        return jsonify({'error': 'Not participating'}), 404

    return jsonify({
        'score': participant.score,
        'progress': participant.progress,
        'rewards_claimed': participant.rewards_claimed
    })
