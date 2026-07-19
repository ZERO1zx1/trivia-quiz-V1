"""Admin Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from app.extensions import db
from app.utils.admin import admin_required
from app.models.user import User
from app.models.question import Category, Question, Answer
from app.models.economy import Transaction
from app.models.shop import ShopItem
from app.models.achievement import Achievement
from app.models.notification import Notification
from app.models.room import Room  # Missing import added
from app.models.user_question import UserQuestion  # Added for user-questions route
from app.utils.ai import generate_trivia_question

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@admin_required
def before_request():
    pass  # Protect all admin routes

# Dashboard – single endpoint
@admin_bp.route('/')
def dashboard():
    stats = {
        'users': User.query.count(),
        'questions': Question.query.count(),
        'categories': Category.query.count(),
        'active_rooms': Room.query.filter_by(status='waiting').count()
    }
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users)

# ==================== Users ====================
@admin_bp.route('/users')
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.id.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'Admin status updated for {user.username}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/toggle-ban', methods=['POST'])
def toggle_ban(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = not user.is_banned
    db.session.commit()
    flash(f'Ban status updated for {user.username}', 'success')
    return redirect(url_for('admin.users'))

# ==================== Questions ====================
@admin_bp.route('/questions')
def questions():
    page = request.args.get('page', 1, type=int)
    questions = Question.query.order_by(Question.id.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/questions.html', questions=questions)

@admin_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted.', 'success')
    return redirect(url_for('admin.questions'))

@admin_bp.route('/questions/ai-generate', methods=['POST'])
def ai_generate():
    category_name = request.form.get('category', 'General Knowledge')
    difficulty = request.form.get('difficulty', 'medium')
    count = int(request.form.get('count', 1))
    cat = Category.query.filter_by(name=category_name).first()
    if not cat:
        cat = Category(name=category_name, slug=category_name.lower().replace(' ', '-'))
        db.session.add(cat)
        db.session.commit()

    generated = 0
    for _ in range(count):
        result = generate_trivia_question(category_name, difficulty)
        if not result: continue
        q = Question(question_text=result['question'], difficulty=difficulty, category_id=cat.id)
        db.session.add(q)
        db.session.flush()
        db.session.add(Answer(question_id=q.id, answer_text=result['correct_answer'], is_correct=True))
        for w in result['wrong_answers']:
            db.session.add(Answer(question_id=q.id, answer_text=w, is_correct=False))
        generated += 1
    db.session.commit()
    flash(f'{generated} questions generated with AI.', 'success')
    return redirect(url_for('admin.questions'))

# ==================== Categories ====================
@admin_bp.route('/categories')
def categories():
    cats = Category.query.all()
    return render_template('admin/categories.html', categories=cats)

# ==================== Shop ====================
@admin_bp.route('/shop')
def shop_items():
    items = ShopItem.query.all()
    return render_template('admin/shop.html', items=items)

# ==================== Achievements ====================
@admin_bp.route('/achievements')
def achievements():
    achievements = Achievement.query.all()
    return render_template('admin/achievements.html', achievements=achievements)

# ==================== Notifications ====================
@admin_bp.route('/notifications')
def notifications():
    notifs = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    return render_template('admin/notifications.html', notifications=notifs)

# ==================== User Submitted Questions ====================
@admin_bp.route('/user-questions')
def user_questions():
    questions = UserQuestion.query.order_by(UserQuestion.created_at.desc()).all()
    return render_template('admin/user_questions.html', questions=questions)

@admin_bp.route('/user-questions/<int:qid>/approve', methods=['POST'])
def approve_question(qid):
    uq = UserQuestion.query.get_or_404(qid)
    q = Question(
        question_text=uq.question_text,
        difficulty=uq.difficulty,
        category_id=uq.category_id,
        is_active=True
    )
    db.session.add(q)
    db.session.flush()
    db.session.add(Answer(question_id=q.id, answer_text=uq.correct_answer, is_correct=True))
    db.session.add(Answer(question_id=q.id, answer_text=uq.wrong_answer1, is_correct=False))
    db.session.add(Answer(question_id=q.id, answer_text=uq.wrong_answer2, is_correct=False))
    db.session.add(Answer(question_id=q.id, answer_text=uq.wrong_answer3, is_correct=False))
    uq.status = 'approved'
    db.session.commit()
    flash('Question approved and added to the pool!', 'success')
    return redirect(url_for('admin.user_questions'))

@admin_bp.route('/user-questions/<int:qid>/reject', methods=['POST'])
def reject_question(qid):
    uq = UserQuestion.query.get_or_404(qid)
    uq.status = 'rejected'
    db.session.commit()
    flash('Question rejected.', 'info')
    return redirect(url_for('admin.user_questions'))