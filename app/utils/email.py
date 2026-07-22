from flask import current_app
from flask_mail import Message
from app.extensions import mail

def send_email(subject, recipients, body):
    try:
        msg = Message(subject, recipients=recipients, body=body)
        mail.send(msg)
        current_app.logger.info(f"Email sent to {recipients}")
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        send_discord_error_log(f"Email sending failed: {e}")