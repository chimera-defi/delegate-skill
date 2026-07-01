#!/usr/bin/env python3
"""Thin subprocess shim exposing the small slice of the devin-delegate core
that the moved extras (mcp_server.py, parallel_batch.py) depend on.

The core ``delegate.py`` (~70KB) does not travel into ``delegate-extras/``, so
importing ``run_delegate`` from it would ImportError once these scripts live in
the index repo. Instead we shell out to the installed ``devin-delegate`` wrapper
binary — which injects the envelope, fallback chain, and telemetry exactly as a
normal delegate call would. This keeps the extras self-contained while never
bypassing the wrapper.

``run_delegate`` keeps the core's positional signature so existing call sites
(``parallel_batch`` passes 8 positional args) work unchanged; it returns the
wrapper's exit code (0 = success, 124 = timeout, 126 = wrapper not found).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _resolve_wrapper() -> str | None:
    env = os.environ.get("DEVIN_DELEGATE_BIN")
    if env and Path(env).exists():
        return env
    found = shutil.which("devin-delegate")
    if found:
        return found
    fallback = Path.home() / ".local" / "bin" / "devin-delegate"
    if fallback.exists():
        return str(fallback)
    return None


def run_delegate(
    task: str,
    context_file: Any = None,
    task_class: Any = None,
    dry_run: bool = False,
    print_envelope: bool = False,
    config: Any = None,
    routing: Any = None,
    repo_root: Any = None,
    workspace: Any = None,
    show_cost: bool = False,
    timeout_override: Any = None,
    quick: bool = False,
    interactive: bool = False,
    safety_check: bool = False,
    strict_safety: bool = False,
    use_cache: bool = True,
    cache_ttl: int = 86400,
    fallback_engine_override: Any = None,
    fallback_provider_override: Any = None,
    fallback_model_override: Any = None,
    fallback_pi_provider_override: Any = None,
) -> int:
    """Invoke the devin-delegate wrapper as a subprocess. Returns its exit code.

    In-process-only args (``config``, ``routing``, ``repo_root``, ``show_cost``)
    are ignored: the wrapper reloads its own config and telemetry. All other args
    map onto the wrapper's CLI flags.
    """
    wrapper = _resolve_wrapper()
    if wrapper is None:
        print(
            "delegate_shim: devin-delegate wrapper not found on PATH, in "
            "$DEVIN_DELEGATE_BIN, or at ~/.local/bin/devin-delegate.",
            flush=True,
        )
        return 126

    cmd: list[str] = [wrapper]
    if task:
        cmd += ["--task", str(task)]
    if context_file:
        cmd += ["--context-file", str(context_file)]
    if task_class:
        cmd += ["--task-class", str(task_class)]
    if workspace:
        cmd += ["--workspace", str(workspace)]
    if dry_run:
        cmd.append("--dry-run")
    if print_envelope:
        cmd.append("--print-envelope")
    if quick:
        cmd.append("--quick")
    if interactive:
        cmd.append("--interactive")
    if safety_check:
        cmd.append("--safety-check")
    if strict_safety:
        cmd.append("--strict-safety")
    if not use_cache:
        cmd.append("--no-cache")
    if cache_ttl and cache_ttl != 86400:
        cmd += ["--cache-ttl", str(cache_ttl)]
    if timeout_override:
        cmd += ["--timeout-override", str(timeout_override)]
    if fallback_engine_override:
        cmd += ["--fallback-engine", str(fallback_engine_override)]
    if fallback_provider_override:
        cmd += ["--fallback-provider", str(fallback_provider_override)]
    if fallback_model_override:
        cmd += ["--fallback-model", str(fallback_model_override)]
    if fallback_pi_provider_override:
        cmd += ["--fallback-pi-provider", str(fallback_pi_provider_override)]

    timeout_s = None
    if timeout_override:
        try:
            timeout_s = float(timeout_override)
        except (TypeError, ValueError):
            timeout_s = None

    try:
        proc = subprocess.run(cmd, timeout=timeout_s, check=False)
        return proc.returncode
    except subprocess.TimeoutExpired:
        print(f"delegate_shim: delegate timed out after {timeout_s}s", flush=True)
        return 124
    except FileNotFoundError:
        print(f"delegate_shim: could not execute wrapper: {wrapper}", flush=True)
        return 126


def current_repo_root(default_root: Path | None = None) -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return Path(proc.stdout.strip())
    if default_root is not None:
        return default_root.resolve()
    return Path.cwd()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"missing required config file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
