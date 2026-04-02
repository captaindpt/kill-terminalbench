"""Shared OpenRouter client helpers."""

from __future__ import annotations

import os
from pathlib import Path

import anthropic
import httpx


SYSTEM_PROMPT = """You are solving a task in a Linux environment. A separate automated verifier will test your work — you cannot see its tests.

Do what the task asks. Nothing more, nothing less. Follow the instruction literally:
- If it says to put files in /app/, put them in /app/ — not /tmp/, not elsewhere.
- If it specifies a function signature like `foo(x, bounds)`, implement exactly that — not `foo(x, lb, ub)`.
- If it says to download and build from source, keep the source where it's expected — do not delete it after building.
- If it names specific output files, produce those exact files with those exact names.
- If it specifies a version (e.g., "POV-Ray 2.2"), use that exact version.

First moves:
- Read all files in the task directory to understand the setup.
- Check for /tests/ or run-tests.sh — if present, read them and treat as your spec.
- If no tests are visible, the task instruction IS your only spec. Parse it carefully for exact file names, paths, formats, function signatures, and version requirements.

Execution model:
- Each bash command runs in a separate non-persistent shell.
- Background jobs started with `&` or `nohup` may die when the command ends.
- For persistent services, use a real daemon strategy such as `setsid`, `start-stop-daemon`, or an actual service.

Verification:
- If tests exist, run them before finishing. Fix ALL failures, not just the first one.
- An exit code of 0 from the wrong invocation is not evidence of success.
- Stop once the task is complete and you have a strong success signal. Do not keep rechecking after a clear pass.
- When reimplementing behavior in another language, validate against the reference on multiple inputs.
- Think about what an automated verifier would check: file existence, exact output format, correct paths, function signatures, numeric accuracy, source code presence.

Artifacts:
- Work in the directory the task expects. Default to /app/ unless told otherwise.
- Do not clean up source code, build directories, or intermediate files unless the task explicitly tells you to. The verifier may check that they exist.
- Do not use bash comments as scratchpad reasoning.

Harness constraints:
- Command timeout: each command has a maximum execution time. Long-running builds may be killed. Split large operations.
- Output handling: output longer than ~12,000 characters is truncated and persisted to /tmp/ktb-agent-artifacts/. You will see a preview and the path.
- Episode budget: you have a fixed number of episodes. The harness warns at 50% and 75%.
- Failure tracking: repeated failures of the same command family trigger warnings. Change approach early.
- Loop detection: repeating the same command sequence triggers an interrupt.

When the task is complete, respond briefly with no tool calls.
"""

TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command and return stdout/stderr and the exit code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute.",
                },
                "timeout_sec": {
                    "type": "number",
                    "description": "Maximum time to wait for the command to finish.",
                    "default": 180,
                },
            },
            "required": ["command"],
        },
    },
]


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _openrouter_client_kwargs() -> dict:
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get(
        "OPENROUTER_API_KEY"
    )
    if not auth_token:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    headers = {"X-Title": "kill-terminalbench"}
    http_referer = os.environ.get("OPENROUTER_HTTP_REFERER")
    if http_referer:
        headers["HTTP-Referer"] = http_referer

    timeout_sec = _env_float("OPENROUTER_TIMEOUT_SEC", 120.0)

    return {
        "api_key": None,
        "auth_token": auth_token,
        "base_url": os.environ.get("ANTHROPIC_BASE_URL", "https://openrouter.ai/api"),
        "timeout": httpx.Timeout(
            connect=min(timeout_sec, 10.0),
            read=timeout_sec,
            write=timeout_sec,
            pool=timeout_sec,
        ),
        "max_retries": _env_int("OPENROUTER_MAX_RETRIES", 1),
        "default_headers": headers,
    }


def get_openrouter_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(**_openrouter_client_kwargs())


def get_async_openrouter_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(**_openrouter_client_kwargs())


def truncate_text(text: str) -> str:
    if not text.strip():
        return "(no output)"
    if len(text) > 50000:
        return text[:25000] + "\n\n... [truncated] ...\n\n" + text[-25000:]
    return text


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
