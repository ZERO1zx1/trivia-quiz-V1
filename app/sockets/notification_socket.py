def register_notification_events(socketio):
    @socketio.on('mark_read', namespace='/notifications')
    def handle_mark_read(data):
        from flask_login import current_user
        if current_user.is_authenticated:
            notif_id = data.get('notif_id')
            from app.models.notification import Notification
            n = Notification.query.get(notif_id)
            if n and n.user_id == current_user.id:
                n.is_read = True
                from app.extensions import db
                db.session.commit()