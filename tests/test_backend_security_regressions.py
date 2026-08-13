from datetime import datetime, timedelta, timezone

import pytest

from app.economy.auction.service import create_auction, place_bid
from app.models.question import Answer, Category, Question
from app.models.user import DiscordAccount


def _login(client, user):
    with client.session_transaction() as browser_session:
        browser_session['_user_id'] = str(user.id)
        browser_session['_fresh'] = True


def _make_question(db):
    category = Category(name='Classic validation', slug='classic-validation')
    question = Question(
        category=category,
        question_text='Which answer is correct?',
        is_active=True,
    )
    correct = Answer(question=question, answer_text='Correct', is_correct=True)
    db.session.add_all([category, question, correct])
    db.session.flush()
    return question, correct


def test_classic_submit_answer_rejects_non_integer_ids(client, db, user):
    question, _ = _make_question(db)
    db.session.commit()
    _login(client, user)

    response = client.post('/quiz/submit_answer', json={
        'question_id': question.id,
        'answer_id': 'not-an-integer',
    })

    assert response.status_code == 400
    assert response.get_json()['error'] == 'answer_id must be an integer'


def test_solo_check_answer_rejects_non_integer_ids(client, db, user):
    question, _ = _make_question(db)
    db.session.commit()
    _login(client, user)

    response = client.post('/quiz/solo/check_answer', json={
        'question_id': question.id,
        'answer_id': 'not-an-integer',
    })

    assert response.status_code == 400
    assert response.get_json()['error'] == 'answer_id must be an integer'


@pytest.mark.parametrize('payload', [
    {'correct': 9, 'total': 8},
    {'correct': 0, 'total': 51},
    {'correct': -1, 'total': 10},
    {'correct': True, 'total': 1},
])
def test_solo_submit_rejects_client_tampered_scores(client, user, payload):
    _login(client, user)

    response = client.post('/quiz/solo/submit', json=payload)

    assert response.status_code == 400
    assert 'correct and total must be integers' in response.get_json()['error']


def test_discord_mutation_requires_service_token(app, client, db, user):
    app.config['DISCORD_API_TOKEN'] = 'test-discord-token'
    account = DiscordAccount(user_id=user.id, discord_id='discord-123')
    db.session.add(account)
    db.session.commit()

    payload = {'discord_id': 'discord-123', 'amount': 10}
    assert client.post('/api/users/coins/add', json=payload).status_code == 401
    assert client.post(
        '/api/users/coins/add', json=payload,
        headers={'X-Discord-API-Key': 'wrong-token'},
    ).status_code == 401

    response = client.post(
        '/api/users/coins/add', json=payload,
        headers={'X-Discord-API-Key': 'test-discord-token'},
    )
    assert response.status_code == 200
    assert response.get_json()['new_coins'] == 1010


def test_expired_auction_rejects_late_bid(seller, buyer, db):
    from app.models.shop import ShopItem, UserInventory

    item = ShopItem(
        name='Late bid item', price=100, base_price=100,
        item_type='badge', is_active=True,
    )
    db.session.add(item)
    db.session.flush()
    db.session.add(UserInventory(user_id=seller.id, item_id=item.id, quantity=1))
    db.session.flush()
    auction = create_auction(seller, item.id, 100, duration_hours=24)
    auction.ends_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db.session.commit()

    with pytest.raises(Exception, match='ended'):
        place_bid(buyer, auction, 200)


def test_premium_decorator_is_loaded_and_gates_non_premium_users(client, user):
    _login(client, user)

    response = client.post('/premium/daily-premium-reward')

    assert response.status_code in (302, 403)


def test_discord_economy_endpoints_reject_malformed_numbers(app, client, db, user):
    app.config['DISCORD_API_TOKEN'] = 'test-discord-token'
    db.session.add(DiscordAccount(user_id=user.id, discord_id='discord-123'))
    db.session.commit()
    headers = {'X-Discord-API-Key': 'test-discord-token'}

    deposit = client.post('/api/bank/deposit', json={
        'discord_id': 'discord-123', 'amount': 'not-a-number'}, headers=headers)
    coinflip = client.post('/api/gamble/coinflip', json={
        'discord_id': 'discord-123', 'bet': 'not-a-number'}, headers=headers)

    assert deposit.status_code == 400
    assert coinflip.status_code == 400


def test_world_boss_mutations_require_service_token(app, client):
    app.config['DISCORD_API_TOKEN'] = 'test-discord-token'
    payload = {'name': 'Test Boss', 'hp': 1000}

    assert client.post('/boss/spawn', json=payload).status_code == 401
    headers = {'X-Discord-API-Key': 'test-discord-token'}
    spawned = client.post('/boss/spawn', json=payload, headers=headers)
    assert spawned.status_code == 201
    boss_id = spawned.get_json()['id']

    damage = client.post('/boss/damage', json={
        'boss_id': boss_id, 'damage': 10,
    }, headers=headers)
    assert damage.status_code == 200
    assert damage.get_json()['current_hp'] == 990


def test_discord_bot_admin_compatibility_routes_are_protected(app, client, db, user):
    from app.models.shop import ShopItem, UserInventory

    app.config['DISCORD_API_TOKEN'] = 'test-discord-token'
    db.session.add(DiscordAccount(user_id=user.id, discord_id='discord-123'))
    item = ShopItem(
        name='Admin grant item', price=100, base_price=100,
        item_type='badge', is_active=True,
    )
    db.session.add(item)
    db.session.commit()
    headers = {'X-Discord-API-Key': 'test-discord-token'}

    assert client.get('/api/admin/server-stats').status_code == 401
    stats = client.get('/api/admin/server-stats', headers=headers)
    assert stats.status_code == 200
    assert stats.get_json()['total_players'] == 1

    banned = client.post(
        f'/api/admin/users/{user.id}/toggle-ban', headers=headers)
    assert banned.status_code == 200
    assert banned.get_json()['is_banned'] is True

    granted = client.post('/api/admin/give-item', json={
        'discord_id': 'discord-123', 'item_id': item.id,
    }, headers=headers)
    assert granted.status_code == 200
    assert UserInventory.query.filter_by(
        user_id=user.id, item_id=item.id).one().quantity == 1
