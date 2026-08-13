from app.models.question import Answer, Category, Question


def _make_question(db):
    category = Category(name="Quiz V2 Test", slug="quiz-v2-test")
    db.session.add(category)
    db.session.flush()

    question = Question(
        category_id=category.id,
        question_text="Which answer is correct?",
        is_active=True,
    )
    db.session.add(question)
    db.session.flush()

    correct = Answer(
        question_id=question.id,
        answer_text="Correct",
        is_correct=True,
    )
    incorrect = Answer(
        question_id=question.id,
        answer_text="Incorrect",
        is_correct=False,
    )
    db.session.add_all([correct, incorrect])
    db.session.commit()
    return question, correct, incorrect


def test_quiz_v2_check_answer_rejects_non_integer_ids(client, db):
    question, _, _ = _make_question(db)

    response = client.post(
        "/quiz/v2/api/check_answer",
        json={"question_id": question.id, "answer_id": "not-an-integer"},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Question and answer IDs must be integers"
    }


def test_quiz_v2_check_answer_accepts_numeric_string_ids(client, db):
    question, correct, _ = _make_question(db)

    response = client.post(
        "/quiz/v2/api/check_answer",
        json={"question_id": str(question.id), "answer_id": str(correct.id)},
    )

    assert response.status_code == 200
    assert response.get_json()["correct"] is True
    assert response.get_json()["correct_answer_id"] == correct.id


def test_authenticated_dashboard_links_solo_quiz_to_lobby_flow(client, db):
    from conftest import make_user

    user = make_user(username="navuser", email="nav@example.test")
    db.session.commit()

    login = client.post(
        "/auth/login",
        data={"username": user.username, "password": "Tr1v!aVerse99"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert b"/rooms/?solo=1" in response.data
    assert b"/quiz/solo/start" not in response.data
