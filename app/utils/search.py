"""Full-Text Search Utilities (Chapter 16)
Supports both database-level search (ILIKE) and optional Elasticsearch integration.
"""
from app.extensions import db
from app.models.user import User
from app.models.question import Question
from app.models.room import Room
from flask import current_app


def search_questions(query_text, category_id=None, difficulty=None, limit=20):
    """Search questions by text using database ILIKE."""
    q = Question.query.filter_by(is_active=True)
    if query_text:
        q = q.filter(Question.question_text.ilike(f'%{query_text}%'))
    if category_id:
        q = q.filter_by(category_id=category_id)
    if difficulty:
        q = q.filter_by(difficulty=difficulty)
    return q.order_by(db.desc(Question.id)).limit(limit).all()


def search_users(query_text, limit=20):
    """Search users by username or display name."""
    q = User.query
    if query_text:
        q = q.filter(
            db.or_(
                User.username.ilike(f'%{query_text}%'),
                User.display_name.ilike(f'%{query_text}%')
            )
        )
    return q.order_by(User.username).limit(limit).all()


def search_rooms(query_text, status='waiting', limit=20):
    """Search rooms by name."""
    q = Room.query.filter_by(status=status)
    if query_text:
        q = q.filter(Room.name.ilike(f'%{query_text}%'))
    return q.order_by(db.desc(Room.created_at)).limit(limit).all()


def get_elasticsearch_client():
    """Get Elasticsearch client if available."""
    try:
        from elasticsearch import Elasticsearch
        es_url = current_app.config.get('ELASTICSEARCH_URL', 'http://localhost:9200')
        es = Elasticsearch([es_url], timeout=10)
        if es.ping():
            return es
    except Exception:
        pass
    return None
