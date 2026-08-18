"""Streak protection alert job (FIX-014).

Canonical registration point for streak-related background work.
Moved here from the legacy ``app.utils.scheduler`` module as part of the
incremental structure cleanup — the legacy module remains available as a
deprecated compatibility shim.

NOTE on the legacy implementation: it queried ``User.streak_count`` and
``User.last_activity``, columns that do not exist on the User model, so
the old job would have raised ``AttributeError`` the first time the
scheduler fired it. This implementation uses the real ``scores`` table
(recent strong performance) plus ``User.last_login_at`` (recent account
activity) so the alert is both safe and meaningful.
"""
from datetime import datetime, timedelta

from app.extensions import db, utcnow
from app.models.room import Match, Score
from app.models.user import User
from app.utils.email import send_streak_alert_email

# Send the warning roughly four hours before a streak would reset.
STREAK_WARNING_HOURS = 20
STREAK_LOOKBACK_DAYS = 2


def check_streak_protection(app):
    """Email opted-in members who performed strongly recently but have not
    logged in since the warning threshold, so they can defend their
    leaderboard standing / streak before it resets.

    Can be called directly (services handle their own app context) or
    wrapped by ``register_jobs``.
    """
    with app.app_context():
        yesterday = utcnow() - timedelta(days=STREAK_LOOKBACK_DAYS)
        warning_threshold = utcnow() - timedelta(hours=STREAK_WARNING_HOURS)

        # Users with a recent high-streak score (joined through the match
        # timestamp, since the scores table carries no created_at), opted
        # into promo email, and idle since the warning threshold.
        recent_streak_ids = db.session.query(Score.user_id).join(
            Match, Match.id == Score.match_id,
        ).filter(
            Match.started_at.isnot(None),
            Match.started_at > yesterday,
            Score.max_streak >= 3,
        ).distinct()

        potential_losers = User.query.filter(
            User.id.in_(recent_streak_ids),
            User.last_login_at < warning_threshold,
            User.last_login_at > (yesterday - timedelta(days=STREAK_LOOKBACK_DAYS)),
            User.email_notif_promo.is_(True),
        ).all()

        for user in potential_losers:
            # The strongest streak this user posted during the lookback.
            best = db.session.query(Score.max_streak).join(
                Match, Match.id == Score.match_id,
            ).filter(
                Score.user_id == user.id,
                Match.started_at > yesterday,
            ).order_by(Score.max_streak.desc()).limit(1).scalar() or 0
            send_streak_alert_email(user, best)
            app.logger.info("Streak alert sent to %s", user.username)
        db.session.commit()
