"""Tests for paginated quiz and contest submission histories."""

from __future__ import annotations

from datetime import datetime, timedelta
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from auth import get_current_user
from database import Base, get_db
from models import (
    Contest,
    ContestProblem,
    ContestSubmission,
    QuizSubmission,
    Test,
    User,
)
from routes import contest_routes, quiz_routes


@pytest.fixture
def app_and_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    session = TestingSession()

    user_one = User(
        name="User One",
        email="one@example.com",
        password_hash="hash",
    )
    user_two = User(
        name="User Two",
        email="two@example.com",
        password_hash="hash",
    )
    session.add_all([user_one, user_two])
    session.commit()
    session.refresh(user_one)
    session.refresh(user_two)

    test_one = Test(title="Quiz One", is_active=True)
    test_two = Test(title="Quiz Two", is_active=True)
    session.add_all([test_one, test_two])

    contest_one = Contest(name="Contest One", is_active=True)
    contest_two = Contest(name="Contest Two", is_active=True)
    session.add_all([contest_one, contest_two])
    session.commit()

    problem_one = ContestProblem(
        contest_id=contest_one.id,
        title="Problem One",
        statement="Solve one",
    )
    problem_two = ContestProblem(
        contest_id=contest_one.id,
        title="Problem Two",
        statement="Solve two",
    )
    problem_three = ContestProblem(
        contest_id=contest_two.id,
        title="Problem Three",
        statement="Solve three",
    )
    session.add_all([problem_one, problem_two, problem_three])
    session.commit()

    base_time = datetime(2026, 8, 1, 12, 0, 0)

    # Five submissions for user one, with two identical timestamps to verify
    # deterministic tie-breaking by ID.
    for index in range(5):
        submitted_at = base_time + timedelta(minutes=index)
        if index == 3:
            submitted_at = base_time + timedelta(minutes=2)

        session.add(
            QuizSubmission(
                user_id=user_one.id,
                test_id=(
                    test_one.id
                    if index < 4
                    else test_two.id
                ),
                score=index + 1,
                total_questions=10,
                submitted_at=submitted_at,
            )
        )

    # Another user's records must never be returned.
    session.add(
        QuizSubmission(
            user_id=user_two.id,
            test_id=test_one.id,
            score=10,
            total_questions=10,
            submitted_at=base_time + timedelta(hours=1),
        )
    )

    contest_rows = [
        (contest_one.id, problem_one.id, "ACCEPTED", 100),
        (contest_one.id, problem_one.id, "WRONG_ANSWER", 0),
        (contest_one.id, problem_two.id, "ACCEPTED", 100),
        (contest_two.id, problem_three.id, "PARTIAL", 50),
        (contest_two.id, problem_three.id, "ACCEPTED", 100),
    ]
    for index, (contest_id, problem_id, verdict, score) in enumerate(
        contest_rows
    ):
        session.add(
            ContestSubmission(
                user_id=user_one.id,
                contest_id=contest_id,
                problem_id=problem_id,
                language="python",
                code=f"print({index})",
                verdict=verdict,
                score=score,
                submitted_at=base_time + timedelta(minutes=index),
            )
        )

    session.add(
        ContestSubmission(
            user_id=user_two.id,
            contest_id=contest_one.id,
            problem_id=problem_one.id,
            language="python",
            code="private-other-user-code",
            verdict="ACCEPTED",
            score=100,
            submitted_at=base_time + timedelta(hours=2),
        )
    )
    session.commit()

    app = FastAPI()
    app.include_router(quiz_routes.router, prefix="/quiz")
    app.include_router(contest_routes.router, prefix="/contests")

    def override_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user_one

    yield app, session, {
        "user_one": user_one,
        "user_two": user_two,
        "test_one": test_one,
        "test_two": test_two,
        "contest_one": contest_one,
        "contest_two": contest_two,
        "problem_one": problem_one,
        "problem_two": problem_two,
        "problem_three": problem_three,
    }

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app_and_db):
    app, _, _ = app_and_db
    return TestClient(app)


def test_quiz_first_page_has_total_and_has_more(client):
    response = client.get(
        "/quiz/submissions/me?limit=2&offset=0&sort=newest"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"] == {
        "limit": 2,
        "offset": 0,
        "total": 5,
        "has_more": True,
    }
    assert len(body["items"]) == 2
    assert body["items"][0]["score"] == 5


def test_quiz_middle_and_last_page(client):
    middle = client.get(
        "/quiz/submissions/me?limit=2&offset=2&sort=newest"
    ).json()
    last = client.get(
        "/quiz/submissions/me?limit=2&offset=4&sort=newest"
    ).json()

    assert len(middle["items"]) == 2
    assert middle["pagination"]["has_more"] is True
    assert len(last["items"]) == 1
    assert last["pagination"]["has_more"] is False


def test_quiz_empty_page_and_test_filter(client, app_and_db):
    _, _, data = app_and_db

    filtered = client.get(
        f"/quiz/submissions/me?test_id={data['test_two'].id}"
    )
    assert filtered.status_code == 200
    assert filtered.json()["pagination"]["total"] == 1

    empty = client.get(
        "/quiz/submissions/me?offset=99"
    )
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["pagination"]["has_more"] is False


def test_quiz_sort_is_deterministic_for_equal_timestamps(client):
    response = client.get(
        "/quiz/submissions/me?limit=10&sort=newest"
    )
    ids = [item["id"] for item in response.json()["items"]]

    # Newest sort uses submitted_at DESC, then ID DESC.
    assert ids.index(4) < ids.index(3)


def test_quiz_user_isolation(client):
    body = client.get(
        "/quiz/submissions/me?limit=100"
    ).json()

    assert body["pagination"]["total"] == 5
    assert all(item["user_id"] != 2 for item in body["items"])


def test_quiz_test_specific_history_is_bounded(
    client,
    app_and_db,
):
    _, _, data = app_and_db
    response = client.get(
        f"/quiz/tests/{data['test_one'].id}/my-submissions"
        "?limit=2&sort=oldest"
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["pagination"]["total"] == 4
    assert body["pagination"]["has_more"] is True


def test_contest_filters_and_pagination(client, app_and_db):
    _, _, data = app_and_db

    response = client.get(
        "/contests/submissions/me"
        f"?contest_id={data['contest_one'].id}"
        "&verdict=accepted"
        "&limit=1"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 2
    assert body["pagination"]["limit"] == 1
    assert body["pagination"]["has_more"] is True
    assert body["items"][0]["verdict"] == "ACCEPTED"
    assert (
        body["items"][0]["contest_id"]
        == data["contest_one"].id
    )


def test_contest_problem_filter(client, app_and_db):
    _, _, data = app_and_db

    response = client.get(
        "/contests/submissions/me"
        f"?problem_id={data['problem_three'].id}"
        "&sort=oldest"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 2
    assert all(
        item["problem_id"] == data["problem_three"].id
        for item in body["items"]
    )


def test_contest_user_isolation(client):
    body = client.get(
        "/contests/submissions/me?limit=100"
    ).json()

    assert body["pagination"]["total"] == 5
    assert all(
        "private-other-user-code" != item["code"]
        for item in body["items"]
    )


def test_contest_specific_history_is_bounded(
    client,
    app_and_db,
):
    _, _, data = app_and_db

    response = client.get(
        f"/contests/{data['contest_one'].id}/my-submissions"
        "?limit=2&offset=1"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 3
    assert len(body["items"]) == 2
    assert body["pagination"]["has_more"] is False


@pytest.mark.parametrize(
    "url",
    [
        "/quiz/submissions/me?limit=0",
        "/quiz/submissions/me?limit=101",
        "/quiz/submissions/me?offset=-1",
        "/quiz/submissions/me?sort=sideways",
        "/contests/submissions/me?limit=0",
        "/contests/submissions/me?limit=101",
        "/contests/submissions/me?offset=-1",
        "/contests/submissions/me?sort=sideways",
    ],
)
def test_invalid_pagination_is_rejected(client, url):
    response = client.get(url)

    assert response.status_code == 422
