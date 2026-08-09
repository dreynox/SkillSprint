"""Tests for targeted database indexes and startup initialization safety."""

from __future__ import annotations

import os
import sys

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.pool import StaticPool


BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database import (
    Base,
    _acquire_postgresql_index_lock,
    _create_index_if_not_exists_sql,
    _declared_composite_indexes,
    ensure_database_indexes,
)
import models  # noqa: F401


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
        "ix_messages_recipient_sender_created_at": (
            "recipient_id",
            "sender_id",
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


def test_existing_sqlite_database_receives_missing_indexes():
    engine = make_engine()

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

    ensure_database_indexes(bind=engine)

    for table_name, expected in EXPECTED_INDEXES.items():
        actual = index_map(engine, table_name)
        for index_name, columns in expected.items():
            assert actual[index_name] == columns


def test_initializer_is_idempotent_on_sqlite():
    engine = make_engine()
    Base.metadata.create_all(bind=engine)

    ensure_database_indexes(bind=engine)
    first = {
        table: index_map(engine, table)
        for table in EXPECTED_INDEXES
    }

    ensure_database_indexes(bind=engine)
    ensure_database_indexes(bind=engine)

    second = {
        table: index_map(engine, table)
        for table in EXPECTED_INDEXES
    }
    assert second == first


def test_bidirectional_message_query_has_both_index_prefixes():
    engine = make_engine()
    Base.metadata.create_all(bind=engine)

    columns = set(index_map(engine, "messages").values())

    assert (
        "sender_id",
        "recipient_id",
        "created_at",
    ) in columns
    assert (
        "recipient_id",
        "sender_id",
        "created_at",
    ) in columns


def test_postgresql_sql_uses_if_not_exists():
    dialect = postgresql.dialect()
    statements = [
        _create_index_if_not_exists_sql(index, dialect)
        for index in _declared_composite_indexes()
    ]

    assert statements
    assert all(
        "CREATE INDEX IF NOT EXISTS" in statement
        for statement in statements
    )


def test_sqlite_sql_uses_if_not_exists():
    dialect = sqlite.dialect()
    for index in _declared_composite_indexes():
        statement = _create_index_if_not_exists_sql(index, dialect)
        assert "CREATE INDEX IF NOT EXISTS" in statement


def test_postgresql_initialization_acquires_advisory_lock():
    calls = []

    class FakeConnection:
        dialect = postgresql.dialect()

        def exec_driver_sql(self, statement):
            calls.append(statement)

    _acquire_postgresql_index_lock(FakeConnection())

    assert calls == [
        "SELECT pg_advisory_xact_lock("
        "hashtext('skillsprint:index-initialization'))"
    ]


def test_non_postgresql_path_skips_advisory_lock():
    calls = []

    class FakeConnection:
        dialect = sqlite.dialect()

        def exec_driver_sql(self, statement):
            calls.append(statement)

    _acquire_postgresql_index_lock(FakeConnection())
    assert calls == []


def test_index_initialization_errors_are_propagated():
    class BrokenContext:
        def __enter__(self):
            raise RuntimeError("schema unavailable")

        def __exit__(self, exc_type, exc, tb):
            return False

    class BrokenBind:
        def begin(self):
            return BrokenContext()

    with pytest.raises(RuntimeError, match="schema unavailable"):
        ensure_database_indexes(bind=BrokenBind())


def test_contest_participation_unique_constraint_is_not_duplicated():
    engine = make_engine()
    Base.metadata.create_all(bind=engine)

    constraints = inspect(engine).get_unique_constraints(
        "contest_participations"
    )
    unique_columns = {
        tuple(constraint["column_names"])
        for constraint in constraints
    }
    assert ("user_id", "contest_id") in unique_columns

    duplicate = [
        columns
        for columns in index_map(
            engine,
            "contest_participations",
        ).values()
        if columns == ("user_id", "contest_id")
    ]
    assert duplicate == []
