"""Quiz V2 Routes — Modern standalone quiz experience with Supabase integration."""
import json
import os
import requests
from datetime import datetime, timezone
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.question import Category, Question, Answer
from app.utils.i18n import get_translations

quiz_v2_bp = Blueprint('quiz_v2', __name__)

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://rqalizeohjpwtvepltqe.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')


def _supabase_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }


def _supabase_get(table, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        r = requests.get(url, headers=_supabase_headers(), params=params or {}, timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def _supabase_insert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        r = requests.post(url, headers=_supabase_headers(), json=data, timeout=10)
        return r.json() if r.status_code in (200, 201) else None
    except Exception:
        return None


def _supabase_update(table, id_col, id_val, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{id_col}=eq.{id_val}"
    try:
        r = requests.patch(url, headers=_supabase_headers(), json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


@quiz_v2_bp.route('/v2')
def v2_home():
    """Modern landing page for Quiz V2."""
    lang = session.get('language', 'mn')
    t = get_translations(lang)
    cats = Category.query.filter_by(is_active=True).all()
    return render_template('quiz_v2/home.html',
                           lang=lang, t=t, categories=cats)


@quiz_v2_bp.route('/v2/categories')
def v2_categories():
    """Category selection screen."""
    lang = session.get('language', 'mn')
    t = get_translations(lang)
    cats = Category.query.filter_by(is_active=True).all()
    cat_data = []
    for c in cats:
        q_count = Question.query.filter_by(category_id=c.id, is_active=True).count()
        cat_data.append({
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'description': c.description or '',
            'icon': c.icon or '📚',
            'color': c.color or '#6366f1',
            'question_count': q_count
        })
    return render_template('quiz_v2/categories.html',
                           lang=lang, t=t, categories=cat_data)


@quiz_v2_bp.route('/v2/api/categories')
def v2_api_categories():
    """API endpoint for categories."""
    cats = Category.query.filter_by(is_active=True).all()
    result = []
    for c in cats:
        q_count = Question.query.filter_by(category_id=c.id, is_active=True).count()
        result.append({
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'description': c.description or '',
            'icon': c.icon or '📚',
            'color': c.color or '#6366f1',
            'question_count': q_count
        })
    return jsonify(result)


@quiz_v2_bp.route('/v2/api/questions')
def v2_api_questions():
    """API endpoint to get questions for a quiz session."""
    category_id = request.args.get('category_id', type=int)
    difficulty = request.args.get('difficulty', 'mixed')
    limit = request.args.get('limit', 10, type=int)

    query = Question.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if difficulty != 'mixed':
        query = query.filter_by(difficulty=difficulty)

    questions = query.order_by(db.func.random()).limit(limit).all()
    result = []
    for q in questions:
        answers_list = [{'id': a.id, 'text': a.answer_text} for a in q.answers]
        result.append({
            'id': q.id,
            'question_text': q.question_text,
            'question_type': q.question_type or 'text',
            'image_url': q.image_url,
            'difficulty': q.difficulty or 'medium',
            'category': q.category.name if q.category else 'General',
            'category_id': q.category_id,
            'explanation': q.explanation or '',
            'answers': answers_list,
            'correct_answer_index': None  # Not sent to client
        })
    return jsonify(result)


@quiz_v2_bp.route('/v2/api/check_answer', methods=['POST'])
def v2_check_answer():
    """Check an answer and return result."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    question_id = data.get('question_id')
    answer_id = data.get('answer_id')
    time_taken = data.get('time_taken', 0)

    if not question_id or answer_id is None:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        question_id = int(question_id)
        answer_id = int(answer_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Question and answer IDs must be integers'}), 400

    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    correct_answer = question.get_correct_answer()
    if not correct_answer:
        return jsonify({'error': 'No correct answer'}), 500

    is_correct = (answer_id == correct_answer.id)

    return jsonify({
        'correct': is_correct,
        'correct_answer_id': correct_answer.id,
        'explanation': question.explanation or ''
    })


@quiz_v2_bp.route('/v2/api/save_score', methods=['POST'])
def v2_save_score():
    """Save quiz score to Supabase."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    user_id = current_user.id if current_user.is_authenticated else None
    category_id = data.get('category_id')
    total = data.get('total_questions', 0)
    correct = data.get('correct_answers', 0)
    wrong = data.get('wrong_answers', 0)
    score = data.get('score', 0)
    max_streak = data.get('max_streak', 0)
    time_spent = data.get('time_spent_seconds', 0)
    difficulty = data.get('difficulty', 'mixed')
    timer_mode = data.get('timer_mode', 'off')

    # Save session
    session_data = {
        'user_id': user_id,
        'category_id': category_id,
        'total_questions': total,
        'correct_answers': correct,
        'wrong_answers': wrong,
        'score': score,
        'max_streak': max_streak,
        'time_spent_seconds': time_spent,
        'difficulty': difficulty,
        'timer_mode': timer_mode,
        'completed_at': datetime.now(timezone.utc).isoformat()
    }

    try:
        _supabase_insert('quiz_sessions', session_data)
    except Exception:
        pass  # Log but don't fail the response

    # Update best score if authenticated
    if user_id:
        _update_best_score(user_id, category_id, score, total, correct, max_streak)

    return jsonify({
        'success': True,
        'score': score,
        'correct': correct,
        'total': total
    })


def _update_best_score(user_id, category_id, score, total, correct, max_streak):
    """Update or create best score record in Supabase."""
    accuracy = (correct / total * 100) if total > 0 else 0

    # Check existing best score
    try:
        existing = _supabase_get('quiz_best_scores',
                                 params={'user_id': f'eq.{user_id}',
                                         'category_id': f'eq.{category_id}'})
        if existing and len(existing) > 0:
            record = existing[0]
            record_id = record['id']
            new_best_score = max(record['best_score'], score)
            new_total_games = record['total_games'] + 1
            new_total_correct = record['total_correct'] + correct
            new_avg = (new_total_correct / new_total_games * 100) if new_total_games > 0 else 0
            new_best_streak = max(record['best_max_streak'], max_streak)

            _supabase_update('quiz_best_scores', 'id', record_id, {
                'best_score': new_best_score,
                'best_accuracy': max(record['best_accuracy'], accuracy),
                'best_max_streak': new_best_streak,
                'total_games': new_total_games,
                'total_correct': new_total_correct,
                'avg_accuracy': new_avg,
                'last_played_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            })
        else:
            _supabase_insert('quiz_best_scores', {
                'user_id': user_id,
                'category_id': category_id,
                'best_score': score,
                'best_accuracy': accuracy,
                'best_max_streak': max_streak,
                'total_games': 1,
                'total_correct': correct,
                'avg_accuracy': accuracy,
                'last_played_at': datetime.now(timezone.utc).isoformat()
            })
    except Exception:
        pass


@quiz_v2_bp.route('/v2/api/best_scores')
def v2_best_scores():
    """Get best scores for the current user."""
    if not current_user.is_authenticated:
        return jsonify([])

    scores = _supabase_get('quiz_best_scores',
                           params={'user_id': f'eq.{current_user.id}'})
    return jsonify(scores or [])


@quiz_v2_bp.route('/v2/api/user_settings', methods=['POST'])
def v2_save_settings():
    """Save user language/theme settings."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    lang = data.get('language', session.get('language', 'en'))
    theme = data.get('theme', 'light')

    session['language'] = lang
    session['theme'] = theme

    user_id = current_user.id if current_user.is_authenticated else None
    if user_id:
        try:
            existing = _supabase_get('quiz_user_settings',
                                     params={'user_id': f'eq.{user_id}'})
            if existing and len(existing) > 0:
                record = existing[0]
                _supabase_update('quiz_user_settings', 'id', record['id'], {
                    'language': lang,
                    'theme': theme,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })
            else:
                _supabase_insert('quiz_user_settings', {
                    'user_id': user_id,
                    'language': lang,
                    'theme': theme
                })
        except Exception:
            pass

    return jsonify({'success': True, 'language': lang, 'theme': theme})


@quiz_v2_bp.route('/v2/api/user_settings')
def v2_get_settings():
    """Get user language/theme settings."""
    if current_user.is_authenticated:
        try:
            existing = _supabase_get('quiz_user_settings',
                                     params={'user_id': f'eq.{current_user.id}'})
            if existing and len(existing) > 0:
                s = existing[0]
                session['language'] = s.get('language', 'mn')
                session['theme'] = s.get('theme', 'light')
                return jsonify(s)
        except Exception:
            pass

    return jsonify({
        'language': session.get('language', 'mn'),
        'theme': session.get('theme', 'light')
    })


@quiz_v2_bp.route('/v2/play/<int:category_id>')
def v2_play(category_id):
    """Quiz gameplay screen."""
    lang = session.get('language', 'mn')
    t = get_translations(lang)
    theme = session.get('theme', 'light')
    cat = Category.query.get(category_id)
    q_count = Question.query.filter_by(category_id=category_id, is_active=True).count()

    if not cat:
        return redirect(url_for('quiz_v2.v2_categories'))

    # Default settings
    timer_mode = request.args.get('timer', 'off')
    difficulty = request.args.get('difficulty', 'mixed')
    question_count = request.args.get('limit', 10, type=int)

    return render_template('quiz_v2/play.html',
                           lang=lang, t=t, theme=theme,
                           category=cat, category_id=category_id,
                           question_count=q_count,
                           timer_mode=timer_mode,
                           difficulty=difficulty,
                           limit=question_count)


@quiz_v2_bp.route('/v2/language/<lang>')
def v2_set_language(lang):
    """Set language."""
    if lang in ('mn', 'en'):
        session['language'] = lang
    return redirect(request.referrer or url_for('quiz_v2.v2_home'))


@quiz_v2_bp.route('/v2/theme/<theme>')
def v2_set_theme(theme):
    """Set theme."""
    if theme in ('light', 'dark'):
        session['theme'] = theme
    return redirect(request.referrer or url_for('quiz_v2.v2_home'))
