"""Background tasks"""
import redis
from rq import Queue
from flask import current_app
from app.extensions import mail
from flask_mail import Message

def get_redis_queue():
    redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379')
    conn = redis.from_url(redis_url)
    return Queue(connection=conn)

def send_email_async(subject, recipients, body):
    """Имэйл илгээх (ар талд)"""
    try:
        msg = Message(subject, recipients=recipients, body=body)
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Email failed: {e}")

def queue_email(subject, recipients, body):
    """Имэйлийг дараалалд оруулах"""
    queue = get_redis_queue()
    queue.enqueue(send_email_async, subject, recipients, body)