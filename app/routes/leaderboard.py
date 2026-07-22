"""Leaderboard Routes"""
from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func
from app.extensions import db
from app.models.economy import LeaderboardEntry
from app.models.user import User

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    period = request.args.get('period', 'alltime')
    valid_periods = ['daily', 'weekly', 'monthly', 'alltime']
    if period not in valid_periods:
        period = 'alltime'

    query = LeaderboardEntry.query.filter_by(period=period).order_by(LeaderboardEntry.score.desc())
    entries = query.paginate(page=page, per_page=25, error_out=False)

    return render_template('leaderboard/index.html', entries=entries, period=period, valid_periods=valid_periods)

@leaderboard_bp.route('/api/<period>')
def api_leaderboard(period):
    if period not in ['daily', 'weekly', 'monthly', 'alltime']:
        return jsonify({'error': 'Invalid period'}), 400
    limit = request.args.get('limit', 100, type=int)
    entries = LeaderboardEntry.query.filter_by(period=period).order_by(
        LeaderboardEntry.score.desc()).limit(limit).all()
    data = []
    for i, entry in enumerate(entries, 1):
        data.append({
            'rank': i,
            'username': entry.user.username if entry.user else 'Unknown',
            'avatar': entry.user.avatar_url if entry.user else None,
            'level': entry.user.level if entry.user else 1,
            'score': entry.score,
            'wins': entry.wins,
            'games_played': entry.games_played,
            'accuracy': round(entry.accuracy, 1)
        })
    return jsonify(data)
