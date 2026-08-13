import uuid

import pytest
from flask import g

from app.extensions import db
from app.models.user import DiscordAccount, User
from app.routes import auth as auth_routes
from app.services.supabase import AuthTokens, SupabaseError, SupabaseService
from conftest import make_user


@pytest.fixture(autouse=True)
def supabase_auth(app, monkeypatch):
    monkeypatch.setitem(app.config, 'SUPABASE_AUTH_ENABLED', True)
    monkeypatch.setitem(app.config, 'SUPABASE_URL',
                        'https://project.supabase.co')
    monkeypatch.setitem(app.config, 'SUPABASE_PUBLISHABLE_KEY',
                        'publishable-key')
    monkeypatch.setitem(app.config, 'SUPABASE_SECRET_KEY', 'secret-key')
    monkeypatch.setattr(
        SupabaseService, 'enabled', staticmethod(lambda: True))


def _tokens(auth_id, **user_fields):
    user = {'id': str(auth_id), **user_fields}
    return AuthTokens('access-token', 'refresh-token', 3600, user)


def _login_session(client, user):
    with client.session_transaction() as browser_session:
        browser_session['_user_id'] = str(user.id)
        browser_session['_fresh'] = True
    g.pop('_login_user', None)


def test_supabase_registration_success_and_failure(client, monkeypatch):
    auth_id = uuid.uuid4()
    monkeypatch.setattr(
        SupabaseService, 'sign_up',
        lambda self, *args, **kwargs: {
            'user': {'id': str(auth_id), 'email_confirmed_at': None}})
    response = client.post('/auth/register', data={
        'username': 'clouduser', 'email': 'cloud@example.com',
        'password': 'Tr1v!aVerse99',
        'confirm_password': 'Tr1v!aVerse99',
    })
    assert response.status_code == 302 and '/auth/login' in response.location
    user = User.query.filter_by(username='clouduser').one()
    assert user.auth_user_id == auth_id
    assert user.password_hash is None and user.is_verified is False

    monkeypatch.setattr(
        SupabaseService, 'sign_up',
        lambda *args, **kwargs: (_ for _ in ()).throw(
            SupabaseError('unavailable')))
    response = client.post('/auth/register', data={
        'username': 'failed', 'email': 'failed@example.com',
        'password': 'Tr1v!aVerse99',
        'confirm_password': 'Tr1v!aVerse99',
    })
    assert response.status_code == 200
    assert User.query.filter_by(username='failed').first() is None


def test_linked_and_legacy_first_login_cutover(client, monkeypatch):
    linked_id = uuid.uuid4()
    linked = make_user(username='linked', email='linked@example.com')
    linked.auth_user_id = linked_id
    legacy = make_user(username='legacy', email='legacy@example.com')
    db.session.commit()
    saved = []
    monkeypatch.setattr(auth_routes, 'save_auth_session',
                        lambda user, tokens: saved.append(user.id))
    monkeypatch.setattr(
        SupabaseService, 'sign_in',
        lambda self, email, password: _tokens(
            linked_id if email == linked.email else legacy_id,
            email=email))

    response = client.post('/auth/login', data={
        'username': linked.username, 'password': 'Tr1v!aVerse99'})
    assert response.status_code == 302 and saved == [linked.id]

    with client.session_transaction() as browser_session:
        browser_session.clear()
    g.pop('_login_user', None)

    legacy_id = uuid.uuid4()
    monkeypatch.setattr(
        SupabaseService, 'create_legacy_user',
        lambda *args, **kwargs: {'user': {'id': str(legacy_id)}})
    response = client.post('/auth/login', data={
        'username': legacy.username, 'password': 'Tr1v!aVerse99'})
    db.session.refresh(legacy)
    assert response.status_code == 302, response.location
    assert legacy.auth_user_id == legacy_id and legacy.password_hash is None
    assert saved[-1] == legacy.id


def test_supabase_login_identity_mismatch_is_rejected(client, monkeypatch):
    user = make_user(username='mismatch', email='mismatch@example.com')
    user.auth_user_id = uuid.uuid4()
    db.session.commit()
    monkeypatch.setattr(
        SupabaseService, 'sign_in',
        lambda *args, **kwargs: _tokens(uuid.uuid4()))
    response = client.post('/auth/login', data={
        'username': user.username, 'password': 'Tr1v!aVerse99'})
    assert response.status_code == 200
    with client.session_transaction() as browser_session:
        assert browser_session.get('_user_id') is None


def test_discord_oauth_new_account_and_expired_state(client, monkeypatch):
    auth_id = uuid.uuid4()
    monkeypatch.setattr(
        SupabaseService, 'begin_oauth',
        lambda self, provider, redirect_to: ('https://oauth.example', 'verify'))
    response = client.get('/auth/discord')
    assert response.location == 'https://oauth.example'
    response = client.get('/auth/discord/callback?code=x')
    assert '/auth/login' in response.location

    monkeypatch.setattr(
        SupabaseService, 'exchange_oauth_code',
        lambda self, code, verifier: _tokens(
            auth_id, email='discord@example.com', user_metadata={
                'provider_id': '12345', 'preferred_username': 'discord-user',
                'full_name': 'Discord User', 'avatar_url': 'https://img'}))
    monkeypatch.setattr(auth_routes, 'save_auth_session', lambda *args: None)
    with client.session_transaction() as browser_session:
        browser_session['supabase_oauth_verifier'] = 'verify'
    response = client.get('/auth/discord/callback?code=valid')
    assert response.status_code == 302 and '/dashboard' in response.location
    user = User.query.filter_by(auth_user_id=auth_id).one()
    assert user.is_verified and user.password_hash is None
    assert DiscordAccount.query.filter_by(
        user_id=user.id, discord_id='12345').count() == 1


def test_password_recovery_and_change(client, monkeypatch):
    auth_id = uuid.uuid4()
    user = make_user(username='recover', email='recover@example.com')
    user.auth_user_id = auth_id
    db.session.commit()
    monkeypatch.setattr(
        SupabaseService, 'recover',
        lambda self, email, redirect_to: 'recovery-verifier')
    response = client.post('/auth/forgot-password', data={'email': user.email})
    assert response.status_code == 302
    with client.session_transaction() as browser_session:
        assert browser_session['supabase_recovery_verifier'] == 'recovery-verifier'

    monkeypatch.setattr(
        SupabaseService, 'exchange_oauth_code',
        lambda self, code, verifier: _tokens(auth_id, email=user.email))
    monkeypatch.setattr(auth_routes, 'save_auth_session', lambda *args: None)
    response = client.get('/auth/reset-password?code=valid')
    assert response.status_code == 200
    updated = []
    monkeypatch.setattr(auth_routes, 'access_token', lambda: 'access-token')
    monkeypatch.setattr(
        SupabaseService, 'update_password',
        lambda self, token, password: updated.append(password))
    monkeypatch.setattr(auth_routes, 'clear_auth_session', lambda: None)
    response = client.post('/auth/reset-password', data={
        'password': 'N3w!Password99',
        'confirm_password': 'N3w!Password99',
    })
    assert response.status_code == 302 and updated == ['N3w!Password99']

    _login_session(client, user)
    monkeypatch.setattr(
        SupabaseService, 'sign_in',
        lambda *args, **kwargs: _tokens(auth_id))
    response = client.post('/auth/change-password', data={
        'current_password': 'old', 'new_password': 'An0ther!Pass99',
        'confirm_password': 'An0ther!Pass99',
    })
    assert response.status_code == 302, response.location
    assert updated[-1] == 'An0ther!Pass99', response.location


def test_realtime_session_only_returns_server_session_token(
        client, user, monkeypatch):
    user.auth_user_id = uuid.uuid4()
    db.session.commit()
    _login_session(client, user)
    monkeypatch.setattr(auth_routes, 'access_token', lambda: 'short-lived-token')
    response = client.get('/auth/realtime-session')
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['access_token'] == 'short-lived-token'
    assert 'secret-key' not in str(payload)
