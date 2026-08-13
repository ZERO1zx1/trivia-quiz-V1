from app.models.room import Room, RoomPlayer
from app.utils import ai as ai_utils
from conftest import make_user


def test_ai_generate_room_creates_host_membership(client, db, monkeypatch):
    user = make_user(username="aiuser", email="aiuser@example.test")
    db.session.commit()

    monkeypatch.setattr(
        ai_utils,
        "generate_trivia_question",
        lambda topic, difficulty: {
            "question": f"Question about {topic}",
            "correct_answer": "Correct",
            "wrong_answers": ["Wrong A", "Wrong B", "Wrong C"],
        },
    )

    login = client.post(
        "/auth/login",
        data={"username": user.username, "password": "Tr1v!aVerse99"},
    )
    assert login.status_code == 302

    response = client.post(
        "/quiz/ai/generate-room",
        json={"topic": "Science", "difficulty": "medium"},
    )

    assert response.status_code == 200
    room_code = response.get_json()["room_code"]
    room = Room.query.filter_by(code=room_code).one()
    player = RoomPlayer.query.filter_by(
        room_id=room.id, user_id=user.id
    ).one()
    assert room.host_id == user.id
    assert player.is_ready is True
