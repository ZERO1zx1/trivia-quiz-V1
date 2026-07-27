"""Email Utilities (Chapter 10)"""
from flask import current_app, render_template, url_for
from flask_mail import Message
from app.extensions import mail


def send_email(subject, recipients, body, html=None):
    """Generic email sending utility."""
    try:
        msg = Message(subject, recipients=recipients, body=body, html=html)
        mail.send(msg)
        current_app.logger.info(f"Email sent to {recipients}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        return False


def send_password_reset_email(user, token):
    """Send password reset email with token link (Chapter 10)."""
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        body = (
            f"Dear {user.username},\n\n"
            f"To reset your password, please visit the following link:\n\n"
            f"{reset_url}\n\n"
            f"If you did not make this request, please ignore this email.\n\n"
            f"This link will expire in 10 minutes.\n\n"
            f"Sincerely,\n"
            f"The TriviaVerse Team"
        )
        html = (
            f"<p>Dear <strong>{user.username}</strong>,</p>"
            f"<p>To reset your password, please click the following link:</p>"
            f"<p><a href=\"{reset_url}\" style=\"background-color:#5865F2;color:white;"
            f"padding:10px 20px;border-radius:5px;text-decoration:none;display:inline-block;"
            f"margin:10px 0;\">Reset Password</a></p>"
            f"<p>If you did not make this request, please ignore this email.</p>"
            f"<p>This link will expire in 10 minutes.</p>"
            f"<p>Sincerely,<br>The TriviaVerse Team</p>"
        )
        send_email(
            subject='[TriviaVerse] Password Reset Request',
            recipients=[user.email],
            body=body,
            html=html
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {e}")


def send_welcome_email(user):
    """Send welcome email to new users."""
    try:
        body = (
            f"Welcome to TriviaVerse, {user.username}!\n\n"
            f"You have been awarded 500 coins to get started.\n"
            f"Visit your dashboard to begin playing!\n\n"
            f"Sincerely,\n"
            f"The TriviaVerse Team"
        )
        send_email(
            subject='[TriviaVerse] Welcome!',
            recipients=[user.email],
            body=body
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send welcome email: {e}")


def send_otp_email(user, otp):
    """Send 6-digit OTP code for account verification."""
    try:
        subject = '[TriviaVerse] Verify Your Account'
        body = f"Hello {user.username},\n\nYour verification code is: {otp}\n\nThis code will expire in 10 minutes."
        html = render_template('emails/otp.html', user=user, otp=otp)
        send_email(subject, [user.email], body, html)
    except Exception as e:
        current_app.logger.error(f"Failed to send OTP email: {e}")


def send_security_alert_email(user, ip_address, location="Unknown"):
    """Send alert for login from a new device or location."""
    if not user.email_notif_security:
        return
    try:
        subject = '[TriviaVerse] Security Alert: New Login'
        body = f"Hello {user.username},\n\nA new login was detected from IP: {ip_address} ({location})."
        html = render_template('emails/security_alert.html', user=user, ip=ip_address, location=location)
        send_email(subject, [user.email], body, html)
    except Exception as e:
        current_app.logger.error(f"Failed to send security alert email: {e}")


def send_duel_invite_email(user, challenger_name, wager):
    """Send email for a new duel challenge."""
    if not user.email_notif_social:
        return
    try:
        subject = f'[TriviaVerse] {challenger_name} challenged you to a Duel!'
        body = f"Hello {user.username},\n\n{challenger_name} has challenged you to a 1v1 Duel for {wager} coins!"
        html = render_template('emails/duel_invite.html', user=user, challenger=challenger_name, wager=wager)
        send_email(subject, [user.email], body, html)
    except Exception as e:
        current_app.logger.error(f"Failed to send duel invite email: {e}")


def send_streak_alert_email(user, streak_days):
    """Send alert when a user is about to lose their streak."""
    if not user.email_notif_promo:
        return
    try:
        subject = '[TriviaVerse] Don\'t lose your streak!'
        body = f"Hello {user.username},\n\nYou are about to lose your {streak_days}-day streak! Play now to protect it."
        html = render_template('emails/streak_alert.html', user=user, streak=streak_days)
        send_email(subject, [user.email], body, html)
    except Exception as e:
        current_app.logger.error(f"Failed to send streak alert email: {e}")
