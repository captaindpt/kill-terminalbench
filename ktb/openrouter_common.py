"""Shared OpenRouter client helpers."""

from __future__ import annotations

import os
from pathlib import Path

import anthropic


SYSTEM_PROMPT = """You are solving a task in a Linux environment.

Work directly in the shell.
Inspect the environment before changing it.
Read errors carefully and adapt.
Before finishing, remove any temp files or build artifacts you created that aren't part of the deliverable.
A separate verifier tests your work automatically.

Execution model:
- Each bash command runs in a separate non-persistent shell.
- Background jobs started with `&` or `nohup` may die when the command ends.
- For persistent services, use a real daemon strategy such as `setsid`, `start-stop-daemon`, or an actual service.

Verification:
- When task tests or verifier scripts are visible, run them the way they are intended to run.
- An exit code of 0 from the wrong invocation is not evidence of success.
- Stop once the task is complete and you have a strong success signal aligned with the task's actual checks.
- Do not keep rechecking after a clear pass, but do not stop on weak or ambiguous signals.
- If multiple required output files are of the same kind, prefer producing them in one coordinated script or pass.
- When possible, produce a minimally valid deliverable early, then refine it.
- When a task explicitly names a package, framework, or API, use that exact interface — not lower-level substitutes — unless you verify equivalence.
- When reimplementing model or algorithm behavior in another language, validate against the reference on multiple representative inputs, not just the bundled example.

Artifacts and scratch work:
- Build or compile scratch binaries in `/tmp` unless the task explicitly requires them in the deliverable directory.
- Do not leave test binaries, build artifacts, or temp files in the deliverable directory unless they are part of the required output.
- Do not use bash comments or comment-only shell commands as scratchpad reasoning. Use the shell to make progress on the task.

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


def get_openrouter_client() -> anthropic.Anthropic:
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get(
        "OPENROUTER_API_KEY"
    )
    if not auth_token:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    headers = {"X-Title": "kill-terminalbench"}
    http_referer = os.environ.get("OPENROUTER_HTTP_REFERER")
    if http_referer:
        headers["HTTP-Referer"] = http_referer

    return anthropic.Anthropic(
        api_key=None,
        auth_token=auth_token,
        base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://openrouter.ai/api"),
        timeout=_env_float("OPENROUTER_TIMEOUT_SEC", 120.0),
        max_retries=_env_int("OPENROUTER_MAX_RETRIES", 1),
        default_headers=headers,
    )


def truncate_text(text: str) -> str:
    if not text.strip():
        return "(no output)"
    if len(text) > 50000:
        return text[:25000] + "\n\n... [truncated] ...\n\n" + text[-25000:]
    return text


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
