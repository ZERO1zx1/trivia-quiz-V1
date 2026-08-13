import io
import uuid
from datetime import datetime, timedelta

import jwt
import pytest
from flask import g
from PIL import Image

from app.extensions import db
from app.models.settings import TwoFactorAuth
from app.routes import account as account_routes
from app.routes import two_factor as two_factor_routes
from app.services.supabase import AuthTokens, SupabaseService


@pytest.fixture(autouse=True)
def configured(app, monkeypatch):
    monkeypatch.setitem(app.config, 'SUPABASE_AUTH_ENABLED', True)
    monkeypatch.setitem(app.config, 'SUPABASE_URL',
                        'https://project.supabase.co')
    monkeypatch.setitem(app.config, 'SUPABASE_PUBLISHABLE_KEY', 'public')
    monkeypatch.setitem(app.config, 'SUPABASE_SECRET_KEY', 'secret')
    monkeypatch.setattr(
        SupabaseService, 'enabled', staticmethod(lambda: True))


def _login(client, user):
    with client.session_transaction() as browser_session:
        browser_session['_user_id'] = str(user.id)
        browser_session['_fresh'] = True
    g.pop('_login_user', None)


def _webp_source():
    stream = io.BytesIO()
    Image.new('RGB', (16, 16), '#5865f2').save(stream, 'PNG')
    stream.seek(0)
    return stream


def _tokens(user):
    return AuthTokens('elevated', 'refresh', 3600,
                      {'id': str(user.auth_user_id)})


def test_profile_images_are_normalized_and_owned(
        client, user, monkeypatch):
    user.auth_user_id = uuid.uuid4()
    user.is_premium = True
    db.session.commit()
    _login(client, user)
    uploaded = []
    monkeypatch.setattr(account_routes, 'access_token', lambda: 'access')

    def upload(self, bucket, path, data, content_type, token):
        uploaded.append((bucket, path, data, content_type, token))
        return f'https://cdn/{bucket}/{path}'

    monkeypatch.setattr(SupabaseService, 'upload_image', upload)
    response = client.post('/account/update-profile', data={
        'display_name': 'Cloud User', 'bio': '<script>alert(1)</script>',
        'avatar': (_webp_source(), 'avatar.png'),
        'banner': (_webp_source(), 'banner.jpg'),
    }, content_type='multipart/form-data')
    assert response.status_code == 302 and len(uploaded) == 2
    assert all(item[1].startswith(f'{user.auth_user_id}/')
               for item in uploaded)
    assert all(item[3] == 'image/webp' for item in uploaded)
    assert all(item[2].startswith(b'RIFF') for item in uploaded)
    assert user.avatar_url.startswith('https://cdn/avatars/')
    assert user.banner_url.startswith('https://cdn/banners/')

    response = client.post('/account/update-profile', data={
        'avatar': (io.BytesIO(b'not-an-image'), 'bad.png'),
    }, content_type='multipart/form-data')
    assert response.status_code == 302


def test_account_settings_and_supabase_password(client, user, monkeypatch):
    user.auth_user_id = uuid.uuid4()
    db.session.commit()
    _login(client, user)
    assert client.post('/account/update-discord-settings', json={
        'rich_presence': False, 'dm_notifications': False}).get_json()['success']
    assert client.post('/account/update-game-settings', json={
        'preferred_difficulty': 'hard', 'performance_mode': True,
        'email_notif_social': False}).get_json()['success']
    assert client.post('/account/settings/theme', json={
        'theme': 'light'}).get_json()['success']
    assert client.post('/account/settings/theme', json={
        'theme': 'invalid'}).status_code == 400
    response = client.post('/account/update-preferences', data={
        'email_notif_promo': 'on'})
    assert response.status_code == 302

    changed = []
    monkeypatch.setattr(
        SupabaseService, 'sign_in', lambda *args: _tokens(user))
    monkeypatch.setattr(account_routes, 'access_token', lambda: 'access')
    monkeypatch.setattr(
        SupabaseService, 'update_password',
        lambda self, token, password: changed.append(password))
    monkeypatch.setattr('app.utils.email.send_email', lambda **kwargs: None)
    response = client.post('/account/change-password', data={
        'current_password': 'old', 'new_password': 'N3w!Password99',
        'confirm_password': 'N3w!Password99'})
    assert response.status_code == 302 and changed == ['N3w!Password99']
    assert user.password_hash is None


def test_supabase_mfa_setup_enable_disable(client, user, monkeypatch):
    user.auth_user_id = uuid.uuid4()
    db.session.commit()
    _login(client, user)
    factor_id = uuid.uuid4()
    monkeypatch.setattr(two_factor_routes, 'access_token',
                        lambda **kwargs: 'access')
    monkeypatch.setattr(
        SupabaseService, 'enroll_totp',
        lambda *args: {'factor': {'id': str(factor_id), 'totp': {
            'qr_code': 'data:image/svg+xml;base64,qr', 'secret': 'secret'}}})
    response = client.get('/two-factor/setup')
    assert response.status_code == 200
    with client.session_transaction() as browser_session:
        assert browser_session['pending_supabase_factor_id'] == str(factor_id)

    monkeypatch.setattr(
        SupabaseService, 'challenge_totp', lambda *args: 'challenge')
    monkeypatch.setattr(
        SupabaseService, 'verify_totp', lambda *args: _tokens(user))
    replaced = []
    monkeypatch.setattr(two_factor_routes, 'replace_auth_tokens',
                        lambda tokens: replaced.append(tokens.access_token))
    response = client.post('/two-factor/enable', data={'code': '123456'})
    assert response.status_code == 302 and replaced == ['elevated']
    twofa = TwoFactorAuth.query.filter_by(user_id=user.id).one()
    assert twofa.is_enabled and twofa.auth_factor_id == factor_id

    unenrolled = []
    monkeypatch.setattr(
        SupabaseService, 'unenroll_factor',
        lambda self, token, factor: unenrolled.append(factor))
    response = client.post('/two-factor/disable', data={'code': '123456'})
    assert response.status_code == 302
    assert unenrolled == [str(factor_id)] and twofa.is_enabled is False


def test_supabase_mfa_login_verification(client, user, app, monkeypatch):
    user.auth_user_id = uuid.uuid4()
    factor_id = uuid.uuid4()
    db.session.add(TwoFactorAuth(
        user_id=user.id, is_enabled=True, auth_factor_id=factor_id,
        method='supabase_totp'))
    db.session.commit()
    token = jwt.encode({
        'uid': user.id, 'nonce': 'test',
        'exp': datetime.utcnow() + timedelta(minutes=10),
    }, app.config['SECRET_KEY'], algorithm='HS256')
    with client.session_transaction() as browser_session:
        browser_session['2fa_user_id'] = user.id
        browser_session['2fa_pending_token'] = token
    g.pop('_login_user', None)
    monkeypatch.setattr(two_factor_routes, 'access_token',
                        lambda **kwargs: 'access')
    monkeypatch.setattr(
        SupabaseService, 'challenge_totp', lambda *args: 'challenge')
    monkeypatch.setattr(
        SupabaseService, 'verify_totp', lambda *args: _tokens(user))
    monkeypatch.setattr(two_factor_routes, 'replace_auth_tokens',
                        lambda tokens: None)
    response = client.post('/two-factor/verify', data={'code': '123456'})
    assert response.status_code == 302 and '/dashboard' in response.location
    with client.session_transaction() as browser_session:
        assert browser_session.get('_user_id') == str(user.id)
        assert '2fa_pending_token' not in browser_session
