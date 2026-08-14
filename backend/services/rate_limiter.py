"""Lightweight, extensible in-memory rate limiting for SkillSprint."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import threading
import time
from typing import Callable, Protocol

from config import SECRET_KEY


class RateLimitStore(Protocol):
    """Storage interface so Redis/shared storage can replace memory later."""

    def get(self, key: str) -> tuple[int, float, int] | None:
        ...

    def set(
        self,
        key: str,
        count: int,
        window_started_at: float,
        window_seconds: int,
    ) -> None:
        ...

    def delete(self, key: str) -> None:
        ...


class InMemoryRateLimitStore:
    """Thread-safe single-process rate-limit state."""

    def __init__(self) -> None:
        self._entries: dict[str, tuple[int, float, int]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> tuple[int, float, int] | None:
        with self._lock:
            return self._entries.get(key)

    def set(
        self,
        key: str,
        count: int,
        window_started_at: float,
        window_seconds: int,
    ) -> None:
        with self._lock:
            self._entries[key] = (
                count,
                window_started_at,
                window_seconds,
            )

    def delete(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def prune_expired(self, now: float) -> int:
        """Remove expired windows and return the number of removed keys."""
        with self._lock:
            expired = [
                key
                for key, (_, started_at, window_seconds) in self._entries.items()
                if max(0.0, now - started_at) >= window_seconds
            ]
            for key in expired:
                self._entries.pop(key, None)
            return len(expired)

    def size(self) -> int:
        with self._lock:
            return len(self._entries)


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after: int


class RateLimiter:
    """Fixed-window limiter with injectable clock and storage backend."""

    def __init__(
        self,
        *,
        store: RateLimitStore | None = None,
        clock: Callable[[], float] = time.time,
        prune_every: int = 100,
    ) -> None:
        if prune_every < 1:
            raise ValueError("prune_every must be at least 1")
        self.store = store or InMemoryRateLimitStore()
        self.clock = clock
        self.prune_every = prune_every
        self._recorded_actions = 0
        self._lock = threading.RLock()

    @staticmethod
    def _validate(limit: int, window_seconds: int) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")

    def _maybe_prune(self, now: float) -> None:
        """Periodically prune stores that expose an optional prune operation."""
        self._recorded_actions += 1
        if self._recorded_actions % self.prune_every:
            return
        prune = getattr(self.store, "prune_expired", None)
        if callable(prune):
            prune(now)

    def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        """Check whether another action is allowed without incrementing it."""
        self._validate(limit, window_seconds)
        now = self.clock()

        with self._lock:
            entry = self.store.get(key)
            if entry is None:
                return RateLimitDecision(
                    allowed=True,
                    remaining=limit,
                    retry_after=0,
                )

            count, started_at, stored_window_seconds = entry
            effective_window = stored_window_seconds or window_seconds
            elapsed = max(0.0, now - started_at)

            if elapsed >= effective_window:
                self.store.delete(key)
                return RateLimitDecision(
                    allowed=True,
                    remaining=limit,
                    retry_after=0,
                )

            if count >= limit:
                return RateLimitDecision(
                    allowed=False,
                    remaining=0,
                    retry_after=max(
                        1,
                        int(effective_window - elapsed + 0.999),
                    ),
                )

            return RateLimitDecision(
                allowed=True,
                remaining=max(0, limit - count),
                retry_after=0,
            )

    def consume(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        """Atomically check and consume one action.

        The first ``limit`` actions are allowed. The next action is blocked.
        This closes the check-then-record race for endpoints where every request
        consumes capacity, such as registration and OTP requests.
        """
        self._validate(limit, window_seconds)
        now = self.clock()

        with self._lock:
            self._maybe_prune(now)
            entry = self.store.get(key)

            if entry is None:
                count = 0
                started_at = now
            else:
                count, started_at, stored_window_seconds = entry
                if max(0.0, now - started_at) >= stored_window_seconds:
                    count = 0
                    started_at = now

            elapsed = max(0.0, now - started_at)
            if count >= limit:
                return RateLimitDecision(
                    allowed=False,
                    remaining=0,
                    retry_after=max(
                        1,
                        int(window_seconds - elapsed + 0.999),
                    ),
                )

            count += 1
            self.store.set(
                key,
                count,
                started_at,
                window_seconds,
            )
            return RateLimitDecision(
                allowed=True,
                remaining=max(0, limit - count),
                retry_after=0,
            )

    def record(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        """Record one failure after an action has already occurred."""
        self._validate(limit, window_seconds)
        now = self.clock()

        with self._lock:
            self._maybe_prune(now)
            entry = self.store.get(key)
            if entry is None:
                count = 1
                started_at = now
            else:
                count, started_at, stored_window_seconds = entry
                if max(0.0, now - started_at) >= stored_window_seconds:
                    count = 1
                    started_at = now
                else:
                    count += 1

            self.store.set(
                key,
                count,
                started_at,
                window_seconds,
            )
            elapsed = max(0.0, now - started_at)
            blocked = count >= limit

            return RateLimitDecision(
                allowed=not blocked,
                remaining=max(0, limit - count),
                retry_after=(
                    max(1, int(window_seconds - elapsed + 0.999))
                    if blocked
                    else 0
                ),
            )

    def reset(self, key: str) -> None:
        self.store.delete(key)


def normalize_identifier(value: str) -> str:
    return value.strip().lower()


def build_rate_limit_key(
    scope: str,
    *,
    requester: str,
    identifier: str | None = None,
) -> str:
    """Build a keyed, non-reversible rate-limit key."""
    normalized_requester = requester.strip() or "unknown"
    normalized_identifier = (
        normalize_identifier(identifier)
        if identifier is not None
        else ""
    )
    payload = (
        f"{normalized_requester}|{normalized_identifier}"
    ).encode("utf-8")
    digest = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return f"{scope}:{digest}"
