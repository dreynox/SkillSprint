#!/usr/bin/env python3
"""
Copy data from the local SQLite database into a PostgreSQL database.

Usage from the backend directory:
    $env:DATABASE_URL="postgresql://..."  # PowerShell
    set DATABASE_URL=postgresql://...      # Windows cmd
    python migrate_sqlite_to_postgres.py

When running from your own computer, use Render's External Database URL.
The Internal Database URL only works from services running inside Render.

Optional:
    set SOURCE_DATABASE_URL=sqlite:///C:/path/to/skillsprint.db
    python migrate_sqlite_to_postgres.py --clear-target

The script creates tables in the target database if needed, copies rows in
foreign-key-safe order, and can clear the target first when requested.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, text

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv()

import models  # noqa: F401  # Populate Base.metadata before create_all.
from database import Base


def normalize_postgres_url(url: str) -> str:
    normalized_url = url.replace("postgres://", "postgresql://", 1)
    return normalized_url.replace("postgresql://", "postgresql+psycopg://", 1)


def resolve_source_url() -> str:
    source_url = os.getenv("SOURCE_DATABASE_URL")
    if source_url:
        return source_url

    sqlite_path = (BASE_DIR / "skillsprint.db").as_posix()
    return f"sqlite:///{sqlite_path}"


def resolve_target_url() -> str:
    target_url = os.getenv("DATABASE_URL")
    if not target_url:
        raise SystemExit("DATABASE_URL is required and should point to the PostgreSQL database.")
    return normalize_postgres_url(target_url)


def clear_target_tables(connection, tables) -> None:
    for table in reversed(tables):
        connection.execute(table.delete())


def sync_sequences(connection, tables) -> None:
    for table in tables:
        primary_key_columns = list(table.primary_key.columns)
        if len(primary_key_columns) != 1:
            continue

        primary_key = primary_key_columns[0]
        if str(primary_key.type).lower() not in {"integer", "bigint"}:
            continue

        sequence_name = connection.execute(
            text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
            {"table_name": table.name, "column_name": primary_key.name},
        ).scalar_one_or_none()

        if not sequence_name:
            continue

        max_value = connection.execute(text(f'SELECT COALESCE(MAX({primary_key.name}), 0) FROM "{table.name}"')).scalar_one()
        next_value = max_value if max_value > 0 else 1
        is_called = max_value > 0
        connection.execute(
            text("SELECT setval(:sequence_name, :next_value, :is_called)"),
            {"sequence_name": sequence_name, "next_value": next_value, "is_called": is_called},
        )


def migrate(clear_target: bool = False) -> None:
    source_url = resolve_source_url()
    target_url = resolve_target_url()

    source_engine = create_engine(
        source_url,
        connect_args={"check_same_thread": False} if source_url.startswith("sqlite") else {},
        pool_pre_ping=not source_url.startswith("sqlite"),
    )
    target_engine = create_engine(
        target_url,
        pool_pre_ping=True,
    )

    Base.metadata.create_all(bind=target_engine)

    source_metadata = MetaData()
    source_metadata.reflect(bind=source_engine)

    target_tables = [table for table in Base.metadata.sorted_tables if table.name in source_metadata.tables]

    with source_engine.connect() as source_connection, target_engine.begin() as target_connection:
        if clear_target:
            clear_target_tables(target_connection, target_tables)

        for table in target_tables:
            source_table = source_metadata.tables[table.name]
            rows = source_connection.execute(source_table.select()).mappings().all()
            if not rows:
                continue

            target_connection.execute(table.insert(), [dict(row) for row in rows])

        if target_engine.dialect.name == "postgresql":
            sync_sequences(target_connection, target_tables)

    print("Migration completed successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate the local SQLite database into PostgreSQL.")
    parser.add_argument(
        "--clear-target",
        action="store_true",
        help="Delete existing rows from the target database before copying data.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    migrate(clear_target=args.clear_target)