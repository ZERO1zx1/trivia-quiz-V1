"""Authentication Routes (Chapters 3, 5, 10)"""
import jwt
import bleach
import requests
import secrets
from urllib.parse import urlparse
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, mail
from app.models.user import User, DiscordAccount
from app.models.achievement import Achievement, UserAchievement
from app.utils.email import send_password_reset_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = bleach.clean(request.form.get('username', '').strip())
        email = bleach.clean(request.form.get('email', '').strip().lower())
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        referral_code = request.form.get('referral_code', '').strip()

        if not all([username, email, password]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        user = User(username=username, email=email, display_name=username)
        user.set_password(password)
        user.coins = 500

        # Handle referral (after user object is created but before commit)
        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer:
                user.referred_by = referrer.id
                referrer.referral_count += 1
                referrer.add_coins(100, 'Referral bonus')
                if referrer.referral_count >= 5:
                    send_notification_for_referrer(referrer)

        db.session.add(user)
        db.session.flush()  # Get user.id for achievements

        # Assign all achievements at 0 progress
        achievements = Achievement.query.all()
        for ach in achievements:
            ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
            db.session.add(ua)
        db.session.commit()

        flash('Account created successfully! Welcome to TriviaVerse.', 'success')
        login_user(user, remember=True)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        user = User.query.filter(
            db.or_(User.username == username, User.email == username)
        ).first()

        if user and user.check_password(password):
            if user.is_banned:
                flash('Your account has been suspended. Contact support.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            user.is_online = True
            user.last_seen = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard.index')

            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)

        flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    current_user.is_online = False
    current_user.last_seen = datetime.utcnow()
    db.session.commit()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home.index'))


@auth_bp.route('/discord')
def discord_login():
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={current_app.config['DISCORD_CLIENT_ID']}"
        f"&redirect_uri={current_app.config['DISCORD_REDIRECT_URI']}"
        f"&response_type=code"
        f"&scope=identify%20email"
    )
    return redirect(discord_auth_url)


@auth_bp.route('/discord/callback')
def discord_callback():
    code = request.args.get('code')
    if not code:
        flash('Discord authentication failed.', 'danger')
        return redirect(url_for('auth.login'))

    data = {
        'client_id': current_app.config['DISCORD_CLIENT_ID'],
        'client_secret': current_app.config['DISCORD_CLIENT_SECRET'],
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': current_app.config['DISCORD_REDIRECT_URI']
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    token_response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)

    if token_response.status_code != 200:
        flash('Failed to authenticate with Discord.', 'danger')
        return redirect(url_for('auth.login'))

    tokens = token_response.json()
    access_token = tokens.get('access_token')

    user_response = requests.get(
        'https://discord.com/api/users/@me',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    if user_response.status_code != 200:
        flash('Failed to get Discord user info.', 'danger')
        return redirect(url_for('auth.login'))

    discord_user = user_response.json()
    discord_id = discord_user['id']
    discord_username = discord_user['username']
    discord_avatar = f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_user.get('avatar')}.png" if discord_user.get('avatar') else None
    email = discord_user.get('email')

    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()

    if discord_account:
        discord_account.access_token = access_token
        discord_account.discord_username = discord_username
        discord_account.discord_avatar = discord_avatar
        db.session.commit()
        login_user(discord_account.user, remember=True)
        flash(f'Welcome back, {discord_account.user.username}!', 'success')
        return redirect(url_for('dashboard.index'))

    if current_user.is_authenticated:
        if current_user.discord_account:
            flash('You already have a Discord account linked.', 'warning')
            return redirect(url_for('dashboard.index'))
        discord_account = DiscordAccount(
            user_id=current_user.id,
            discord_id=discord_id,
            discord_username=discord_username,
            discord_avatar=discord_avatar,
            access_token=access_token
        )
        db.session.add(discord_account)
        db.session.commit()
        flash('Discord account linked successfully!', 'success')
        return redirect(url_for('dashboard.index'))

    if email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if not existing_user.discord_account:
                discord_account = DiscordAccount(
                    user_id=existing_user.id,
                    discord_id=discord_id,
                    discord_username=discord_username,
                    discord_avatar=discord_avatar,
                    access_token=access_token
                )
                db.session.add(discord_account)
                db.session.commit()
            login_user(existing_user, remember=True)
            flash('Your account has been linked with Discord!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            user_email = email
    else:
        user_email = f"{discord_id}@discord.user"

    base_username = discord_username
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}_{counter}"
        counter += 1

    user = User(
        username=username,
        email=user_email,
        display_name=discord_username,
        avatar_url=discord_avatar or '/static/avatars/default.png'
    )
    user.set_password(secrets.token_urlsafe(32))
    user.coins = 500
    db.session.add(user)
    db.session.flush()

    discord_account = DiscordAccount(
        user_id=user.id,
        discord_id=discord_id,
        discord_username=discord_username,
        discord_avatar=discord_avatar,
        access_token=access_token
    )
    db.session.add(discord_account)
    db.session.commit()

    achievements = Achievement.query.all()
    for ach in achievements:
        ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
        db.session.add(ua)
    db.session.commit()

    login_user(user, remember=True)
    flash('Account created with Discord! Welcome to TriviaVerse.', 'success')
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Please enter your email address.', 'warning')
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                token = user.get_reset_password_token(expires_in=600)
                send_password_reset_email(user, token)
            flash('If that email is registered, you will receive a reset link shortly.', 'info')
            return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        else:
            user.set_password(password)
            db.session.commit()
            flash('Password has been reset! You can now login.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Allow logged-in users to change their password from settings page."""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('account.settings'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('account.settings'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'danger')
        return redirect(url_for('account.settings'))

    current_user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('account.settings'))


def send_notification_for_referrer(referrer):
    """Send notification when referrer reaches 5 referrals."""
    try:
        from app.utils.notify import send_notification
        send_notification(
            user_id=referrer.id,
            title='Referral Milestone! 🎉',
            message=f'You\'ve referred {referrer.referral_count} players! Badge unlocked!',
            notif_type='success'
        )
    except Exception:
        pass
