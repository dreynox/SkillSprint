"""Reusable pagination helpers for SkillSprint APIs."""

from __future__ import annotations

from typing import Literal

from fastapi import Query


SortOrder = Literal["newest", "oldest"]


class PaginationParams:
    """Validated limit/offset/sort query parameters."""

    def __init__(
        self,
        limit: int = Query(
            20,
            ge=1,
            le=100,
            description="Maximum number of records to return (1-100).",
            examples=[20],
        ),
        offset: int = Query(
            0,
            ge=0,
            description="Number of matching records to skip.",
            examples=[0],
        ),
        sort: Literal["newest", "oldest"] = Query(
            "newest",
            description="Sort submission history by submission time.",
            examples=["newest"],
        ),
    ):
        self.limit = limit
        self.offset = offset
        self.sort = sort
