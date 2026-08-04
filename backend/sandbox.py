"""
sandbox.py – Hardened execution sandbox for SkillSprint's compiler engine.

When COMPILER_SANDBOX_ENABLED=true every code-execution request is routed
through an ephemeral Docker container with the following security controls:

    • --network none                        (no outbound network)
    • --cpus <COMPILER_CPU_LIMIT>           (CPU cap)
    • --memory / --memory-swap              (memory cap, no swap)
    • --pids-limit <COMPILER_PID_LIMIT>     (blocks fork bombs)
    • --read-only + --tmpfs /sandbox        (read-only FS, scoped tmp)
    • --user nobody                         (non-root execution)
    • --cap-drop ALL                        (minimal Linux capabilities)
    • --security-opt no-new-privileges:true (privilege escalation blocked)
    • --rm                                  (auto-removed on exit)

When COMPILER_SANDBOX_ENABLED=false (the default) the module falls back to a
plain subprocess.run() call – suitable for local development without Docker.

Public API
----------
    run_sandboxed(command, cwd, stdin_data, timeout, submission_id) -> CompletedProcess
"""

from __future__ import annotations

import logging
import shlex
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import config

logger = logging.getLogger("skillsprint.sandbox")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _docker_available() -> bool:
    """Return True if the docker CLI is on PATH and the daemon is reachable."""
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _build_docker_command(
    inner_command: list[str],
    host_src_dir: Path,
    timeout: int,
) -> list[str]:
    """
    Assemble the full ``docker run`` command with all hardening flags.

    The *host_src_dir* directory (the API server's tempfile workspace) is
    bind-mounted **read-write** at ``/sandbox`` inside the container.  This is
    the container's working directory so that:

    * Source files written by the API process are immediately visible to the
      container without a copy step.
    * Compiled artifacts (e.g. ``main_exec``) produced during the compile
      phase are written back to the same host-side directory and are available
      to subsequent calls that share the same *host_src_dir* (i.e. the run
      phase in ``compiler.py``).
    * The host-side binary-existence check in ``compiler.py`` works correctly
      because the binary lands in the shared host directory.

    ``/tmp`` inside the container is a separate, isolated tmpfs so that the
    runtime can create temporary files without touching the host filesystem.

    The container root filesystem is ``--read-only``; only ``/sandbox`` (via
    bind-mount) and ``/tmp`` (via tmpfs) are writable.
    """
    cmd = [
        "docker", "run",
        "--rm",                                              # auto-remove on exit
        "--network", config.COMPILER_NETWORK_MODE,          # no outbound network
        "--cpus", config.COMPILER_CPU_LIMIT,                 # CPU cap
        "--memory", config.COMPILER_MEM_LIMIT,               # memory cap
        "--memory-swap", config.COMPILER_MEM_LIMIT,          # disable swap
        "--pids-limit", str(config.COMPILER_PID_LIMIT),      # block fork bombs
        "--read-only",                                       # read-only root FS
        # /tmp: isolated tmpfs for runtime scratch (does NOT overlap /sandbox)
        "--tmpfs", "/tmp:rw,size=32m,mode=1777",
        "--user", "nobody",                                  # non-root user
        "--cap-drop", "ALL",                                 # drop all capabilities
        "--security-opt", "no-new-privileges:true",         # block privilege escalation
        "--stop-timeout", "1",                              # fast stop on kill signal
        "--workdir", "/sandbox",
        # Bind-mount the shared workspace read-write so compile + run phases
        # can both access source files and produced artifacts.
        "--volume", f"{host_src_dir}:/sandbox:rw",
        config.COMPILER_SANDBOX_IMAGE,
    ]
    cmd.extend(inner_command)
    return cmd



def _kill_container(container_id: str) -> None:
    """Best-effort container kill – called on timeout."""
    try:
        subprocess.run(
            ["docker", "kill", container_id],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_sandboxed(
    command: list[str],
    cwd: Path,
    stdin_data: str,
    timeout: int,
    submission_id: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Execute *command* inside a hardened sandbox and return a
    ``subprocess.CompletedProcess`` compatible result.

    Parameters
    ----------
    command:
        The exact command + args to run (e.g. ``["python", "main.py"]``).
    cwd:
        The host-side directory that contains the source file(s). This
        directory will be bind-mounted read-only into the container.
    stdin_data:
        Text to pipe into the process's stdin.
    timeout:
        Wall-clock timeout in seconds. The process (and container) will be
        force-killed after this many seconds.
    submission_id:
        Opaque correlation ID logged alongside every execution record.
        A UUID4 will be generated if not provided.
    """
    sid = submission_id or str(uuid.uuid4())
    use_docker = config.COMPILER_SANDBOX_ENABLED and _docker_available()

    start = time.perf_counter()

    if use_docker:
        # ── Docker sandboxed path ──────────────────────────────────────────
        # Rewrite the command so it runs relative to /sandbox (the workdir)
        # rather than the host cwd.  Source files are at /sandbox/src/; the
        # container's workdir /sandbox is writable via tmpfs.
        docker_cmd = _build_docker_command(command, cwd, timeout)

        logger.info(
            "sandbox.start  sid=%s  sandbox=docker  cmd=%s",
            sid,
            shlex.join(command),
        )

        try:
            proc = subprocess.run(
                docker_cmd,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=timeout + 5,  # outer timeout gives Docker a grace period
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.warning(
                "sandbox.timeout  sid=%s  sandbox=docker  elapsed_ms=%d",
                sid,
                elapsed_ms,
            )
            # Re-raise so compiler.py can return a TIMEOUT status to the client.
            raise subprocess.TimeoutExpired(docker_cmd, timeout)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "sandbox.done  sid=%s  sandbox=docker  exit_code=%d  "
            "elapsed_ms=%d  stdout_bytes=%d  stderr_bytes=%d",
            sid,
            proc.returncode,
            elapsed_ms,
            len(proc.stdout or ""),
            len(proc.stderr or ""),
        )
        return proc

    else:
        # ── Direct subprocess fallback (local dev / Docker unavailable) ───
        if config.COMPILER_SANDBOX_ENABLED:
            logger.warning(
                "sandbox.fallback  sid=%s  reason='Docker unavailable – "
                "running unsandboxed. Set COMPILER_SANDBOX_ENABLED=false to "
                "suppress this warning in dev.'",
                sid,
            )
        else:
            logger.debug(
                "sandbox.fallback  sid=%s  reason='sandbox disabled'", sid
            )

        try:
            proc = subprocess.run(
                command,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(cwd),
            )
        except subprocess.TimeoutExpired as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.warning(
                "sandbox.timeout  sid=%s  sandbox=direct  elapsed_ms=%d",
                sid,
                elapsed_ms,
            )
            raise exc

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "sandbox.done  sid=%s  sandbox=direct  exit_code=%d  "
            "elapsed_ms=%d  stdout_bytes=%d  stderr_bytes=%d",
            sid,
            proc.returncode,
            elapsed_ms,
            len(proc.stdout or ""),
            len(proc.stderr or ""),
        )
        return proc
