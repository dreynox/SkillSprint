"""Tests for targeted database indexes added by issue #26."""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool


BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database import Base, ensure_database_indexes
import models  # noqa: F401 - registers all SQLAlchemy tables


EXPECTED_INDEXES = {
    "quiz_submissions": {
        "ix_quiz_submissions_user_submitted_at": (
            "user_id",
            "submitted_at",
        ),
        "ix_quiz_submissions_test_submitted_at": (
            "quiz_id",
            "submitted_at",
        ),
    },
    "contest_submissions": {
        "ix_contest_submissions_user_submitted_at": (
            "user_id",
            "submitted_at",
        ),
        "ix_contest_submissions_contest_submitted_at": (
            "contest_id",
            "submitted_at",
        ),
    },
    "messages": {
        "ix_messages_sender_recipient_created_at": (
            "sender_id",
            "recipient_id",
            "created_at",
        ),
    },
    "password_reset_otps": {
        "ix_password_reset_otps_email_consumed_created_at": (
            "email",
            "consumed",
            "created_at",
        ),
    },
}


def make_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def index_map(engine, table_name):
    return {
        index["name"]: tuple(index["column_names"])
        for index in inspect(engine).get_indexes(table_name)
    }


def test_declared_indexes_have_expected_names_and_columns():
    engine = make_engine()
    Base.metadata.create_all(bind=engine)

    for table_name, expected in EXPECTED_INDEXES.items():
        actual = index_map(engine, table_name)
        for index_name, columns in expected.items():
            assert actual[index_name] == columns


def test_compatibility_helper_adds_indexes_to_existing_sqlite_tables():
    engine = make_engine()

    # Simulate an older database: create the tables manually without the new
    # composite indexes, then run the compatibility helper.
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE quiz_submissions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                quiz_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                submitted_at DATETIME NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            CREATE TABLE contest_submissions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                contest_id INTEGER NOT NULL,
                problem_id INTEGER NOT NULL,
                language VARCHAR NOT NULL,
                code TEXT NOT NULL,
                verdict VARCHAR NOT NULL,
                score INTEGER NOT NULL,
                execution_results TEXT,
                submitted_at DATETIME NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                content TEXT,
                media_type VARCHAR,
                file_path VARCHAR,
                expires_at DATETIME,
                is_read BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            CREATE TABLE password_reset_otps (
                id INTEGER PRIMARY KEY,
                email VARCHAR NOT NULL,
                otp_hash VARCHAR NOT NULL,
                expires_at DATETIME NOT NULL,
                attempts INTEGER NOT NULL,
                consumed BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )

    for table_name, expected in EXPECTED_INDEXES.items():
        before = index_map(engine, table_name)
        for index_name in expected:
            assert index_name not in before

    ensure_database_indexes(bind=engine)

    for table_name, expected in EXPECTED_INDEXES.items():
        after = index_map(engine, table_name)
        for index_name, columns in expected.items():
            assert after[index_name] == columns


def test_compatibility_helper_is_idempotent():
    engine = make_engine()
    Base.metadata.create_all(bind=engine)

    ensure_database_indexes(bind=engine)
    first_snapshot = {
        table: index_map(engine, table)
        for table in EXPECTED_INDEXES
    }

    # Running it repeatedly must neither fail nor duplicate indexes.
    ensure_database_indexes(bind=engine)
    ensure_database_indexes(bind=engine)

    second_snapshot = {
        table: index_map(engine, table)
        for table in EXPECTED_INDEXES
    }

    assert second_snapshot == first_snapshot

    for table_name, expected in EXPECTED_INDEXES.items():
        actual_names = [
            name
            for name in second_snapshot[table_name]
            if name in expected
        ]
        assert len(actual_names) == len(expected)


def test_contest_participation_unique_constraint_is_not_duplicated():
    engine = make_engine()
    Base.metadata.create_all(bind=engine)

    # The existing UNIQUE(user_id, contest_id) constraint already supports the
    # equality lookup used by the join endpoint. We intentionally do not add a
    # redundant composite index for the same columns.
    constraints = inspect(engine).get_unique_constraints(
        "contest_participations"
    )
    unique_columns = {
        tuple(constraint["column_names"])
        for constraint in constraints
    }
    assert ("user_id", "contest_id") in unique_columns

    indexes = index_map(engine, "contest_participations")
    duplicate = [
        columns
        for columns in indexes.values()
        if columns == ("user_id", "contest_id")
    ]
    assert duplicate == []


def test_no_problem_verdict_index_without_matching_route_query():
    engine = make_engine()
    Base.metadata.create_all(bind=engine)

    indexes = index_map(engine, "contest_submissions")

    assert not any(
        columns == ("problem_id", "verdict")
        for columns in indexes.values()
    )
