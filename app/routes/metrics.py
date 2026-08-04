"""Prometheus Metrics Exporter for TriviaVerse"""
from flask import Blueprint, Response

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/metrics')
def prometheus_metrics():
    """Expose Prometheus metrics endpoint."""
    from app.models.user import User
    from app.models.question import Question
    from app.models.room import Room
    from app.extensions import db

    lines = []
    lines.append('# HELP triviaverse_users_total Total registered users')
    lines.append('# TYPE triviaverse_users_total gauge')
    try:
        total_users = User.query.count()
        lines.append(f'triviaverse_users_total {total_users}')
    except:
        lines.append('triviaverse_users_total 0')

    lines.append('# HELP triviaverse_questions_total Total questions in database')
    lines.append('# TYPE triviaverse_questions_total gauge')
    try:
        total_questions = Question.query.count()
        lines.append(f'triviaverse_questions_total {total_questions}')
    except:
        lines.append('triviaverse_questions_total 0')

    lines.append('# HELP triviaverse_active_rooms Total active rooms')
    lines.append('# TYPE triviaverse_active_rooms gauge')
    try:
        active_rooms = Room.query.filter_by(status='waiting').count()
        lines.append(f'triviaverse_active_rooms {active_rooms}')
    except:
        lines.append('triviaverse_active_rooms 0')

    lines.append('# HELP triviaverse_app_info Application info')
    lines.append('# TYPE triviaverse_app_info gauge')
    lines.append('triviaverse_app_info{version="3.0"} 1')

    return Response('\n'.join(lines), mimetype='text/plain; version=0.0.4; charset=utf-8')
