"""Multi-language code execution and lightweight debugging utilities."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import config
import sandbox

# Default wall-clock time limit for a single run (overridden by config env var).
TIME_LIMIT = config.COMPILER_TIMEOUT_SECONDS
OUTPUT_SIZE_LIMIT = 10000  # chars


class CompilationError(Exception):
    pass


class ExecutionError(Exception):
    pass


class ExecutionTimeoutError(Exception):
    pass


class ToolUnavailableError(Exception):
    pass


@dataclass(frozen=True)
class LanguageSpec:
    key: str
    display_name: str
    source_filename: str
    run_command: list[str]
    compile_command: list[str] | None = None
    needs_output_binary: bool = False


EXECUTABLE_NAME = "main_exec.exe" if os.name == "nt" else "main_exec"

LANGUAGE_SPECS: dict[str, LanguageSpec] = {
    "c": LanguageSpec(
        key="c",
        display_name="C (C99)",
        source_filename="main.c",
        compile_command=["gcc", "-O2", "-std=c99", "-Wall", "main.c", "-o", EXECUTABLE_NAME],
        run_command=[f"./{EXECUTABLE_NAME}"],
        needs_output_binary=True,
    ),
    "cpp": LanguageSpec(
        key="cpp",
        display_name="C++ (g++)",
        source_filename="main.cpp",
        compile_command=["g++", "-O2", "-std=c++17", "main.cpp", "-o", EXECUTABLE_NAME],
        run_command=[f"./{EXECUTABLE_NAME}"],
        needs_output_binary=True,
    ),
    "python": LanguageSpec(
        key="python",
        display_name="Python",
        source_filename="main.py",
        run_command=["python", "main.py"],
    ),
    "javascript": LanguageSpec(
        key="javascript",
        display_name="JavaScript (Node.js)",
        source_filename="main.js",
        run_command=["node", "main.js"],
    ),
    "java": LanguageSpec(
        key="java",
        display_name="Java",
        source_filename="Main.java",
        compile_command=["javac", "Main.java"],
        run_command=["java", "-cp", ".", "Main"],
    ),
    "php": LanguageSpec(
        key="php",
        display_name="PHP",
        source_filename="main.php",
        run_command=["php", "main.php"],
    ),
    "go": LanguageSpec(
        key="go",
        display_name="Go",
        source_filename="main.go",
        compile_command=["go", "build", "-o", EXECUTABLE_NAME, "main.go"],
        run_command=[f"./{EXECUTABLE_NAME}"],
        needs_output_binary=True,
    ),
    "rust": LanguageSpec(
        key="rust",
        display_name="Rust",
        source_filename="main.rs",
        compile_command=["rustc", "main.rs", "-O", "-o", EXECUTABLE_NAME],
        run_command=[f"./{EXECUTABLE_NAME}"],
        needs_output_binary=True,
    ),
    "r": LanguageSpec(
        key="r",
        display_name="R",
        source_filename="main.R",
        run_command=["Rscript", "main.R"],
    ),
}

LANGUAGE_ALIASES = {
    "c99": "c",
    "c++": "cpp",
    "cpp17": "cpp",
    "js": "javascript",
    "node": "javascript",
    "py": "python",
    "golang": "go",
    "rs": "rust",
}

WEB_ONLY_LANGUAGES = {
    "html": "HTML runs in a browser, not as a CLI process.",
    "css": "CSS is stylesheet syntax and has no standalone runtime.",
    "react": "React requires a Node build toolchain (Vite/webpack/esbuild) for rendering.",
    "typescript": "TypeScript requires transpilation (tsc/esbuild) before execution.",
}


def normalize_language(language: str) -> str:
    value = (language or "").strip().lower()
    return LANGUAGE_ALIASES.get(value, value)


def _tool_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _ensure_dependencies(spec: LanguageSpec):
    checks: list[str] = []

    # For compiled languages the runtime executable is generated in a temp
    # workspace, so only the compiler binary should be pre-checked.
    if spec.compile_command:
        checks.append(spec.compile_command[0])
    else:
        checks.append(spec.run_command[0])

    missing = sorted({cmd for cmd in checks if not _tool_exists(cmd)})
    if missing:
        raise ToolUnavailableError(f"Missing runtime/compiler tools: {', '.join(missing)}")


def _run_subprocess(
    command: list[str],
    cwd: Path,
    stdin_data: str,
    timeout: int,
    submission_id: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Route execution through the hardened sandbox layer."""
    # Enforce the server-side hard cap so callers cannot exceed policy.
    capped_timeout = min(timeout, config.COMPILER_TIMEOUT_SECONDS)
    try:
        return sandbox.run_sandboxed(
            command=command,
            cwd=cwd,
            stdin_data=stdin_data,
            timeout=capped_timeout,
            submission_id=submission_id,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExecutionTimeoutError(
            f"Execution exceeded {capped_timeout}s timeout"
        ) from exc


def list_supported_languages() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for spec in LANGUAGE_SPECS.values():
        runtime_ok = True if spec.compile_command else _tool_exists(spec.run_command[0])
        compile_ok = True if not spec.compile_command else _tool_exists(spec.compile_command[0])
        available = runtime_ok and compile_ok

        missing: list[str] = []
        if spec.compile_command:
            compiler_cmd = spec.compile_command[0]
            if not _tool_exists(compiler_cmd):
                missing.append(compiler_cmd)
        else:
            runtime_cmd = spec.run_command[0]
            if not _tool_exists(runtime_cmd):
                missing.append(runtime_cmd)

        result.append(
            {
                "key": spec.key,
                "name": spec.display_name,
                "type": "compiled" if spec.compile_command else "interpreted",
                "available": available,
                "missing": missing,
                "debugger": spec.key in {"c", "cpp"} and _tool_exists("gdb"),
            }
        )

    for key, message in WEB_ONLY_LANGUAGES.items():
        result.append(
            {
                "key": key,
                "name": key.upper() if key in {"html", "css"} else key.title(),
                "type": "web",
                "available": True,
                "missing": [],
                "debugger": False,
                "note": message,
            }
        )

    return sorted(result, key=lambda item: item["key"])


def execute_language_code(language: str, code: str, stdin: str = "", timeout: int = TIME_LIMIT) -> dict[str, Any]:
    lang = normalize_language(language)

    if lang in WEB_ONLY_LANGUAGES:
        return {
            "status": "WEB_PREVIEW_ONLY",
            "language": lang,
            "stdout": "",
            "stderr": WEB_ONLY_LANGUAGES[lang],
            "exit_code": 0,
            "execution_time_ms": 0,
            "message": WEB_ONLY_LANGUAGES[lang],
            "sandbox_used": False,
            "submission_id": None,
        }

    spec = LANGUAGE_SPECS.get(lang)
    if not spec:
        return {
            "status": "UNSUPPORTED_LANGUAGE",
            "language": lang,
            "stdout": "",
            "stderr": "Language is not configured in this deployment.",
            "exit_code": 1,
            "execution_time_ms": 0,
            "message": "Language is not configured in this deployment.",
            "sandbox_used": False,
            "submission_id": None,
        }

    _ensure_dependencies(spec)

    # Generate a unique ID for audit log correlation.
    sid = str(uuid.uuid4())
    sandbox_used = config.COMPILER_SANDBOX_ENABLED

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        source_file = workspace / spec.source_filename
        source_file.write_text(code, encoding="utf-8")

        if spec.compile_command:
            compile_result = _run_subprocess(
                spec.compile_command, workspace, "", timeout, submission_id=sid
            )
            if compile_result.returncode != 0:
                stderr = (compile_result.stderr or compile_result.stdout or "Compilation failed")[:OUTPUT_SIZE_LIMIT]
                raise CompilationError(stderr)

            if spec.needs_output_binary and not (workspace / EXECUTABLE_NAME).exists():
                # In Docker-sandbox mode the container writes the binary back to
                # the bind-mounted workspace (= this host-side tmpdir), so this
                # check works correctly in both sandbox and direct modes.
                raise CompilationError("Compilation succeeded but executable not found")


        start = time.perf_counter()
        run_result = _run_subprocess(
            spec.run_command, workspace, stdin, timeout, submission_id=sid
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        stdout = (run_result.stdout or "")[:OUTPUT_SIZE_LIMIT]
        stderr = (run_result.stderr or "")[:OUTPUT_SIZE_LIMIT]

        status = "SUCCESS" if run_result.returncode == 0 else "RUNTIME_ERROR"
        message = "Executed successfully" if status == "SUCCESS" else "Program exited with non-zero status"

        return {
            "status": status,
            "language": lang,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": run_result.returncode,
            "execution_time_ms": elapsed_ms,
            "message": message,
            "sandbox_used": sandbox_used,
            "submission_id": sid,
        }


def test_code(code: str, test_cases: list[dict[str, str]], language: str = "c") -> dict[str, Any]:
    """Run code against text I/O test cases with a common response shape."""
    passed = 0
    results: list[dict[str, Any]] = []

    for idx, test_case in enumerate(test_cases, start=1):
        test_input = test_case.get("input", "")
        expected = str(test_case.get("expected_output", "")).strip()

        try:
            execution = execute_language_code(language=language, code=code, stdin=test_input)
            if execution["status"] in {"UNSUPPORTED_LANGUAGE", "WEB_PREVIEW_ONLY"}:
                return {
                    "status": execution["status"],
                    "message": execution.get("message"),
                    "passed": 0,
                    "total": len(test_cases),
                    "results": [],
                }

            if execution["status"] != "SUCCESS":
                results.append(
                    {
                        "test_case": idx,
                        "status": "RUNTIME_ERROR",
                        "input": test_input[:200],
                        "expected": expected[:200],
                        "actual": execution.get("stdout", "")[:200],
                        "error": execution.get("stderr", "")[:200],
                    }
                )
                continue

            actual = str(execution.get("stdout", "")).strip()
            if actual == expected:
                passed += 1
                result_status = "PASS"
            else:
                result_status = "FAIL"

            results.append(
                {
                    "test_case": idx,
                    "status": result_status,
                    "input": test_input[:200],
                    "expected": expected[:200],
                    "actual": actual[:200],
                }
            )
        except CompilationError as exc:
            return {
                "status": "COMPILATION_ERROR",
                "message": str(exc),
                "passed": 0,
                "total": len(test_cases),
                "results": [],
            }
        except ExecutionTimeoutError as exc:
            results.append(
                {
                    "test_case": idx,
                    "status": "TIMEOUT",
                    "input": test_input[:200],
                    "expected": expected[:200],
                    "error": str(exc),
                }
            )
        except ToolUnavailableError as exc:
            return {
                "status": "TOOL_UNAVAILABLE",
                "message": str(exc),
                "passed": 0,
                "total": len(test_cases),
                "results": [],
            }
        except Exception as exc:
            results.append(
                {
                    "test_case": idx,
                    "status": "RUNTIME_ERROR",
                    "input": test_input[:200],
                    "expected": expected[:200],
                    "error": str(exc)[:200],
                }
            )

    return {
        "status": "ACCEPTED" if passed == len(test_cases) and len(test_cases) > 0 else "PARTIAL",
        "passed": passed,
        "total": len(test_cases),
        "results": results,
    }


def debug_c_cpp_with_gdb(language: str, code: str, stdin: str = "", breakpoints: list[int] | None = None) -> dict[str, Any]:
    """Run gdb in batch mode and return debugger text output for C/C++."""
    lang = normalize_language(language)
    if lang not in {"c", "cpp"}:
        return {
            "status": "UNSUPPORTED_LANGUAGE",
            "message": "GDB debug is supported for C/C++ only in this mode.",
            "stdout": "",
            "stderr": "",
        }

    if not _tool_exists("gdb"):
        return {
            "status": "TOOL_UNAVAILABLE",
            "message": "gdb is not available on this deployment.",
            "stdout": "",
            "stderr": "",
        }

    spec = LANGUAGE_SPECS[lang]
    _ensure_dependencies(spec)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        src = workspace / spec.source_filename
        src.write_text(code, encoding="utf-8")

        compile_cmd = [
            *(spec.compile_command or []),
        ]
        if compile_cmd:
            # Rebuild with debug symbols.
            compile_cmd = [arg for arg in compile_cmd if arg not in {"-O2"}] + ["-g"]
            compile_res = _run_subprocess(compile_cmd, workspace, "", 10)
            if compile_res.returncode != 0:
                return {
                    "status": "COMPILATION_ERROR",
                    "message": "Compilation failed for debug session",
                    "stdout": compile_res.stdout[:OUTPUT_SIZE_LIMIT],
                    "stderr": compile_res.stderr[:OUTPUT_SIZE_LIMIT],
                }

        gdb_commands = ["set pagination off"]
        for line_no in (breakpoints or [])[:8]:
            if isinstance(line_no, int) and line_no > 0:
                gdb_commands.append(f"break {line_no}")

        if stdin:
            input_file = workspace / "stdin.txt"
            input_file.write_text(stdin, encoding="utf-8")
            gdb_commands.append(f"run < {input_file.name}")
        else:
            gdb_commands.append("run")

        gdb_commands.extend(["bt", "info locals", "quit"])

        cmd = ["gdb", "--batch", f"./{EXECUTABLE_NAME}"]
        for item in gdb_commands:
            cmd.extend(["-ex", item])

        result = _run_subprocess(cmd, workspace, "", 15)
        return {
            "status": "DEBUG_COMPLETE" if result.returncode == 0 else "DEBUG_ERROR",
            "message": "GDB debug session finished",
            "stdout": (result.stdout or "")[:OUTPUT_SIZE_LIMIT],
            "stderr": (result.stderr or "")[:OUTPUT_SIZE_LIMIT],
        }
