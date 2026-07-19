"""Dashboard Routes"""
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.extensions import db
from app.models.room import Room, RoomPlayer
from app.models.question import Category
from app.models.economy import Transaction, LeaderboardEntry
from app.models.achievement import UserAchievement
from app.utils.notify import send_notification

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    recent_matches = current_user.scores.order_by(db.desc('id')).limit(5).all()
    friends = current_user.get_friends()
    online_friends = [f for f in friends if f.is_online]
    notifications = current_user.notifications.limit(10).all()
    top_players = LeaderboardEntry.query.filter_by(period='alltime').order_by(
        LeaderboardEntry.score.desc()).limit(5).all()
    categories = Category.query.filter_by(is_active=True).all()
    active_rooms = Room.query.filter_by(status='waiting').limit(8).all()
    transactions = current_user.transactions.order_by(db.desc('id')).limit(5).all()
    achievements = UserAchievement.query.filter_by(
        user_id=current_user.id, is_unlocked=True).order_by(db.desc('unlocked_at')).limit(6).all()

    return render_template('dashboard/index.html',
                         recent_matches=recent_matches,
                         online_friends=online_friends,
                         notifications=notifications,
                         top_players=top_players,
                         categories=categories,
                         active_rooms=active_rooms,
                         transactions=transactions,
                         achievements=achievements)

@dashboard_bp.route('/api/stats')
@login_required
def api_user_stats():
    stats = {
        'username': current_user.username,
        'display_name': current_user.display_name,
        'level': current_user.level,
        'xp': current_user.xp,
        'coins': current_user.coins,
        'wins': current_user.wins,
        'losses': current_user.losses,
        'games_played': current_user.games_played,
        'accuracy': round(current_user.accuracy, 1),
        'avatar': current_user.avatar_url,
        'is_online': current_user.is_online
    }
    return jsonify(stats)

@dashboard_bp.route('/daily-reward', methods=['POST'])
@login_required
def daily_reward():
    # Хугацаа шалгах
    if current_user.last_daily_reward:
        time_since = datetime.utcnow() - current_user.last_daily_reward
        if time_since < timedelta(hours=20):
            hours_left = 20 - (time_since.total_seconds() / 3600)
            return jsonify({'success': False, 'message': f'Come back in {int(hours_left)}h!'})

    # Шагнал өгөх (coins + xp)
    coin_reward = current_app.config['DAILY_REWARD_COINS']
    xp_reward = 10
    current_user.add_coins(coin_reward, 'Daily Reward')
    level_up, old_level, new_level = current_user.add_xp(xp_reward)
    current_user.last_daily_reward = datetime.utcnow()
    db.session.commit()

    # Мэдэгдэл илгээх
    send_notification(
        user_id=current_user.id,
        title='Daily Reward Claimed!',
        message=f'You received {coin_reward} coins and {xp_reward} XP!',
        notif_type='success'
    )
    if level_up:
        send_notification(
            user_id=current_user.id,
            title='Level Up!',
            message=f'Congratulations, you reached level {new_level}!',
            notif_type='success'
        )

    return jsonify({
        'success': True,
        'reward': coin_reward,
        'xp_earned': xp_reward,
        'level_up': level_up,
        'new_level': new_level,
        'new_coins': current_user.coins,
        'new_xp': current_user.xp
    })