import json
import uuid
from datetime import datetime, timedelta

import pytest
import requests

from app.extensions import db
from app.models.settings import Session
from app.services import auth_sessions
from app.services.supabase import AuthTokens, SupabaseError, SupabaseService


class FakeResponse:
    def __init__(self, status=200, payload=None, content=True):
        self.status_code = status
        self._payload = payload
        self.content = b'{}' if content else b''

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload if self._payload is not None else {}


@pytest.fixture
def configured_supabase(app):
    original = {key: app.config.get(key) for key in (
        'SUPABASE_URL', 'SUPABASE_PUBLISHABLE_KEY', 'SUPABASE_SECRET_KEY',
        'SUPABASE_HTTP_TIMEOUT', 'SUPABASE_AUTH_ENABLED')}
    app.config.update(
        SUPABASE_URL='https://project.supabase.co',
        SUPABASE_PUBLISHABLE_KEY='publishable-test-key',
        SUPABASE_SECRET_KEY='secret-test-key',
        SUPABASE_HTTP_TIMEOUT=7, SUPABASE_AUTH_ENABLED=True)
    yield
    app.config.update(original)


def test_request_adapter_success_headers_and_failures(configured_supabase,
                                                       monkeypatch):
    service = SupabaseService()
    captured = {}

    def request(method, url, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        return FakeResponse(payload={'ok': True})

    monkeypatch.setattr(service.http, 'request', request)
    assert service._request('GET', '/auth/v1/user', token='user-token') == {
        'ok': True}
    assert captured['headers']['apikey'] == 'publishable-test-key'
    assert captured['headers']['Authorization'] == 'Bearer user-token'
    assert captured['timeout'] == 7

    monkeypatch.setattr(
        service.http, 'request',
        lambda *args, **kwargs: FakeResponse(400, {'message': 'invalid'}))
    with pytest.raises(SupabaseError, match='invalid'):
        service._request('POST', '/auth/v1/token')

    def unavailable(*args, **kwargs):
        raise requests.Timeout('timed out')

    monkeypatch.setattr(service.http, 'request', unavailable)
    with pytest.raises(SupabaseError, match='unavailable'):
        service._request('GET', '/auth/v1/user')


def test_auth_storage_realtime_adapter_contracts(configured_supabase,
                                                 monkeypatch):
    service = SupabaseService()
    calls = []

    def request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        if 'challenge' in path:
            return {'id': 'challenge-id'}
        if 'token' in path or 'verify' in path:
            return {'access_token': 'access', 'refresh_token': 'refresh',
                    'expires_in': 120, 'user': {'id': 'auth-id'}}
        return {'user': {'id': 'auth-id'}}

    monkeypatch.setattr(service, '_request', request)
    assert service.sign_up('a@example.com', 'password', {'name': 'A'})['user']
    assert service.sign_in('a@example.com', 'password').access_token == 'access'
    assert service.create_legacy_user(
        'a@example.com', 'password', {}, True)['user']['id'] == 'auth-id'
    service.delete_user('auth-id')
    assert service.refresh('refresh').refresh_token == 'refresh'
    verifier = service.recover('a@example.com', 'https://app/reset')
    assert len(verifier) > 40
    service.update_password('access', 'new-password')
    oauth_url, oauth_verifier = service.begin_oauth(
        'discord', 'https://app/callback')
    assert 'provider=discord' in oauth_url and len(oauth_verifier) > 40
    assert service.exchange_oauth_code(
        'code', oauth_verifier).user['id'] == 'auth-id'
    service.enroll_totp('access', 'phone')
    assert service.challenge_totp('access', 'factor') == 'challenge-id'
    assert service.verify_totp(
        'access', 'factor', 'challenge-id', '123456').expires_in == 120
    service.unenroll_factor('access', 'factor')
    service.broadcast('user:auth-id:notifications', 'created', {'id': 1})
    assert calls[-1][1].endswith('events/created?private=true')

    monkeypatch.setattr(
        service.http, 'post',
        lambda *args, **kwargs: FakeResponse(201, {'Key': 'avatars/file'}))
    url = service.upload_image(
        'avatars', 'auth-id/avatar.webp', b'image', 'image/webp', 'access')
    assert url.endswith('/avatars/auth-id/avatar.webp')


def test_database_backed_auth_session_lifecycle(app, user,
                                                configured_supabase,
                                                monkeypatch):
    user.auth_user_id = uuid.uuid4()
    db.session.commit()
    tokens = AuthTokens('access-one', 'refresh-one', 3600,
                        {'id': str(user.auth_user_id)})
    with app.test_request_context('/'):
        auth_sessions.save_auth_session(user, tokens)
        db.session.commit()
        browser_handle = auth_sessions.session[auth_sessions.SESSION_KEY]
        record = Session.query.one()
        assert record.session_token != browser_handle
        assert 'access-one' not in record.access_token_ciphertext
        assert auth_sessions.access_token() == 'access-one'

        replacement = AuthTokens('access-two', 'refresh-two', 7200, {})
        auth_sessions.replace_auth_tokens(replacement)
        assert auth_sessions.access_token() == 'access-two'
        auth_sessions.clear_auth_session()
        assert auth_sessions.access_token() is None
        assert Session.query.one().is_active is False

        with pytest.raises(SupabaseError, match='expired'):
            auth_sessions.replace_auth_tokens(replacement)

        auth_sessions.save_auth_session(user, tokens)
        db.session.commit()
        record = Session.query.filter_by(is_active=True).one()
        record.expires_at = datetime(2000, 1, 1)
        db.session.commit()
        monkeypatch.setattr(
            SupabaseService, 'refresh',
            lambda self, refresh: AuthTokens(
                'refreshed-access', 'refreshed-refresh', 3600, {}))
        assert auth_sessions.access_token() == 'refreshed-access'

        record.access_token_ciphertext = 'not-fernet-ciphertext'
        db.session.commit()
        assert auth_sessions.access_token() is None
        assert record.is_active is False


def test_game_snapshot_round_trip(db, user):
    from app.models.room import GameSnapshot, Room
    from app.sockets import game_socket

    room = Room(code='SNAP01', name='Snapshot', host_id=user.id)
    db.session.add(room)
    db.session.commit()
    game_socket.game_states['SNAP01'] = {
        'current_question': 1,
        'eliminated': {user.id},
        'scores': {user.id: 50},
        'streaks': {user.id: 2},
        'survival_lives': {user.id: 1},
        'answers': {user.id: {0: 7}},
    }
    game_socket._save_snapshot('SNAP01')
    snapshot = GameSnapshot.query.one()
    assert snapshot.version == 1
    game_socket.game_states.clear()
    restored = game_socket._state('SNAP01')
    assert restored['eliminated'] == {user.id}
    assert restored['scores'][user.id] == 50
    assert restored['answers'][user.id][0] == 7
    game_socket._save_snapshot('SNAP01')
    assert snapshot.version == 2
