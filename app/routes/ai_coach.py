"""AI Coach Routes - Хувийн дасгалжуулагч"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.utils.ai_coach import generate_coach_advice, get_user_weak_categories

ai_coach_bp = Blueprint('ai_coach', __name__)


@ai_coach_bp.route('/api/coach/advice')
@login_required
def get_advice():
    """Get AI-powered coaching advice for the current user."""
    advice = generate_coach_advice(current_user.id)
    if not advice:
        return jsonify({'error': 'Could not generate advice'}), 500
    return jsonify({'advice': advice})


@ai_coach_bp.route('/api/coach/categories')
@login_required
def get_category_stats():
    """Get user's category performance breakdown."""
    stats = get_user_weak_categories(current_user.id)
    if not stats:
        return jsonify({'categories': [], 'weakest': None, 'strongest': None})

    categories = []
    for cat_name, cat_stats in stats.items():
        if isinstance(cat_stats, dict):
            total = cat_stats.get('total', 0)
            correct = cat_stats.get('correct', 0)
            accuracy = (correct / total * 100) if total > 0 else 0
            categories.append({
                'name': cat_name,
                'total': total,
                'correct': correct,
                'accuracy': round(accuracy, 1)
            })

    if categories:
        categories.sort(key=lambda x: x['accuracy'])
        weakest = categories[0]
        strongest = categories[-1]
    else:
        weakest = None
        strongest = None

    return jsonify({
        'categories': categories,
        'weakest': weakest,
        'strongest': strongest
    })
