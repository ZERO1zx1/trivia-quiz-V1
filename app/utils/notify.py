from app.extensions import db, socketio
from app.models.notification import Notification
import requests
from flask import current_app

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

def announce_leaderboard_change(user, period, rank):
    webhook_url = current_app.config.get('DISCORD_LEADERBOARD_WEBHOOK')
    if not webhook_url:
        return
    message = f"🏆 **{user.username}** just reached **#{rank}** on the {period} leaderboard!"
    try:
        requests.post(webhook_url, json={"content": message})
    except Exception as e:
        current_app.logger.error(f"Discord webhook failed: {e}")