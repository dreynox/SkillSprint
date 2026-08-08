# Database Indexes

Issue #26 adds targeted composite indexes for high-frequency backend query
patterns. The index set is intentionally small: indexes were added only when a
current route or established history lookup benefits from the column prefix.

## Added indexes

### Quiz submissions

```text
ix_quiz_submissions_user_submitted_at
(user_id, submitted_at)
```

Supports per-user quiz statistics/history lookups and keeps timestamp-ordered
history efficient as a user's submission count grows.

```text
ix_quiz_submissions_test_submitted_at
(quiz_id, submitted_at)
```

Supports quiz/test submission history filtered by `test_id` and ordered by
submission time. The physical database column is `quiz_id` even though the
SQLAlchemy attribute is `test_id`.

### Contest submissions

```text
ix_contest_submissions_user_submitted_at
(user_id, submitted_at)
```

Supports per-user contest statistics/history queries.

```text
ix_contest_submissions_contest_submitted_at
(contest_id, submitted_at)
```

Directly supports:

```python
.filter(ContestSubmission.contest_id == contest_id)
.order_by(ContestSubmission.submitted_at.asc())
```

used by the contest-submission listing endpoint.

### Messages

```text
ix_messages_sender_recipient_created_at
(sender_id, recipient_id, created_at)
```

Supports each branch of the two-user conversation query, which filters by
sender and recipient and orders messages chronologically.

### Password reset OTP

```text
ix_password_reset_otps_email_consumed_created_at
(email, consumed, created_at)
```

Matches the password-reset lookup:

```python
.filter(
    PasswordResetOTP.email == email,
    PasswordResetOTP.consumed.is_(False),
)
.order_by(PasswordResetOTP.created_at.desc())
```

`created_at` is indexed instead of `expires_at` because the current route
actually orders by creation time.

## Intentionally not added

### Contest participation duplicate index

`ContestParticipation` already has:

```text
UNIQUE(user_id, contest_id)
```

That unique constraint creates a supporting index and serves the current join
lookup where both columns are equality predicates. Adding another
`(user_id, contest_id)` index would be redundant.

### Contest submission `(problem_id, verdict)`

No current route filters `ContestSubmission` by both `problem_id` and
`verdict`, so this candidate was not added. It should be introduced only when a
real query pattern requires it.

### Message `(recipient_id, is_read, created_at)`

Unread counts are currently computed from the already-loaded conversation
messages rather than queried with `recipient_id + is_read`. Adding this index
now would increase write/storage cost without serving an existing database
query.

## Existing database compatibility

`ensure_database_indexes()` uses SQLAlchemy's:

```python
index.create(checkfirst=True)
```

This makes the migration step:

- idempotent;
- safe for existing data;
- compatible with SQLite;
- compatible with PostgreSQL through SQLAlchemy's dialect layer.

Startup order is:

```text
ensure_sqlite_compatibility()
Base.metadata.create_all()
ensure_database_indexes()
```

New databases receive the indexes through model metadata; existing databases
receive any missing declared composite indexes from the compatibility helper.

## Tests

Run:

```powershell
cd backend
python -m pytest tests/test_database_indexes.py -v
```

The tests inspect exact SQLite index names and column order, simulate an older
database without indexes, rerun the helper multiple times, and verify that
redundant candidate indexes are not introduced.
