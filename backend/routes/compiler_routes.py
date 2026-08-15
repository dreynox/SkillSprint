from dependency_injector.wiring import Provide, inject
from container import Container
from typing import List

from fastapi import APIRouter

from compiler import (
    CompilationError,
    ExecutionError,
    ExecutionTimeoutError,
    ToolUnavailableError,
    debug_c_cpp_with_gdb,
    execute_language_code,
    list_supported_languages,
    normalize_language,
)
from schemas import (
    CompilerDebugRequest,
    CompilerDebugResponse,
    CompilerLanguageOut,
    CompilerRunRequest,
    CompilerRunResponse,
)

router = APIRouter()


@router.get("/languages", response_model=List[CompilerLanguageOut])
@inject
def get_supported_languages():
    return [CompilerLanguageOut(**item) for item in list_supported_languages()]


@router.post("/run", response_model=CompilerRunResponse)
@inject
def run_code(payload: CompilerRunRequest):
    try:
        result = execute_language_code(
            language=payload.language,
            code=payload.code,
            stdin=payload.stdin,
            timeout=payload.timeout,
        )
        return CompilerRunResponse(**result)
    except CompilationError as exc:
        return CompilerRunResponse(
            status="COMPILATION_ERROR",
            language=normalize_language(payload.language),
            stdout="",
            stderr=str(exc),
            exit_code=1,
            execution_time_ms=0,
            message="Compilation failed",
        )
    except ExecutionTimeoutError as exc:
        return CompilerRunResponse(
            status="TIMEOUT",
            language=normalize_language(payload.language),
            stdout="",
            stderr=str(exc),
            exit_code=124,
            execution_time_ms=payload.timeout * 1000,
            message="Execution timed out",
        )
    except ToolUnavailableError as exc:
        return CompilerRunResponse(
            status="TOOL_UNAVAILABLE",
            language=normalize_language(payload.language),
            stdout="",
            stderr=str(exc),
            exit_code=127,
            execution_time_ms=0,
            message="Required runtime/compiler tool is missing",
        )
    except ExecutionError as exc:
        return CompilerRunResponse(
            status="RUNTIME_ERROR",
            language=normalize_language(payload.language),
            stdout="",
            stderr=str(exc),
            exit_code=1,
            execution_time_ms=0,
            message="Execution failed",
        )


@router.post("/debug", response_model=CompilerDebugResponse)
@inject
def debug_code(payload: CompilerDebugRequest):
    result = debug_c_cpp_with_gdb(
        language=payload.language,
        code=payload.code,
        stdin=payload.stdin,
        breakpoints=payload.breakpoints,
    )
    return CompilerDebugResponse(**result)
