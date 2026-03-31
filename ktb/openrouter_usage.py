"""OpenRouter usage helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _get_openrouter_key() -> str | None:
    return os.environ.get("OPENROUTER_API_KEY")


def _api_get_json(url: str) -> dict[str, Any] | None:
    key = _get_openrouter_key()
    if not key:
        return None

    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None


def fetch_key_info() -> dict[str, Any] | None:
    payload = _api_get_json("https://openrouter.ai/api/v1/key")
    if payload is None:
        return None
    return payload.get("data")


def fetch_credits() -> dict[str, Any] | None:
    payload = _api_get_json("https://openrouter.ai/api/v1/credits")
    if payload is None:
        return None
    return payload.get("data")


def summarize_run_usage(run_dir: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "episodes": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost": 0.0,
        "generations": [],
    }

    for response_path in sorted(run_dir.rglob("response.json")):
        data = json.loads(response_path.read_text())
        usage = data.get("usage") or {}
        generation = {
            "id": data.get("id"),
            "path": str(response_path.relative_to(run_dir)),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cost": usage.get("cost", 0.0),
        }
        summary["episodes"] += 1
        summary["input_tokens"] += generation["input_tokens"]
        summary["output_tokens"] += generation["output_tokens"]
        summary["cost"] += generation["cost"]
        summary["generations"].append(generation)

    summary["cost"] = round(summary["cost"], 8)
    return summary


def write_run_usage_summary(
    run_dir: Path,
    *,
    key_info_before: dict[str, Any] | None = None,
    key_info_after: dict[str, Any] | None = None,
    credits_before: dict[str, Any] | None = None,
    credits_after: dict[str, Any] | None = None,
) -> Path:
    summary = {
        "run_dir": str(run_dir),
        "run_usage": summarize_run_usage(run_dir),
        "openrouter": {
            "key_info_before": key_info_before,
            "key_info_after": key_info_after,
            "credits_before": credits_before,
            "credits_after": credits_after,
        },
    }
    output_path = run_dir / "openrouter-usage.json"
    output_path.write_text(json.dumps(summary, indent=2))
    return output_path
