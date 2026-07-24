"""TriviaVerse Application Factory"""
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import config
from .extensions import db, socketio
from apscheduler.schedulers.background import BackgroundScheduler
from app.routes.premium_api import premium_api_bp
from app.utils.scheduler import check_expired_premium
from app.routes.fortune import fortune_bp
from app.routes.boss_api import boss_api_bp
from app.extensions import limiter, cors
from app.routes.user_api import user_api_bp
from flask_login import logout_user, current_user
from flask import Flask, request, redirect, url_for, flash, render_template

def create_app(config_name='default'):
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config[config_name])
    app.jinja_env.globals.update(min=min, max=max)

    # ================= LOG SETUP =================
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_handler = RotatingFileHandler('logs/triviaverse.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('TriviaVerse startup')

    # ================= EXTENSIONS INIT =================
    async_mode = app.config.get('SOCKETIO_ASYNC_MODE', 'threading')
    cors_origins = app.config.get('SOCKETIO_CORS_ALLOWED_ORIGINS', '*')
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}})
    limiter.init_app(app)

    from app.extensions import db, migrate, login_manager, socketio, csrf
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, async_mode=async_mode, cors_allowed_origins=cors_origins)
    csrf.init_app(app)

    # Premium хугацаа дууссан хэрэглэгчдийг шалгах төлөвлөгч
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: check_expired_premium(app),
        trigger='interval',
        hours=1
    )
    scheduler.start()

    # ================= BAN CHECK =================
    @app.before_request
    def check_banned():
        if current_user.is_authenticated and current_user.is_banned:
            if request.endpoint not in ('auth.logout', 'static'):
                logout_user()
                flash('Your account has been suspended.', 'danger')
                return redirect(url_for('auth.login'))

    # ================= BLUEPRINTS (бүгдийг энд импортлох) =================
    from app.routes.home import home_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.rooms import rooms_bp
    from app.routes.quiz import quiz_bp
    from app.routes.leaderboard import leaderboard_bp
    from app.routes.social import social_bp
    from app.routes.account import account_bp
    from app.routes.shop import shop_bp
    from app.routes.inventory import inventory_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
    from app.routes.quests import quests_bp
    from app.routes.user_questions import user_q_bp
    from app.routes.daily_trivia import daily_trivia_bp
    from app.routes.search import search_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(rooms_bp, url_prefix='/rooms')
    app.register_blueprint(quiz_bp, url_prefix='/quiz')
    app.register_blueprint(leaderboard_bp, url_prefix='/leaderboard')
    app.register_blueprint(social_bp, url_prefix='/social')
    app.register_blueprint(account_bp, url_prefix='/account')
    app.register_blueprint(shop_bp, url_prefix='/shop')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(quests_bp, url_prefix='/quests')
    app.register_blueprint(user_q_bp, url_prefix='/user-questions')
    app.register_blueprint(daily_trivia_bp, url_prefix='/daily-trivia')
    app.register_blueprint(search_bp)
    app.register_blueprint(premium_api_bp, url_prefix='/premium')
    app.register_blueprint(fortune_bp, url_prefix='/fortune')
    app.register_blueprint(boss_api_bp, url_prefix='/boss')
    app.register_blueprint(user_api_bp, url_prefix='/api/user')


    # ================= MAIL =================
    from app.extensions import mail
    mail.init_app(app)

    # ================= SOCKET EVENTS =================
    from app.sockets.room_socket import register_room_events
    from app.sockets.game_socket import register_game_events
    from app.sockets.notification_socket import register_notification_events
    register_room_events(socketio)
    register_game_events(socketio)
    register_notification_events(socketio)

    # ================= DATABASE & SEEDING + OWNER SETUP =================
    with app.app_context():
        db.create_all()
        _seed_categories()
        _seed_achievements()

        # ---- Автомат Owner тохиргоо (Username, Discord ID, эсвэл Email-ээр) ----
        from app.models.user import User, DiscordAccount

        owner_username = app.config.get('OWNER_USERNAME')
        owner_discord_id = app.config.get('OWNER_DISCORD_ID')
        owner_email = app.config.get('OWNER_EMAIL')

        user = None

        # 1. Username-аар хайх
        if owner_username:
            user = User.query.filter_by(username=owner_username).first()

        # 2. Discord ID-аар хайх (хэрэв олдоогүй бол)
        if not user and owner_discord_id:
            discord_acc = DiscordAccount.query.filter_by(discord_id=owner_discord_id).first()
            if discord_acc and discord_acc.user:
                user = discord_acc.user

        # 3. Email-ээр хайх (хэрэв олдоогүй бол)
        if not user and owner_email:
            user = User.query.filter_by(email=owner_email).first()

        # 4. Олдсон хэрэглэгчийг Owner болгох
        if user and user.role != 'owner':
            user.role = 'owner'
            user.is_admin = True
            user.is_premium = True
            db.session.commit()
            app.logger.info(f"User {user.username} (ID:{user.id}) set as owner via config.")

    # ================= FLASK-LOGIN =================
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import redirect, url_for, flash
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    # ================= GLOBAL TEMPLATE VARIABLES =================
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        return {
            'app_name': 'TriviaVerse',
            'current_year': 2026,
            'current_user': current_user
        }

    # ================= ERROR HANDLERS =================
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app


def _seed_categories():
    from app.models.question import Category
    if Category.query.first():
        return
    categories = [
        ('General Knowledge', 'general', 'Brain', '#5865F2'),
        ('Science', 'science', 'Atom', '#00D4FF'),
        ('Programming', 'programming', 'Code', '#8B5CF6'),
        ('Technology', 'technology', 'Cpu', '#EC4899'),
        ('History', 'history', 'Landmark', '#FACC15'),
        ('Movies', 'movies', 'Film', '#EF4444'),
        ('Anime', 'anime', 'Sparkles', '#22C55E'),
        ('Music', 'music', 'Music', '#7289DA'),
        ('Gaming', 'gaming', 'Gamepad2', '#5865F2'),
        ('Sports', 'sports', 'Trophy', '#00D4FF'),
    ]
    for name, slug, icon, color in categories:
        db.session.add(Category(name=name, slug=slug, icon=icon, color=color))
    db.session.commit()

def _seed_achievements():
    from app.models.achievement import Achievement
    if Achievement.query.first():
        return
    achievements = [
        ('First Blood', 'Win your first match', 'sword', 'wins', 'wins_count', 1, 50, 100, 'common'),
        ('Rising Star', 'Win 10 matches', 'star', 'wins', 'wins_count', 10, 200, 500, 'common'),
        ('Champion', 'Win 50 matches', 'crown', 'wins', 'wins_count', 50, 500, 2000, 'rare'),
        ('Legend', 'Win 100 matches', 'trophy', 'wins', 'wins_count', 100, 1000, 5000, 'epic'),
        ('Trivia Master', 'Play 500 games', 'brain', 'games', 'games_count', 500, 2000, 10000, 'legendary'),
        ('Sharpshooter', 'Maintain 80% accuracy', 'target', 'accuracy', 'accuracy_rate', 80, 300, 1000, 'rare'),
        ('Speed Demon', 'Answer correctly in under 2 seconds', 'zap', 'special', 'fast_answer', 1, 100, 200, 'epic'),
        ('Perfectionist', 'Get a perfect game', 'check-circle', 'special', 'perfect_game', 1, 500, 1000, 'legendary'),
    ]
    for name, desc, icon, cat, req_type, req_val, xp, coins, rarity in achievements:
        db.session.add(Achievement(
            name=name, description=desc, icon=icon, category=cat,
            requirement_type=req_type, requirement_value=req_val,
            xp_reward=xp, coin_reward=coins, rarity=rarity
        ))
    db.session.commit()