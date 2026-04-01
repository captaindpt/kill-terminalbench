"""Tool-result formatting and persistence helpers for Harbor runs."""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from pathlib import Path

from harbor.environments.base import BaseEnvironment

from .openrouter_common import ensure_dir


REMOTE_ARTIFACT_DIR = "/tmp/ktb-agent-artifacts"


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


TOOL_PREVIEW_CHARS = _env_int("KTB_TOOL_PREVIEW_CHARS", 2000)
TOOL_PERSIST_THRESHOLD_CHARS = _env_int("KTB_TOOL_PERSIST_THRESHOLD_CHARS", 12000)
TOOL_AGGREGATE_LIMIT_CHARS = _env_int("KTB_TOOL_AGGREGATE_LIMIT_CHARS", 200000)


SEMANTIC_EXIT_CODE_NOTES = {
    "grep": {1: "no matches found"},
    "rg": {1: "no matches found"},
    "diff": {1: "differences found"},
    "cmp": {1: "files differ"},
    "test": {1: "condition was false"},
    "[": {1: "condition was false"},
}


@dataclass
class ToolExecution:
    tool_use_id: str
    command: str
    return_code: int
    stdout: str | None
    stderr: str | None
    timeout_sec: int | None = None


@dataclass
class PreparedToolResult:
    tool_use_id: str
    command: str
    formatted_output: str
    content: str
    content_len: int
    persisted: bool
    local_artifact_path: Path | None = None
    remote_artifact_path: str | None = None


def _command_name(command: str) -> str | None:
    for raw_line in command.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            first = shlex.split(line, comments=False)
        except ValueError:
            first = line.split()
        if not first:
            continue
        token = first[0]
        if "=" in token and not token.startswith(("./", "/")):
            continue
        return token
    return None


def _exit_code_note(command: str, return_code: int) -> str | None:
    command_name = _command_name(command)
    if command_name is None:
        return None
    notes = SEMANTIC_EXIT_CODE_NOTES.get(command_name)
    if notes is None:
        return None
    return notes.get(return_code)


def _preview_text(text: str, limit: int = TOOL_PREVIEW_CHARS) -> str:
    if len(text) <= limit:
        return text
    head_len = limit // 2
    tail_len = limit - head_len
    omitted = len(text) - head_len - tail_len
    return (
        text[:head_len]
        + f"\n\n... [{omitted} chars omitted] ...\n\n"
        + text[-tail_len:]
    )


def format_exec_output(
    stdout: str | None,
    stderr: str | None,
    return_code: int,
    command: str,
    timeout_sec: int | None = None,
) -> str:
    note = _exit_code_note(command, return_code)
    header = f"[exit_code={return_code}]"
    if note:
        header = f"[exit_code={return_code}; note={note}]"
    if return_code == 143 and timeout_sec:
        timeout_note = f"command timed out after {timeout_sec}s"
        header = f"[exit_code={return_code}; note={timeout_note}]"

    parts = [header]
    if stdout:
        parts.append(stdout.rstrip())
    if stderr:
        parts.append(f"[stderr]\n{stderr.rstrip()}")

    text = "\n\n".join(part for part in parts if part)
    return text if text.strip() else f"{header}\n\n(no output)"


async def ensure_remote_artifact_dir(environment: BaseEnvironment) -> None:
    await environment.exec(
        f"mkdir -p {shlex.quote(REMOTE_ARTIFACT_DIR)}",
        timeout_sec=30,
    )


async def _persist_result(
    *,
    prepared: PreparedToolResult,
    episode: int,
    tool_index: int,
    local_dir: Path,
    environment: BaseEnvironment,
) -> PreparedToolResult:
    ensure_dir(local_dir)
    local_path = local_dir / f"tool-{tool_index:02d}.txt"
    local_path.write_text(prepared.formatted_output)

    remote_path = f"{REMOTE_ARTIFACT_DIR}/episode-{episode:03d}-tool-{tool_index:02d}.txt"
    await environment.upload_file(local_path, remote_path)

    preview = _preview_text(prepared.formatted_output)
    content = (
        f"[persisted_output]\n"
        f"Full output saved to {remote_path}\n"
        f"Use `cat {shlex.quote(remote_path)}` to inspect the full result.\n\n"
        f"[preview]\n{preview}"
    )

    prepared.persisted = True
    prepared.local_artifact_path = local_path
    prepared.remote_artifact_path = remote_path
    prepared.content = content
    prepared.content_len = len(content)
    return prepared


async def prepare_tool_results(
    *,
    executions: list[ToolExecution],
    episode: int,
    logs_dir: Path,
    environment: BaseEnvironment,
) -> list[dict[str, str]]:
    local_dir = ensure_dir(logs_dir / "persisted-tool-results" / f"episode-{episode}")
    prepared_results: list[PreparedToolResult] = []

    for tool_index, execution in enumerate(executions):
        formatted_output = format_exec_output(
            stdout=execution.stdout,
            stderr=execution.stderr,
            return_code=execution.return_code,
            command=execution.command,
            timeout_sec=execution.timeout_sec,
        )
        prepared = PreparedToolResult(
            tool_use_id=execution.tool_use_id,
            command=execution.command,
            formatted_output=formatted_output,
            content=formatted_output,
            content_len=len(formatted_output),
            persisted=False,
        )
        if prepared.content_len > TOOL_PERSIST_THRESHOLD_CHARS:
            prepared = await _persist_result(
                prepared=prepared,
                episode=episode,
                tool_index=tool_index,
                local_dir=local_dir,
                environment=environment,
            )
        prepared_results.append(prepared)

    total_chars = sum(item.content_len for item in prepared_results)
    if total_chars > TOOL_AGGREGATE_LIMIT_CHARS:
        candidates = sorted(
            (
                (idx, item)
                for idx, item in enumerate(prepared_results)
                if not item.persisted
            ),
            key=lambda pair: pair[1].content_len,
            reverse=True,
        )
        for idx, item in candidates:
            item = await _persist_result(
                prepared=item,
                episode=episode,
                tool_index=idx,
                local_dir=local_dir,
                environment=environment,
            )
            prepared_results[idx] = item
            total_chars = sum(result.content_len for result in prepared_results)
            if total_chars <= TOOL_AGGREGATE_LIMIT_CHARS:
                break

    return [
        {
            "type": "tool_result",
            "tool_use_id": item.tool_use_id,
            "content": item.content,
        }
        for item in prepared_results
    ]
