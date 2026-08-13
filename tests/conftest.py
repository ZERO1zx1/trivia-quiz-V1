"""Shared test fixtures for TriviaVerse regression / integration tests.

All fixtures build on Flask's 'testing' config (in-memory SQLite) so no
database or secrets are required to run the suite.
"""
import pytest

from app import create_app
from app.extensions import db as _db
from app.models.user import User


@pytest.fixture(scope='session')
def app():
    application = create_app('testing')
    application.config['SERVER_NAME'] = 'localhost'
    application.config['WTF_CSRF_ENABLED'] = False
    application.config['TESTING'] = True
    return application


@pytest.fixture(autouse=True)
def _push_context(app):
    ctx = app.app_context()
    ctx.push()
    yield
    ctx.pop()


@pytest.fixture(autouse=True)
def db(app):
    """Fresh schema + seeded rows per test."""
    _db.session.remove()
    _db.create_all()
    yield _db
    _db.session.remove()
    _db.drop_all()


@pytest.fixture
def client(app, db):
    return app.test_client()


def make_user(username='testuser', email='test@example.com', password=None,
              verified=True, coins=1000):
    """Helper to create a user (coins default high enough for tests)."""
    from app.models.user import User
    user = User(
        username=username,
        email=email,
        display_name=username,
        coins=coins,
    )
    user.set_password(password or 'Tr1v!aVerse99')
    user.is_verified = verified
    _db.session.add(user)
    _db.session.flush()
    return user


@pytest.fixture
def user(db):
    return make_user()


@pytest.fixture
def unverified_user(db):
    return make_user(username='unverified', email='un@example.com',
                     verified=False)


@pytest.fixture
def buyer(db):
    return make_user(username='buyer', email='buyer@example.com')


@pytest.fixture
def seller(db):
    return make_user(username='seller', email='seller@example.com')
