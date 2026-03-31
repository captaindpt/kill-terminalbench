"""Shared OpenRouter client helpers."""

from __future__ import annotations

import os
from pathlib import Path

import anthropic


SYSTEM_PROMPT = """You are solving a task in a Linux environment.

Work directly in the shell.
Inspect the environment before changing it.
Read errors carefully and adapt.
Verify your work before finishing.
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
