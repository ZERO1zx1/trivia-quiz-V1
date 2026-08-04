"""Anti-Cheat System
Detects suspicious activity: bots, scripts, and speed-hacking.
"""
from datetime import datetime, timedelta
from flask import current_app, request
from app.extensions import db


# Suspicious speed threshold (seconds) - if answered correctly in less than this
SUSPICIOUS_SPEED_THRESHOLD = 0.5

# Consecutive suspicious answers before flagging
SUSPICIOUS_COUNT_THRESHOLD = 10

# Shadow-ban duration
SHADOW_BAN_DURATION_HOURS = 24


class AntiCheatTracker:
    """Tracks player answer speed and accuracy patterns."""

    @staticmethod
    def record_answer(user, question_id, answer_id, time_taken, is_correct):
        """Record an answer for anti-cheat analysis.

        If a player consistently answers very hard questions
        correctly in under 0.5 seconds, flag as suspicious.
        """
        from app.models.settings import AuditLog

        if not is_correct:
            return False

        # Check if answer speed is suspicious
        if time_taken < SUSPICIOUS_SPEED_THRESHOLD:
            current_app.logger.warning(
                f"ANTI-CHEAT: User {user.id} answered Q{question_id} in {time_taken:.3f}s"
            )
            # Log suspicious activity
            try:
                log = AuditLog(
                    user_id=user.id,
                    action='suspicious_answer',
                    details=f'Question {question_id}, time: {time_taken:.3f}s, correct: {is_correct}'
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                db.session.rollback()

            return True  # Flagged as suspicious

        return False

    @staticmethod
    def check_user_for_ban(user):
        """Check if a user should be shadow-banned based on recent activity.

        If user has 10+ suspicious answers in the last hour,
        automatically apply shadow-ban.
        """
        from app.models.settings import AuditLog

        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        suspicious_count = AuditLog.query.filter(
            AuditLog.user_id == user.id,
            AuditLog.action == 'suspicious_answer',
            AuditLog.created_at >= one_hour_ago
        ).count()

        if suspicious_count >= SUSPICIOUS_COUNT_THRESHOLD:
            # Apply shadow-ban
            user.is_banned = True
            db.session.commit()
            current_app.logger.warning(
                f"ANTI-CHEAT: User {user.id} shadow-banned after "
                f"{suspicious_count} suspicious answers"
            )
            return True

        return False

    @staticmethod
    def get_suspicious_users(limit=50):
        """Get list of potentially suspicious users for admin review."""
        from app.models.settings import AuditLog

        one_day_ago = datetime.utcnow() - timedelta(hours=24)
        suspicious_logs = db.session.query(
            AuditLog.user_id,
            db.func.count(AuditLog.id).label('suspicious_count')
        ).filter(
            AuditLog.action == 'suspicious_answer',
            AuditLog.created_at >= one_day_ago
        ).group_by(AuditLog.user_id).order_by(
            db.desc('suspicious_count')
        ).limit(limit).all()

        result = []
        for user_id, count in suspicious_logs:
            from app.models.user import User
            user = User.query.get(user_id)
            if user:
                result.append({
                    'user_id': user.id,
                    'username': user.username,
                    'suspicious_count': count,
                    'is_banned': user.is_banned
                })

        return result
