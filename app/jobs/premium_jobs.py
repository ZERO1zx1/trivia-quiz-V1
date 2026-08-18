"""Premium membership expiry job (FIX-014).

Canonical registration point for premium-related background work.
Moved here from the legacy ``app.utils.scheduler`` module as part of the
incremental structure cleanup — the legacy module remains available as a
deprecated compatibility shim.
"""
from datetime import datetime

from app.extensions import db, utcnow
from app.models.user import User

try:
    import requests  # noqa: F401
except ImportError:  # pragma: no cover - requests is in requirements
    requests = None


# Default per-user storage/coin limits for lapsed premium members.
STANDARD_BOX_STORAGE_LIMIT = 50
STANDARD_COIN_MULTIPLIER = 1


def check_expired_premium(app):
    """Downgrade expired premium members, reset their multipliers and
    storage limits, and (optionally) remove their premium Discord role.

    Can be called directly (services handle their own app context) or
    wrapped by ``register_jobs``.
    """
    with app.app_context():
        expired = User.query.filter(
            User.is_premium.is_(True),
            User.premium_expiry.isnot(None),
            User.premium_expiry < utcnow(),
        ).all()
        api_base = app.config.get('API_BASE_URL', '')
        for user in expired:
            user.is_premium = False
            user.premium_expiry = None
            user.coin_multiplier = STANDARD_COIN_MULTIPLIER
            user.box_storage_limit = STANDARD_BOX_STORAGE_LIMIT
            if requests is not None and user.discord_account and api_base:
                try:
                    requests.post(
                        f"{api_base}/discord/premium-role",
                        json={"discord_id": user.discord_account.discord_id,
                              "action": "remove"},
                        timeout=5,
                    )
                except Exception as e:  # noqa: BLE001
                    app.logger.error("Discord role removal failed: %s", e)
        db.session.commit()
