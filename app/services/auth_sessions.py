"""Encrypted, database-backed Supabase token sessions."""
from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app, session

from app.extensions import db, utcnow
from app.models.settings import Session
from app.services.supabase import AuthTokens, SupabaseError, SupabaseService

SESSION_KEY = 'supabase_session'


def _fernet() -> Fernet:
    material = current_app.config['SECRET_KEY'].encode('utf-8')
    key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
    return Fernet(key)


def _digest(handle: str) -> str:
    return hashlib.sha256(handle.encode('ascii')).hexdigest()


def save_auth_session(user, tokens: AuthTokens) -> None:
    clear_auth_session()
    handle = secrets.token_urlsafe(48)
    cipher = _fernet()
    record = Session(
        user_id=user.id,
        auth_user_id=user.auth_user_id,
        session_token=_digest(handle),
        access_token_ciphertext=cipher.encrypt(
            tokens.access_token.encode('utf-8')).decode('ascii'),
        refresh_token_ciphertext=cipher.encrypt(
            tokens.refresh_token.encode('utf-8')).decode('ascii'),
        ip_address=None,
        is_active=True,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(seconds=tokens.expires_in),
    )
    db.session.add(record)
    session[SESSION_KEY] = handle


def replace_auth_tokens(tokens: AuthTokens) -> None:
    record = _record()
    if not record:
        raise SupabaseError('Authentication session expired')
    cipher = _fernet()
    record.access_token_ciphertext = cipher.encrypt(
        tokens.access_token.encode()).decode('ascii')
    record.refresh_token_ciphertext = cipher.encrypt(
        tokens.refresh_token.encode()).decode('ascii')
    record.expires_at = utcnow() + timedelta(
        seconds=tokens.expires_in)
    record.last_active = utcnow()
    db.session.commit()


def _record():
    handle = session.get(SESSION_KEY)
    if not handle:
        return None
    return Session.query.filter_by(
        session_token=_digest(handle), is_active=True).first()


def access_token(*, refresh_if_needed: bool = True) -> str | None:
    record = _record()
    if not record or not record.access_token_ciphertext:
        return None
    cipher = _fernet()
    try:
        access = cipher.decrypt(
            record.access_token_ciphertext.encode('ascii')).decode('utf-8')
        refresh = cipher.decrypt(
            record.refresh_token_ciphertext.encode('ascii')).decode('utf-8')
    except (InvalidToken, AttributeError):
        record.is_active = False
        db.session.commit()
        session.pop(SESSION_KEY, None)
        return None

    refresh_at = (record.expires_at or datetime.min) - timedelta(seconds=60)
    if refresh_if_needed and utcnow() >= refresh_at:
        try:
            tokens = SupabaseService().refresh(refresh)
        except SupabaseError:
            record.is_active = False
            db.session.commit()
            session.pop(SESSION_KEY, None)
            return None
        record.access_token_ciphertext = cipher.encrypt(
            tokens.access_token.encode()).decode('ascii')
        record.refresh_token_ciphertext = cipher.encrypt(
            tokens.refresh_token.encode()).decode('ascii')
        record.expires_at = utcnow() + timedelta(
            seconds=tokens.expires_in)
        record.last_active = utcnow()
        db.session.commit()
        return tokens.access_token
    return access


def clear_auth_session() -> None:
    record = _record()
    if record:
        record.is_active = False
        db.session.commit()
    session.pop(SESSION_KEY, None)
