"""Authentication, email verification and 2FA integration tests.

Covers FIX-002 (verification gate), FIX-003 (canonical 2FA model),
FIX-004 (2FA enforced before login_user, signed pending token), and
FIX-023 (canonical password policy). Built on Flask's 'testing' config
with an in-memory SQLite database — no secrets or services required.
"""
import pyotp

from app.extensions import db as _db
from app.models.settings import TwoFactorAuth
from app.models.user import User
from app.shared.password_policy import validate_password
from app.utils.two_factor import generate_2fa_secret, verify_2fa_code


def make_user(username='testuser', email='test@example.com', password=None,
              verified=True, coins=1000):
    from app.models.user import User as _User
    user = _User(username=username, email=email, display_name=username,
                 coins=coins)
    user.set_password(password or 'Tr1v!aVerse99')
    user.is_verified = verified
    _db.session.add(user)
    _db.session.flush()
    return user


def _register(client, username='reguser', email='reg@example.com',
              password='Tr1v!aVerse99'):
    return client.post('/auth/register', data={
        'username': username, 'email': email,
        'password': password, 'confirm_password': password,
    }, follow_redirects=False)


# ---------- FIX-002: email verification gate ----------

def test_unverified_user_redirected_to_verify_after_login(client):
    """A user with is_verified=False must never get a session; they are
    bounced to the OTP verification page instead."""
    make_user(username='unv', email='unv@example.com', verified=False)
    response = client.post('/auth/login', data={
        'username': 'unv', 'password': 'Tr1v!aVerse99',
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/verify' in response.headers['Location']

    # The user must still not be authenticated.
    get = client.get('/dashboard/', follow_redirects=False)
    assert get.status_code in (302, 401)

    # verify_user_id is stashed so the OTP form can target this account.
    with client.session_transaction() as sess:
        assert 'verify_user_id' in sess
        assert sess.get('_user_id') is None


def test_verified_user_logs_in_normally(client):
    """A fully verified user (no 2FA) completes the normal login flow."""
    make_user(username='v', email='v@example.com', verified=True)
    response = client.post('/auth/login', data={
        'username': 'v', 'password': 'Tr1v!aVerse99',
    }, follow_redirects=False)
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert 'verify_user_id' not in sess
        assert '2fa_user_id' not in sess
        assert sess.get('_user_id') is not None


def test_registration_marks_new_account_unverified(client):
    _db.session.commit()
    before = User.query.count()
    response = _register(client)
    assert response.status_code == 302
    assert '/auth/verify' in response.headers['Location']
    _db.session.commit()
    user = User.query.filter_by(username='reguser').first()
    assert user is not None and not user.is_verified
    assert User.query.count() == before + 1


def test_otp_verify_marks_user_verified(client):
    """Submitting the correct OTP clears the gate and lets the user log in."""
    make_user(username='otpuser', email='otp@example.com', verified=False)
    user = User.query.filter_by(username='otpuser').first()
    user.generate_otp()
    _db.session.commit()
    code = user.otp_code

    client.post('/auth/login', data={
        'username': 'otpuser', 'password': 'Tr1v!aVerse99',
    }, follow_redirects=False)

    response = client.post('/auth/verify', data={'otp': code},
                           follow_redirects=False)
    _db.session.commit()
    assert User.query.filter_by(username='otpuser').first().is_verified
    assert response.status_code == 302
    assert 'verify' not in response.headers['Location'].lower()


def test_wrong_otp_does_not_verify(client):
    make_user(username='badotp', email='badotp@example.com', verified=False)
    User.query.filter_by(username='badotp').first().generate_otp()
    _db.session.commit()

    client.post('/auth/login', data={
        'username': 'badotp', 'password': 'Tr1v!aVerse99',
    }, follow_redirects=False)
    client.post('/auth/verify', data={'otp': '000000'}, follow_redirects=False)
    _db.session.commit()
    assert not User.query.filter_by(username='badotp').first().is_verified


# ---------- FIX-003 / FIX-004: 2FA enforced before login_user ----------

def _enable_2fa(user):
    """Simulate the 2FA setup flow writing the canonical model fields."""
    secret = generate_2fa_secret()
    twofa = TwoFactorAuth(
        user_id=user.id, is_enabled=True,
        secret_key=secret, method='app',
    )
    _db.session.add(twofa)
    _db.session.commit()
    return secret


def test_2fa_enabled_user_redirected_to_verify(client):
    """A password-correct login must NOT create a session when 2FA is on —
    the user is intercepted to the TOTP verify endpoint."""
    user = make_user(username='fauser', email='fa@example.com', verified=True)
    _enable_2fa(user)

    response = client.post('/auth/login', data={
        'username': 'fauser', 'password': 'Tr1v!aVerse99',
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/two-factor' in response.headers['Location']

    with client.session_transaction() as sess:
        assert '2fa_user_id' in sess
        assert '2fa_pending_token' in sess
        assert 'user_id' not in sess


def test_2fa_wrong_totp_rejected(client):
    user = make_user(username='fa2', email='fa2@example.com', verified=True)
    secret = _enable_2fa(user)
    client.post('/auth/login', data={
        'username': 'fa2', 'password': 'Tr1v!aVerse99',
    }, follow_redirects=False)
    bad_code = str(int(pyotp.TOTP(secret).now()) + 1).zfill(6)
    response = client.post('/two-factor/verify', data={'code': bad_code},
                           follow_redirects=False)
    _db.session.commit()
    # A wrong TOTP re-renders the verification form and keeps the user
    # logged out.
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get('_user_id') is None


def test_2fa_correct_totp_completes_login(client):
    user = make_user(username='fa3', email='fa3@example.com', verified=True)
    secret = _enable_2fa(user)
    client.post('/auth/login', data={
        'username': 'fa3', 'password': 'Tr1v!aVerse99',
    }, follow_redirects=False)

    code = pyotp.TOTP(secret).now()
    response = client.post('/two-factor/verify', data={'code': code},
                           follow_redirects=False)
    _db.session.commit()
    assert response.status_code == 302
    assert 'two-factor' not in response.headers['Location']
    with client.session_transaction() as sess:
        assert '2fa_pending_token' not in sess
        assert sess.get('_user_id') is not None


def test_2fa_replay_of_pending_token_rejected(client):
    """A pending 2FA token is one-shot: re-submitting after success fails."""
    user = make_user(username='fa4', email='fa4@example.com', verified=True)
    secret = _enable_2fa(user)
    client.post('/auth/login', data={
        'username': 'fa4', 'password': 'Tr1v!aVerse99',
    }, follow_redirects=False)
    code = pyotp.TOTP(secret).now()
    client.post('/two-factor/verify', data={'code': code},
                follow_redirects=False)

    # Replay: another verify attempt without a fresh pending token.
    response = client.post('/two-factor/verify', data={'code': code},
                           follow_redirects=False)
    assert response.status_code == 302
    assert 'login' in response.headers['Location']


def test_2fa_disable_requires_valid_code(client):
    """2FA cannot be turned off without proving the current TOTP."""
    user = make_user(username='fa5', email='fa5@example.com', verified=True)
    secret = _enable_2fa(user)
    client.post('/auth/login', data={
        'username': 'fa5', 'password': 'Tr1v!aVerse99',
    }, follow_redirects=False)
    code = pyotp.TOTP(secret).now()
    client.post('/two-factor/verify', data={'code': code})

    response = client.post('/two-factor/disable',
                           data={'code': '000000'}, follow_redirects=False)
    _db.session.commit()
    assert TwoFactorAuth.query.filter_by(user_id=user.id,
                                         is_enabled=True).first() is not None
    assert response.status_code in (200, 302)
    # Disabling again with a valid code succeeds.
    valid = pyotp.TOTP(secret).now()
    client.post('/two-factor/disable', data={'code': valid},
                follow_redirects=False)
    _db.session.commit()
    assert TwoFactorAuth.query.filter_by(user_id=user.id,
                                         is_enabled=True).first() is None


# ---------- FIX-023: canonical password policy ----------

def test_password_policy_rejects_weak_passwords():
    assert validate_password('12345')  # errors returned (weak)
    assert validate_password('short')  # errors returned (weak)
    assert validate_password('alllowercase1234')  # errors returned (weak)


def test_password_policy_accepts_strong_password():
    assert validate_password('Tr1v!aVerse99') == []


def test_register_rejects_weak_password(client):
    response = _register(client, password='weak')
    # Policy error flashes and the form re-renders; no user created.
    assert response.status_code == 200
    assert not User.query.filter_by(username='reguser').first()


def test_register_rejects_mismatched_confirmation(client):
    response = client.post('/auth/register', data={
        'username': 'mmuser', 'email': 'mm@example.com',
        'password': 'Tr1v!aVerse99', 'confirm_password': 'Different1!',
    }, follow_redirects=False)
    assert response.status_code == 200
    assert not User.query.filter_by(username='mmuser').first()
