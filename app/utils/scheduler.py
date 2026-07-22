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