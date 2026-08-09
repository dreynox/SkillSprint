# Database Indexes

The indexes in this change are tied to current backend query patterns.

## Submission indexes

```text
quiz_submissions:
(user_id, submitted_at)
(quiz_id, submitted_at)

contest_submissions:
(user_id, submitted_at)
(contest_id, submitted_at)
```

These support user/test/contest history lookups ordered by submission time.

## Bidirectional message query

`GET /messages/with/{user_id}` queries both conversation directions:

```text
sender=current AND recipient=peer
OR
sender=peer AND recipient=current
```

One index cannot efficiently lead with both sender and recipient, so both are
declared:

```text
(sender_id, recipient_id, created_at)
(recipient_id, sender_id, created_at)
```

This directly addresses both branches of the existing OR query.

## Password-reset OTP

```text
(email, consumed, created_at)
```

This matches the active-code lookup and newest-first ordering.

## PostgreSQL startup concurrency

The earlier `Index.create(checkfirst=True)` approach performed an existence
check before creation and could race when multiple workers started together.

The PostgreSQL path now uses a transaction-scoped advisory lock:

```sql
SELECT pg_advisory_xact_lock(
  hashtext('skillsprint:index-initialization')
);
```

and creates indexes with:

```sql
CREATE INDEX IF NOT EXISTS ...
```

The advisory lock serializes competing SkillSprint startup workers and is
released automatically when the transaction commits or rolls back.

SQLite also uses `CREATE INDEX IF NOT EXISTS`, keeping repeated initialization
idempotent.

## Failure behavior

Index setup failures are no longer treated as successful startup.
`initialize_database()` prints the original traceback and then raises:

```text
RuntimeError: SkillSprint database schema initialization failed
```

so a partially initialized schema does not silently continue serving traffic.

## PostgreSQL-path testing

The focused tests verify PostgreSQL SQL generation and that the PostgreSQL path
requests the transaction advisory lock. A live PostgreSQL server is not
required for those unit tests.

## Intentionally omitted duplicate index

`ContestParticipation` already has `UNIQUE(user_id, contest_id)`, so an
additional identical composite index remains unnecessary.
