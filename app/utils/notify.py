# app/utils/notify.py
from app.extensions import db, socketio
from app.models.notification import Notification

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