from app.extensions import db, socketio
from app.models.chat import ChatChannel, ChatMember, ChatMessage
from app.models.guild import Guild, GuildBoss, GuildMember, GuildRank
from app.models.room import Room, RoomPlayer
from app.models.tournament import (
    Tournament, TournamentMatch, TournamentParticipant,
)
from app.models.notification import Notification
from conftest import make_user


def _login(client, user):
    with client.session_transaction() as browser_session:
        browser_session['_user_id'] = str(user.id)
        browser_session['_fresh'] = True


def _events(client, name, namespace=None):
    return [event for event in client.get_received(namespace)
            if event['name'] == name]


def test_room_and_chat_socket_flows(app, client, user):
    guest = make_user(username='roomguest', email='roomguest@example.com')
    room = Room(code='SOCK01', name='Socket room', host_id=user.id)
    channel = ChatChannel(
        name='Private test', channel_type='private', is_private=True)
    db.session.add_all([room, channel])
    db.session.flush()
    db.session.add_all([
        RoomPlayer(room=room, user_id=user.id),
        RoomPlayer(room=room, user_id=guest.id),
        ChatMember(channel_id=channel.id, user_id=user.id),
    ])
    db.session.commit()
    _login(client, user)
    live = socketio.test_client(app, flask_test_client=client)
    live.emit('join_chat', {})
    assert _events(live, 'error')
    live.emit('send_message', {'channel_id': channel.id, 'content': ''})
    assert _events(live, 'error')
    assert _events(live, 'room_joined') == []
    live.emit('join_room', {'room_code': 'missing'})
    assert _events(live, 'error')
    live.emit('join_room', {'room_code': room.code})
    assert _events(live, 'room_joined')
    live.emit('toggle_ready', {'room_code': room.code})
    assert _events(live, 'player_ready_changed')
    live.emit('send_chat', {'room_code': room.code, 'message': 'hello'})
    assert _events(live, 'chat_message')
    live.emit('invite_to_room', {'room_code': room.code,
                                 'friend_id': guest.id})
    assert _events(live, 'invite_sent')
    assert Notification.query.filter_by(user_id=guest.id).count() == 1

    live.emit('join_chat', {'channel_id': channel.id})
    assert _events(live, 'joined')
    live.emit('send_message', {'channel_id': channel.id,
                               'content': '<img onerror=alert(1)>'})
    message = ChatMessage.query.one()
    assert message.content == '<img onerror=alert(1)>'
    assert _events(live, 'new_message')
    live.emit('typing', {'channel_id': channel.id, 'is_typing': True})
    live.emit('edit_message', {'message_id': message.id,
                               'content': 'safe edit'})
    assert _events(live, 'message_edited')
    live.emit('delete_message', {'message_id': message.id})
    assert _events(live, 'message_deleted')
    live.emit('leave_chat', {'channel_id': channel.id})
    live.emit('kick_player', {'room_code': room.code, 'user_id': guest.id})
    assert _events(live, 'player_kicked')
    live.disconnect()


def test_private_chat_membership_is_enforced(app, client, user):
    channel = ChatChannel(
        name='Members only', channel_type='private', is_private=True)
    db.session.add(channel)
    db.session.commit()
    _login(client, user)
    live = socketio.test_client(app, flask_test_client=client)
    live.emit('join_chat', {'channel_id': channel.id})
    assert _events(live, 'error')[0]['args'][0]['message'] == 'Access denied'
    live.disconnect()


def test_notification_guild_and_tournament_sockets(app, client, user):
    guest = make_user(username='notifyguest', email='notifyguest@example.com')
    guild = Guild(name='Socket guild', tag='SOCK', owner_id=user.id)
    db.session.add(guild)
    db.session.flush()
    rank = GuildRank(guild_id=guild.id, name='Owner')
    db.session.add(rank)
    db.session.flush()
    member = GuildMember(guild_id=guild.id, user_id=user.id, rank_id=rank.id)
    boss = GuildBoss(name='Test boss', hp=100, max_hp=100, is_active=True)
    tournament = Tournament(name='Socket cup', status='active')
    db.session.add_all([member, boss, tournament])
    db.session.flush()
    player_a = TournamentParticipant(
        tournament_id=tournament.id, user_id=user.id)
    player_b = TournamentParticipant(
        tournament_id=tournament.id, user_id=guest.id)
    db.session.add_all([player_a, player_b])
    db.session.flush()
    match = TournamentMatch(
        tournament_id=tournament.id, player_a_id=player_a.id,
        player_b_id=player_b.id)
    db.session.add(match)
    db.session.commit()
    _login(client, user)

    notifications = socketio.test_client(
        app, namespace='/notifications', flask_test_client=client)
    notifications.emit(
        'direct_message', {'to_user_id': guest.id, 'message': 'hi'},
        namespace='/notifications')
    assert _events(notifications, 'message_sent', '/notifications')
    assert Notification.query.filter_by(user_id=guest.id).count() == 1
    notifications.disconnect(namespace='/notifications')

    live = socketio.test_client(app, flask_test_client=client)
    live.emit('join_guild', {})
    assert _events(live, 'error')
    live.emit('join_guild', {'guild_id': guild.id})
    assert _events(live, 'guild_joined')
    live.emit('guild_chat', {'guild_id': guild.id, 'content': 'guild hello'})
    assert _events(live, 'guild_message')
    live.emit('guild_boss_attack', {'guild_id': guild.id, 'damage': 100})
    assert _events(live, 'boss_damage')
    assert GuildBoss.query.one().is_active is False
    live.emit('guild_war_start', {
        'guild_id': guild.id, 'target_guild_id': 999})
    assert _events(live, 'war_started')
    live.emit('leave_guild', {'guild_id': guild.id})

    live.emit('join_tournament', {})
    assert _events(live, 'error')
    live.emit('join_tournament', {'tournament_id': 999999})
    assert _events(live, 'error')
    live.emit('join_tournament', {'tournament_id': tournament.id})
    assert _events(live, 'tournament_joined')
    live.emit('tournament_ready', {'tournament_id': tournament.id})
    assert _events(live, 'player_ready')
    live.emit('tournament_match_start', {
        'tournament_id': tournament.id, 'match_id': match.id})
    assert _events(live, 'match_started')
    live.emit('tournament_match_result', {
        'tournament_id': tournament.id, 'match_id': match.id,
        'winner_id': player_a.id, 'score_a': 10, 'score_b': 5})
    assert _events(live, 'match_result')
    assert TournamentMatch.query.one().status == 'completed'
    live.emit('tournament_next_round', {'tournament_id': tournament.id})
    assert _events(live, 'next_round')
    live.emit('tournament_leave', {'tournament_id': tournament.id})
    live.disconnect()
