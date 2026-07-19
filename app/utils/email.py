from flask import current_app, url_for
from flask_mail import Message
from app.extensions import mail
import jwt
from datetime import datetime, timedelta

def send_reset_email(user):
    token = jwt.encode(
        {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(hours=1)},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message(
        'TriviaVerse Password Reset',
        recipients=[user.email]
    )
    msg.body = f'''Хэрэв та энэ хүсэлтийг хийсэн бол доорх холбоосоор нууц үгээ сэргээнэ үү:
{reset_url}

Хэрэв та хүсэлт хийгээгүй бол энэ имэйлийг үл харгалзаарай.
'''
    mail.send(msg)