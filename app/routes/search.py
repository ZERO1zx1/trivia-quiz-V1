"""Search Routes (Chapter 16)"""
from flask import Blueprint, render_template, request
from flask_login import login_required
from app.utils.search import search_questions, search_users, search_rooms

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
@login_required
def search_page():
    """Full-text search page for questions, users, and rooms."""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    limit = request.args.get('limit', 20, type=int)

    results = {
        'questions': [],
        'users': [],
        'rooms': []
    }

    if query:
        if search_type in ('all', 'questions'):
            questions = search_questions(query, limit=limit)
            results['questions'] = [
                {
                    'id': q.id,
                    'text': q.question_text[:200],
                    'category': q.category.name if q.category else None,
                    'difficulty': q.difficulty,
                    'times_used': q.times_used,
                    'correct_rate': round(q.correct_rate, 1) if q.correct_rate else 0
                }
                for q in questions
            ]

        if search_type in ('all', 'users'):
            users = search_users(query, limit=limit)
            results['users'] = [
                {
                    'id': u.id,
                    'username': u.username,
                    'display_name': u.display_name,
                    'avatar_url': u.avatar_url,
                    'level': u.level,
                    'accuracy': round(u.accuracy, 1) if u.accuracy else 0,
                    'games_played': u.games_played
                }
                for u in users
            ]

        if search_type in ('all', 'rooms'):
            rooms = search_rooms(query, limit=limit)
            results['rooms'] = [
                {
                    'id': r.id,
                    'name': r.name,
                    'code': r.code,
                    'status': r.status,
                    'player_count': r.max_players,
                    'difficulty': r.difficulty
                }
                for r in rooms
            ]

    return render_template('search/search.html', query=query, results=results, search_type=search_type)
