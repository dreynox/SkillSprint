"""Lightweight, extensible in-memory rate limiting for SkillSprint."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import threading
import time
from typing import Callable, Protocol


class RateLimitStore(Protocol):
    """Storage interface so Redis/shared storage can replace memory later."""

    def get(self, key: str) -> tuple[int, float] | None:
        ...

    def set(self, key: str, count: int, window_started_at: float) -> None:
        ...

    def delete(self, key: str) -> None:
        ...


class InMemoryRateLimitStore:
    """Thread-safe single-process rate-limit state."""

    def __init__(self) -> None:
        self._entries: dict[str, tuple[int, float]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> tuple[int, float] | None:
        with self._lock:
            return self._entries.get(key)

    def set(self, key: str, count: int, window_started_at: float) -> None:
        with self._lock:
            self._entries[key] = (count, window_started_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after: int


class RateLimiter:
    """Fixed-window limiter with an injectable clock and storage backend."""

    def __init__(
        self,
        *,
        store: RateLimitStore | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.store = store or InMemoryRateLimitStore()
        self.clock = clock
        self._lock = threading.RLock()

    @staticmethod
    def _validate(limit: int, window_seconds: int) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")

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

            count, started_at = entry
            elapsed = max(0.0, now - started_at)

            if elapsed >= window_seconds:
                self.store.delete(key)
                return RateLimitDecision(
                    allowed=True,
                    remaining=limit,
                    retry_after=0,
                )

            if count >= limit:
                retry_after = max(
                    1,
                    int(window_seconds - elapsed + 0.999),
                )
                return RateLimitDecision(
                    allowed=False,
                    remaining=0,
                    retry_after=retry_after,
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
        """Record one relevant action and return the resulting state."""
        self._validate(limit, window_seconds)
        now = self.clock()

        with self._lock:
            entry = self.store.get(key)
            if entry is None:
                count = 1
                started_at = now
            else:
                count, started_at = entry
                if max(0.0, now - started_at) >= window_seconds:
                    count = 1
                    started_at = now
                else:
                    count += 1

            self.store.set(key, count, started_at)
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
    """Build a non-reversible key so raw emails are not stored in memory."""
    normalized_requester = requester.strip() or "unknown"
    normalized_identifier = (
        normalize_identifier(identifier)
        if identifier is not None
        else ""
    )
    digest = hashlib.sha256(
        f"{normalized_requester}|{normalized_identifier}".encode("utf-8")
    ).hexdigest()
    return f"{scope}:{digest}"
