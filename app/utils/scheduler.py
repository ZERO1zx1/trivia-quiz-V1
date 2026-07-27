from datetime import datetime
import requests
from app.extensions import db
from app.models.user import User

def check_expired_premium(app):
    with app.app_context():
        expired = User.query.filter(
            User.is_premium == True,
            User.premium_expiry != None,
            User.premium_expiry < datetime.utcnow()
        ).all()
        for user in expired:
            user.is_premium = False
            user.premium_expiry = None
            user.coin_multiplier = 1
            user.box_storage_limit = 50  # энгийн хэрэглэгчийн хязгаар
            # Discord Role хасах
            if user.discord_account:
                try:
                    requests.post(
                        f"{app.config['API_BASE_URL']}/discord/premium-role",
                        json={"discord_id": user.discord_account.discord_id, "action": "remove"},
                        timeout=5
                    )
                except Exception as e:
                    app.logger.error(f"Discord role removal failed: {e}")
        db.session.commit()

def check_streak_protection(app):
    """Check users who are about to lose their streak and send email alert."""
    from datetime import datetime, timedelta
    from app.utils.email import send_streak_alert_email
    
    with app.app_context():
        # Users who haven't played today but have a streak
        # (Assuming last_activity is updated on game play)
        yesterday = datetime.utcnow() - timedelta(days=1)
        warning_threshold = datetime.utcnow() - timedelta(hours=20) # 4 hours before reset
        
        potential_losers = User.query.filter(
            User.streak_count > 0,
            User.last_activity < yesterday,
            User.last_activity > (yesterday - timedelta(days=1)),
            User.email_notif_promo == True # Use promo or create a specific setting
        ).all()
        
        for user in potential_losers:
            # Check if alert already sent today to avoid spam
            # (Simplified: assume one alert per streak danger period)
            send_streak_alert_email(user)
            app.logger.info(f"Streak alert sent to {user.username}")