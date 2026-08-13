import requests
from app.extensions import db
from app.models.user import DiscordAccount, User
from app.services.supabase import SupabaseService
from conftest import make_user


class Response:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status

    def json(self):
        return self.payload


def _legacy(app, monkeypatch):
    monkeypatch.setitem(app.config, 'SUPABASE_AUTH_ENABLED', False)
    monkeypatch.setitem(app.config, 'DISCORD_CLIENT_ID', 'client')
    monkeypatch.setitem(app.config, 'DISCORD_CLIENT_SECRET', 'secret')
    monkeypatch.setattr(
        SupabaseService, 'enabled', staticmethod(lambda: False))


def _discord_http(monkeypatch, *, discord_id='1234',
                  email='discord@example.com', username='discorder'):
    monkeypatch.setattr(
        'app.routes.auth.requests.post',
        lambda *args, **kwargs: Response({'access_token': 'discord-access'}))
    monkeypatch.setattr(
        'app.routes.auth.requests.get',
        lambda *args, **kwargs: Response({
            'id': discord_id, 'username': username, 'email': email,
            'avatar': 'avatarhash'}))


def _state(client, value='valid-state'):
    with client.session_transaction() as browser_session:
        browser_session['discord_oauth_state'] = value


def test_legacy_discord_redirect_and_invalid_callback(
        app, client, monkeypatch):
    _legacy(app, monkeypatch)
    response = client.get('/auth/discord')
    assert response.status_code == 302
    assert 'discord.com/api/oauth2/authorize' in response.location
    with client.session_transaction() as browser_session:
        state = browser_session['discord_oauth_state']
    assert state and 'state=' in response.location
    response = client.get('/auth/discord/callback?state=wrong&code=x')
    assert response.status_code == 302 and '/auth/login' in response.location


def test_legacy_discord_existing_identity(app, client, user, monkeypatch):
    _legacy(app, monkeypatch)
    account = DiscordAccount(
        user_id=user.id, discord_id='1234', discord_username='old')
    db.session.add(account)
    db.session.commit()
    _discord_http(monkeypatch)
    _state(client)
    response = client.get(
        '/auth/discord/callback?state=valid-state&code=valid')
    assert response.status_code == 302 and '/dashboard' in response.location
    assert account.access_token == 'discord-access'
    assert account.discord_username == 'discorder'


def test_legacy_discord_matches_email_and_links(
        app, client, user, monkeypatch):
    _legacy(app, monkeypatch)
    user.email = 'discord@example.com'
    db.session.commit()
    _discord_http(monkeypatch)
    _state(client)
    response = client.get(
        '/auth/discord/callback?state=valid-state&code=valid')
    assert response.status_code == 302 and '/dashboard' in response.location
    assert DiscordAccount.query.filter_by(user_id=user.id).count() == 1


def test_legacy_discord_creates_verified_user_without_email(
        app, client, monkeypatch):
    _legacy(app, monkeypatch)
    _discord_http(
        monkeypatch, discord_id='9876', email=None, username='newdiscord')
    _state(client)
    response = client.get(
        '/auth/discord/callback?state=valid-state&code=valid')
    assert response.status_code == 302 and '/dashboard' in response.location
    user = User.query.filter_by(username='newdiscord').one()
    assert user.email == '9876@discord.user' and user.is_verified
    assert user.discord_account.discord_id == '9876'


def test_legacy_discord_network_failure_is_safe(
        app, client, monkeypatch):
    _legacy(app, monkeypatch)
    monkeypatch.setattr(
        'app.routes.auth.requests.post',
        lambda *args, **kwargs: (_ for _ in ()).throw(
            requests.Timeout('timeout')))
    _state(client)
    response = client.get(
        '/auth/discord/callback?state=valid-state&code=valid')
    assert response.status_code == 302 and '/auth/login' in response.location
