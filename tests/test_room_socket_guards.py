from app.extensions import db, socketio
from app.models.notification import Notification
from app.models.question import Category, Question
from app.models.room import Room, RoomPlayer
from app.sockets import game_socket
from conftest import make_user


def _login(client, user):
    with client.session_transaction() as browser_session:
        browser_session["_user_id"] = str(user.id)
        browser_session["_fresh"] = True


def _events(socket_client, name):
    return [item for item in socket_client.get_received() if item["name"] == name]


def test_lobby_start_rejects_insufficient_questions(app, client, db):
    host = make_user(username="roomhost", email="roomhost@example.test")
    guest = make_user(username="roomguest", email="roomguest@example.test")
    category = Category(name="Socket Guard", slug="socket-guard")
    question = Question(category=category, question_text="Only one question")
    room = Room(
        code="GUARD1",
        name="Guard room",
        host_id=host.id,
        category_id=category.id,
        difficulty="mixed",
        question_count=2,
    )
    db.session.add_all([
        category,
        question,
        room,
        RoomPlayer(room=room, user_id=host.id, is_ready=True),
        RoomPlayer(room=room, user_id=guest.id, is_ready=True),
    ])
    db.session.commit()

    _login(client, host)
    live = socketio.test_client(app, flask_test_client=client)
    live.emit("start_game_lobby", {"room_code": "GUARD1"})

    errors = _events(live, "error")
    assert errors
    assert "Not enough questions" in errors[0]["args"][0]["message"]
    assert Room.query.filter_by(code="GUARD1").one().status == "waiting"
    assert not Room.query.filter_by(code="GUARD1").one().match
    assert "GUARD1" not in game_socket.game_states
    live.disconnect()


def test_room_invite_requires_membership(app, client, db):
    owner = make_user(username="inviteowner", email="inviteowner@example.test")
    outsider = make_user(username="inviteoutsider", email="inviteoutsider@example.test")
    recipient = make_user(username="inviterecipient", email="inviterecipient@example.test")
    room = Room(code="INV001", name="Invite room", host_id=owner.id)
    db.session.add_all([room, RoomPlayer(room=room, user_id=owner.id)])
    db.session.commit()

    _login(client, outsider)
    live = socketio.test_client(app, flask_test_client=client)
    live.emit("invite_to_room", {
        "room_code": "INV001",
        "friend_id": recipient.id,
    })

    errors = _events(live, "error")
    assert errors
    assert "not a member" in errors[0]["args"][0]["message"]
    assert Notification.query.filter_by(user_id=recipient.id).count() == 0
    live.disconnect()
