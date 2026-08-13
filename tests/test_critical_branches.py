import io
import time
import uuid
from datetime import datetime, timedelta

import pytest
from flask import g
from werkzeug.datastructures import FileStorage

from app.economy.inventory.transactions import (
    CoinError, InventoryError, deduct_coins, market_treasury_id,
    release_inventory, reserve_inventory, tax_transfer, transfer_coins,
    transfer_inventory,
)
from app.extensions import db, socketio
from app.models.room import Room, RoomPlayer
from app.models.settings import TwoFactorAuth
from app.models.shop import ShopItem, UserInventory
from app.routes import account as account_routes
from app.routes import auth as auth_routes
from app.routes import two_factor as two_factor_routes
from app.services.supabase import SupabaseError, SupabaseService
from conftest import make_user


def _login(client, user):
    with client.session_transaction() as browser_session:
        browser_session['_user_id'] = str(user.id)
        browser_session['_fresh'] = True
    g.pop('_login_user', None)


def test_auth_validation_logout_realtime_and_otp(app, client, user,
                                                 monkeypatch):
    with pytest.raises(SupabaseError):
        auth_routes._auth_uuid({})
    with app.test_request_context('/'):
        assert auth_routes._otp_allowed('127.0.0.1')
        assert not auth_routes._otp_allowed('127.0.0.1')
        assert auth_routes._complete_login(user).status_code == 302
        auth_routes.session['2fa_pending_token'] = 'invalid'
        assert auth_routes._complete_login(user).status_code == 302

    response = client.post('/auth/register', data={})
    assert response.status_code == 200
    response = client.post('/auth/register', data={
        'username': user.username, 'email': 'other@example.com',
        'password': 'Tr1v!aVerse99', 'confirm_password': 'Tr1v!aVerse99'})
    assert response.status_code == 200

    _login(client, user)
    monkeypatch.setitem(app.config, 'SUPABASE_AUTH_ENABLED', False)
    response = client.get('/auth/realtime-session')
    assert response.status_code == 503
    response = client.get('/auth/logout')
    assert response.status_code == 302 and user.is_online is False


def test_auth_reset_change_and_resend_branches(app, client, user,
                                               monkeypatch):
    token = user.get_reset_password_token()
    assert client.get(f'/auth/reset-password/{token}').status_code == 200
    assert client.post(f'/auth/reset-password/{token}', data={
        'password': 'a', 'confirm_password': 'b'}).status_code == 200
    assert client.post(f'/auth/reset-password/{token}', data={
        'password': 'weak', 'confirm_password': 'weak'}).status_code == 200
    response = client.post(f'/auth/reset-password/{token}', data={
        'password': 'N3w!Password99',
        'confirm_password': 'N3w!Password99'})
    assert response.status_code == 302

    _login(client, user)
    monkeypatch.setitem(app.config, 'SUPABASE_AUTH_ENABLED', False)
    assert client.post('/auth/change-password', data={
        'current_password': 'wrong', 'new_password': 'N3w!Password99',
        'confirm_password': 'N3w!Password99'}).status_code == 302
    user.set_password('Current!Pass99')
    db.session.commit()
    assert client.post('/auth/change-password', data={
        'current_password': 'Current!Pass99', 'new_password': 'one',
        'confirm_password': 'two'}).status_code == 302

    with client.session_transaction() as browser_session:
        browser_session.clear()
        browser_session['verify_user_id'] = user.id
    g.pop('_login_user', None)
    user.is_verified = False
    db.session.commit()
    monkeypatch.setattr('app.utils.email.send_otp_email',
                        lambda *args: None)
    assert client.get('/auth/resend-otp').status_code == 302
    assert client.get('/auth/resend-otp').status_code == 302


def test_account_error_branches(app, client, user, monkeypatch):
    empty = FileStorage(stream=io.BytesIO(b''), filename='empty.png')
    with pytest.raises(ValueError):
        account_routes._normalized_image(empty)
    huge = FileStorage(
        stream=io.BytesIO(b'x' * (6 * 1024 * 1024 + 1)),
        filename='huge.png')
    with pytest.raises(ValueError):
        account_routes._normalized_image(huge)

    _login(client, user)
    monkeypatch.setattr(
        SupabaseService, 'enabled', staticmethod(lambda: True))
    response = client.post('/account/update-profile', data={
        'avatar': (io.BytesIO(b'bad'), 'bad.png')},
        content_type='multipart/form-data')
    assert response.status_code == 302
    other = make_user(username='profileother', email='profile@example.com')
    db.session.commit()
    assert client.get(f'/account/profile/{other.id}').status_code == 200


def test_supabase_mfa_failure_branches(app, client, user, monkeypatch):
    user.auth_user_id = uuid.uuid4()
    db.session.commit()
    _login(client, user)
    monkeypatch.setattr(
        SupabaseService, 'enabled', staticmethod(lambda: True))
    monkeypatch.setattr(two_factor_routes, 'access_token', lambda **kwargs: None)
    assert '/auth/login' in client.get('/two-factor/setup').location

    monkeypatch.setattr(two_factor_routes, 'access_token',
                        lambda **kwargs: 'access')
    monkeypatch.setattr(
        SupabaseService, 'enroll_totp',
        lambda *args: (_ for _ in ()).throw(SupabaseError('failure')))
    assert '/account/settings' in client.get('/two-factor/setup').location
    assert '/two-factor/setup' in client.post(
        '/two-factor/enable', data={}).location
    assert '/account/settings' in client.post(
        '/two-factor/disable', data={}).location

    with client.session_transaction() as browser_session:
        browser_session['pending_supabase_factor_id'] = str(uuid.uuid4())
    monkeypatch.setattr(
        SupabaseService, 'challenge_totp',
        lambda *args: (_ for _ in ()).throw(SupabaseError('invalid code')))
    assert '/two-factor/setup' in client.post(
        '/two-factor/enable', data={'code': '000000'}).location

    monkeypatch.setattr(
        SupabaseService, 'enabled', staticmethod(lambda: False))
    assert client.get('/two-factor/setup').status_code == 200


def test_economy_policy_error_branches(user, buyer):
    item = ShopItem(
        name='Critical item', description='x', price=1, item_type='badge')
    inventory = UserInventory(
        user_id=user.id, item=item, quantity=1, locked_quantity=0)
    buyer_inventory = UserInventory(
        user_id=buyer.id, item=item, quantity=2, locked_quantity=0)
    db.session.add_all([item, inventory, buyer_inventory])
    db.session.commit()
    with pytest.raises(InventoryError):
        reserve_inventory(inventory, 0)
    with pytest.raises(InventoryError):
        reserve_inventory(inventory, 2)
    with pytest.raises(InventoryError):
        release_inventory(inventory, 0)
    with pytest.raises(InventoryError):
        transfer_inventory(inventory, buyer, 1)
    reserve_inventory(inventory, 1)
    transfer_inventory(inventory, buyer, 1)
    assert buyer_inventory.quantity == 3
    with pytest.raises(CoinError):
        deduct_coins(user, 0)
    with pytest.raises(CoinError):
        deduct_coins(user, user.coins + 1)
    with pytest.raises(CoinError):
        transfer_coins(user, buyer, 0)
    transfer_coins(user, None, 1, 'escrow')
    transfer_coins(user, buyer, 1, 'peer transfer')
    assert buyer.coins > 0
    assert market_treasury_id() == 0
    tax_transfer(1)


def test_game_socket_rejects_invalid_starts(app, client, user):
    _login(client, user)
    live = socketio.test_client(app, flask_test_client=client)
    live.emit('start_game', {'room_code': 'missing'})
    assert any(e['name'] == 'error' for e in live.get_received())
    room = Room(code='EMPTY1', name='Empty', host_id=user.id,
                question_count=1)
    db.session.add(room)
    db.session.flush()
    db.session.add(RoomPlayer(room_id=room.id, user_id=user.id))
    db.session.commit()
    live.emit('start_game', {'room_code': room.code})
    assert any(e['name'] == 'error' for e in live.get_received())
    live.emit('request_question', {'room_code': 'missing'})
    assert any(e['name'] == 'error' for e in live.get_received())
    live.emit('next_question', {'room_code': 'missing'})
    live.emit('leave_game', {'room_code': 'missing'})
    live.emit('skip_question', {'room_code': 'missing'})
    live.emit('game_admin_kick_player', {
        'room_code': room.code, 'user_id': user.id})
    live.emit('recover_game', {'room_code': 'missing'})
    live.disconnect()
