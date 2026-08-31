"""Liveness and readiness endpoints for SkillSprint."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from container import Container
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from compiler import list_supported_languages
from database import engine


router = APIRouter()

SERVICE_NAME = "skillsprint-api"


def check_database_readiness() -> dict[str, Any]:
    """Verify database connectivity using a non-mutating lightweight query."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        # Do not expose connection strings, filesystem paths, credentials, or
        # driver exception details through the health endpoint.
        return {"status": "unavailable"}


def check_compiler_readiness() -> dict[str, Any]:
    """Report availability of configured executable compiler/runtime tools.

    Browser-only languages are intentionally excluded because they do not
    depend on a backend CLI runtime. Readiness requires at least one configured
    backend execution language to be available; partial toolchain availability
    is reported as ``degraded`` but remains ready.
    """
    try:
        languages = list_supported_languages()
    except Exception:
        return {
            "status": "unavailable",
            "available_languages": 0,
            "configured_languages": 0,
        }

    executable_languages = [
        language
        for language in languages
        if language.get("type") != "web"
    ]
    available_languages = [
        language
        for language in executable_languages
        if language.get("available") is True
    ]

    available_count = len(available_languages)
    configured_count = len(executable_languages)

    if available_count == 0:
        status = "unavailable"
    elif available_count < configured_count:
        status = "degraded"
    else:
        status = "ok"

    return {
        "status": status,
        "available_languages": available_count,
        "configured_languages": configured_count,
    }


@router.get("/live")
def liveness():
    """Confirm that the FastAPI process is running."""
    return {
        "status": "ok",
        "service": SERVICE_NAME,
    }


@router.get("/ready")
def readiness():
    """Check database connectivity and compiler/runtime availability."""
    database_check = check_database_readiness()
    compiler_check = check_compiler_readiness()

    database_ready = database_check["status"] == "ok"
    compiler_ready = compiler_check["status"] in {"ok", "degraded"}
    ready = database_ready and compiler_ready

    payload = {
        "status": "ready" if ready else "not_ready",
        "checks": {
            "database": database_check,
            "compiler": compiler_check,
        },
    }

    if ready:
        return payload

    return JSONResponse(
        status_code=503,
        content=payload,
    )
