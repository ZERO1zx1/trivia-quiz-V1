"""Asynchronous email task helpers (RQ-based).

Canonical location for the application's background email helpers. The
original root-level ``app/tasks.py`` module was orphaned (no importers
inside the repository) and has been relocated here; a deprecated stub
remains at ``app/tasks.py`` for backward compatibility.

These helpers rely on Redis + RQ, which are not pinned in
``requirements.txt`` — import guard keeps the rest of the app working
when RQ is unavailable.
"""
from app.extensions import mail

try:
    import redis
    from rq import Queue
except ImportError:  # pragma: no cover - RQ not installed
    redis = None
    Queue = None

from flask import current_app
from flask_mail import Message


def get_redis_queue():
    """Return an RQ ``Queue`` bound to the configured Redis instance."""
    if redis is None or Queue is None:
        raise RuntimeError(
            "rq is not installed; install it and set REDIS_URL to use "
            "background email queuing."
        )
    redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379')
    return Queue(connection=redis.from_url(redis_url))


def send_email_async(subject, recipients, body):
    """Send an email synchronously (worker entry point)."""
    try:
        msg = Message(subject, recipients=recipients, body=body)
        mail.send(msg)
    except Exception as e:  # noqa: BLE001
        current_app.logger.error("Email failed: %s", e)


def queue_email(subject, recipients, body):
    """Enqueue an email for background delivery."""
    queue = get_redis_queue()
    queue.enqueue(send_email_async, subject, recipients, body)
