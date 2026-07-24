"""Admin Routes (Chapters 5, 7, 15)"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user
from app.extensions import db
from app.utils.admin import admin_required, role_required
from app.models.user import User
from app.models.question import Category, Question, Answer
from app.models.economy import Transaction
from app.models.shop import ShopItem, UserInventory
from app.models.achievement import Achievement
from app.models.notification import Notification
from app.models.room import Room
from app.models.user_question import UserQuestion
from app.models.box import Box, UserBox
from app.utils.ai import generate_trivia_question
import random
import requests
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
@admin_required
def before_request():
    pass  # Protect all admin routes


# ==================== Dashboard ====================
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
    if user.id == current_user.id:
        flash('You cannot ban yourself!', 'danger')
        return redirect(url_for('admin.users'))
    user.is_banned = not user.is_banned
    db.session.commit()
    flash(f'Ban status updated for {user.username}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/ban-sync', methods=['POST'])
@role_required('owner', 'admin')
def ban_sync(user_id):
    user = User.query.get_or_404(user_id)
    if user.discord_account:
        try:
            requests.post(
                f"{current_app.config['API_BASE_URL']}/discord/ban",
                json={"discord_id": user.discord_account.discord_id},
                timeout=5
            )
        except Exception as e:
            current_app.logger.error(f"Discord ban sync failed: {e}")
    user.is_banned = True
    db.session.commit()
    flash(f'{user.username} has been banned on Discord and website.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/change-role', methods=['POST'])
@role_required('owner')
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    user.role = request.form.get('role', 'user')
    db.session.commit()
    flash(f'Role updated to {user.role} for {user.username}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-premium', methods=['POST'])
@role_required('owner', 'admin')
def toggle_premium(user_id):
    user = User.query.get_or_404(user_id)
    user.is_premium = not user.is_premium
    if user.is_premium:
        user.premium_expiry = datetime.utcnow() + timedelta(days=30)
    else:
        user.premium_expiry = None
    db.session.commit()
    flash(f'Premium status updated for {user.username}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/reset-xp', methods=['POST'])
@role_required('owner', 'admin')
def reset_xp(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot reset your own XP!', 'danger')
        return redirect(url_for('admin.users'))
    user.xp = 0
    user.level = 1
    db.session.commit()
    flash(f'XP and level reset for {user.username}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/give-coins', methods=['POST'])
@role_required('admin', 'owner')
def give_coins(user_id):
    user = User.query.get_or_404(user_id)
    amount = int(request.form.get('amount', 0))
    user.add_coins(amount, 'Admin grant')
    db.session.commit()
    flash(f'Gave {amount} coins to {user.username}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/give-boxes', methods=['POST'])
@role_required('admin', 'owner')
def give_boxes(user_id):
    user = User.query.get_or_404(user_id)
    box_type = request.form.get('box_type', 'common')
    quantity = int(request.form.get('quantity', 1))
    box = Box.query.filter_by(rarity=box_type).first()
    if not box:
        flash('Box type not found.', 'danger')
        return redirect(url_for('admin.users'))
    for _ in range(quantity):
        db.session.add(UserBox(user_id=user.id, box_id=box.id, quantity=1))
    db.session.commit()
    flash(f'Gave {quantity} {box_type} boxes to {user.username}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/reset-economy', methods=['POST'])
@role_required('admin', 'owner')
def reset_economy(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot reset your own economy!', 'danger')
        return redirect(url_for('admin.users'))
    user.coins = 0
    user.xp = 0
    user.level = 1
    # Delete user's boxes
    UserBox.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    flash(f'Economy reset for {user.username}', 'success')
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

    if difficulty == 'mixed':
        difficulties = ['easy', 'medium', 'hard']

    cat = None
    if category_name:
        cat = Category.query.filter_by(name=category_name).first()
        if not cat:
            cat = Category(name=category_name, slug=category_name.lower().replace(' ', '-'))
            db.session.add(cat)
            db.session.commit()

    generated = 0
    for i in range(count):
        current_difficulty = difficulty
        if difficulty == 'mixed':
            current_difficulty = random.choice(difficulties)

        result = generate_trivia_question(category_name or 'General Knowledge', current_difficulty)
        if not result:
            current_app.logger.error(f"AI generation failed (attempt {i+1}/{count})")
            continue

        q = Question(
            question_text=result['question'],
            difficulty=current_difficulty,
            category_id=cat.id if cat else None,
            is_active=True
        )
        db.session.add(q)
        db.session.flush()
        db.session.add(Answer(question_id=q.id, answer_text=result['correct_answer'], is_correct=True))
        for w in result.get('wrong_answers', []):
            db.session.add(Answer(question_id=q.id, answer_text=w, is_correct=False))
        generated += 1

    db.session.commit()

    if generated > 0:
        flash(f'{generated} questions generated with AI!', 'success')
    else:
        flash('AI generation failed. Check the log file for details.', 'danger')
        current_app.logger.error(f"All {count} AI generation attempts failed")

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

    if uq.user and uq.user.discord_account:
        try:
            requests.post(
                f"{current_app.config['API_BASE_URL']}/discord/dm",
                json={"discord_id": uq.user.discord_account.discord_id,
                      "message": f"✅ Your question has been approved!\nQuestion: {uq.question_text[:50]}..."},
                timeout=5
            )
        except Exception as e:
            current_app.logger.error(f"Discord DM failed: {e}")

    flash('Question approved and user notified!', 'success')
    return redirect(url_for('admin.user_questions'))


@admin_bp.route('/user-questions/<int:qid>/reject', methods=['POST'])
def reject_question(qid):
    uq = UserQuestion.query.get_or_404(qid)
    uq.status = 'rejected'
    db.session.commit()
    flash('Question rejected.', 'info')
    return redirect(url_for('admin.user_questions'))


# ==================== Discord Integration ====================
@admin_bp.route('/discord/announce', methods=['POST'])
@admin_required
def discord_announce():
    message = request.form.get('message', '')
    webhook_url = current_app.config.get('DISCORD_ANNOUNCEMENT_WEBHOOK', current_app.config.get('DISCORD_ERROR_WEBHOOK', ''))
    if webhook_url:
        try:
            requests.post(webhook_url, json={"content": message}, timeout=5)
            flash('Announcement sent to Discord!', 'success')
        except Exception as e:
            current_app.logger.error(f"Discord announce failed: {e}")
            flash('Failed to send announcement.', 'danger')
    else:
        flash('Webhook not configured.', 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/shop/add', methods=['POST'])
@admin_required
def add_shop_item():
    name = request.form.get('name')
    description = request.form.get('description')
    price = int(request.form.get('price', 0))
    item_type = request.form.get('item_type', 'frame')
    image_url = request.form.get('image_url', '')

    if not name or price <= 0:
        flash('Name and valid price are required.', 'danger')
        return redirect(url_for('admin.shop_items'))

    item = ShopItem(name=name, description=description, price=price, item_type=item_type, image_url=image_url)
    db.session.add(item)
    db.session.commit()
    flash(f'Item "{name}" added!', 'success')
    return redirect(url_for('admin.shop_items'))


@admin_bp.route('/shop/<int:item_id>/delete', methods=['POST'])
@admin_required
def delete_shop_item(item_id):
    item = ShopItem.query.get_or_404(item_id)
    UserInventory.query.filter_by(item_id=item_id).delete()
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.', 'success')
    return redirect(url_for('admin.shop_items'))
