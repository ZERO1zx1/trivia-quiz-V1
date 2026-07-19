from flask import Blueprint, render_template, jsonify
from app.models.question import Category, Question
from app.models.room import Room
from app.models.economy import LeaderboardEntry
from app.models.user import User

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    categories = Category.query.filter_by(is_active=True).all()
    public_rooms = Room.query.filter_by(is_private=False, status='waiting').limit(10).all()
    top_players = LeaderboardEntry.query.filter_by(period='alltime')\
        .order_by(LeaderboardEntry.score.desc()).limit(5).all()
    total_players = User.query.count()
    return render_template('home/index.html',
                         categories=categories,
                         public_rooms=public_rooms,
                         top_players=top_players,
                         total_players=total_players)

@home_bp.route('/about')
def about():
    return render_template('home/about.html')

@home_bp.route('/api/stats')
def api_stats():
    stats = {
        'total_players': User.query.count(),
        'total_questions': Question.query.filter_by(is_active=True).count(),
        'total_categories': Category.query.filter_by(is_active=True).count(),
        'active_rooms': Room.query.filter_by(status='waiting').count()
    }
    return jsonify(stats)