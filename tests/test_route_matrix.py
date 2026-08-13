"""Exercise every safe GET route as both a visitor and a signed-in user."""
from uuid import UUID

from flask import url_for
from werkzeug.routing import IntegerConverter, UUIDConverter


SKIP_ENDPOINTS = {'static', 'auth.logout', 'auth.discord_login'}


def _value(converter, name):
    if isinstance(converter, IntegerConverter):
        return 999999
    if isinstance(converter, UUIDConverter):
        return UUID('00000000-0000-0000-0000-000000000001')
    if 'code' in name:
        return 'TEST01'
    if 'username' in name:
        return 'testuser'
    return 'test'


def _get_urls(app):
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            if 'GET' not in rule.methods or rule.endpoint in SKIP_ENDPOINTS:
                continue
            values = {
                name: _value(converter, name)
                for name, converter in rule._converters.items()
            }
            yield rule.endpoint, url_for(rule.endpoint, **values)


def _post_urls(app):
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            if 'POST' not in rule.methods:
                continue
            values = {
                name: _value(converter, name)
                for name, converter in rule._converters.items()
            }
            yield rule.endpoint, url_for(rule.endpoint, **values)


def test_all_get_routes_avoid_internal_errors(app, client, user):
    failures = []
    for authenticated in (False, True):
        for endpoint, path in _get_urls(app):
            with client.session_transaction() as browser_session:
                browser_session.clear()
                if authenticated:
                    browser_session['_user_id'] = str(user.id)
                    browser_session['_fresh'] = True
            response = client.get(path, follow_redirects=False)
            if response.status_code >= 500:
                failures.append((authenticated, endpoint, path,
                                 response.status_code))
    assert not failures, failures


def test_all_post_routes_reject_empty_input_without_internal_errors(
        app, client, user):
    """Invalid/empty input is still untrusted input and must never raise 500."""
    failures = []
    for authenticated in (False, True):
        for endpoint, path in _post_urls(app):
            with client.session_transaction() as browser_session:
                browser_session.clear()
                if authenticated:
                    browser_session['_user_id'] = str(user.id)
                    browser_session['_fresh'] = True
            try:
                response = client.post(
                    path, json={}, follow_redirects=False)
                if response.status_code >= 500:
                    failures.append((authenticated, endpoint, path,
                                     response.status_code))
            except Exception as exc:
                failures.append((authenticated, endpoint, path,
                                 type(exc).__name__, str(exc)))
    assert not failures, failures
