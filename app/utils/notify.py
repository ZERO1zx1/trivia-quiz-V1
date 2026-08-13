from app.extensions import db, socketio
from app.models.notification import Notification
import requests
from flask import current_app
from app.models.user import User
from app.services.supabase import SupabaseError, SupabaseService

def send_notification(user_id, title, message, notif_type='info'):
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type
    )
    db.session.add(notif)
    db.session.commit()

    socketio.emit(
        'new_notification',
        notif.to_dict(),
        room=f'user_{user_id}',
        namespace='/notifications'
    )
    user = db.session.get(User, user_id)
    if user and user.auth_user_id and SupabaseService.enabled():
        try:
            SupabaseService().broadcast(
                f'user:{user.auth_user_id}:notifications',
                'notification_created', notif.to_dict(), private=True)
        except SupabaseError:
            current_app.logger.exception('Realtime notification failed')

def announce_leaderboard_change(user, period, rank):
    webhook_url = current_app.config.get('DISCORD_LEADERBOARD_WEBHOOK')
    if not webhook_url:
        return
    message = f"🏆 **{user.username}** just reached **#{rank}** on the {period} leaderboard!"
    try:
        requests.post(webhook_url, json={"content": message}, timeout=10)
    except requests.RequestException as exc:
        current_app.logger.error('Discord webhook failed: %s', exc)
