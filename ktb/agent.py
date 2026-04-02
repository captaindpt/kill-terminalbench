"""Core agent loop. Minimal scaffolding, maximum context for the model."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

import anthropic

from .prompts import SYSTEM_PROMPT, TOOLS


@dataclass
class AgentResult:
    success: bool = False
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    num_turns: int = 0
    wall_time_sec: float = 0.0
    error: Optional[str] = None


@dataclass
class AgentConfig:
    backend: str = "openrouter"
    model: str = "anthropic/claude-opus-4.6"
    max_turns: int = 75
    max_tokens: int = 16384
    bash_timeout: int = 700
    temperature: float = 1.0


def _format_command_output(stdout: str, stderr: str, returncode: int) -> str:
    parts = [f"[exit_code={returncode}]"]
    if stdout:
        parts.append(stdout.rstrip())
    if stderr:
        parts.append(f"[stderr]\n{stderr.rstrip()}")

    output = "\n\n".join(part for part in parts if part)
    if len(output) > 50000:
        output = output[:25000] + "\n\n... [truncated] ...\n\n" + output[-25000:]
    return output


def run_bash_in_container(container_name: str, command: str, timeout: int = 300) -> str:
    """Execute a bash command inside a docker container."""
    try:
        result = subprocess.run(
            ["docker", "exec", container_name, "bash", "-lc", command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return _format_command_output(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT after {timeout}s]"
    except Exception as e:
        return f"[ERROR: {e}]"


def run_agent(
    instruction: str,
    container_name: str,
    config: Optional[AgentConfig] = None,
) -> AgentResult:
    """Run the agent loop on a task."""
    if config is None:
        config = AgentConfig()

    if config.backend != "openrouter":
        raise ValueError(f"Unsupported agent backend: {config.backend}")

    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get(
        "OPENROUTER_API_KEY"
    )
    if not auth_token:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to .env or use --backend solution to validate the harness without a model."
        )

    default_headers = {"X-Title": "kill-terminalbench"}
    http_referer = os.environ.get("OPENROUTER_HTTP_REFERER")
    if http_referer:
        default_headers["HTTP-Referer"] = http_referer

    client = anthropic.Anthropic(
        api_key=None,
        auth_token=auth_token,
        base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://openrouter.ai/api"),
        default_headers=default_headers,
    )
    result = AgentResult()
    start = time.time()

    messages = [
        {"role": "user", "content": f"Task:\n{instruction}"},
    ]

    for turn in range(config.max_turns):
        result.num_turns = turn + 1

        response = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
            temperature=config.temperature,
        )

        result.total_input_tokens += response.usage.input_tokens
        result.total_output_tokens += response.usage.output_tokens

        # Process response
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        # Check if model wants to use tools
        tool_uses = [b for b in assistant_content if b.type == "tool_use"]

        if not tool_uses:
            # Model is done (end_turn with no tool calls)
            break

        # Execute all tool calls
        tool_results = []
        for tool_use in tool_uses:
            if tool_use.name == "bash":
                cmd = tool_use.input.get("command", "")
                output = run_bash_in_container(
                    container_name, cmd, timeout=config.bash_timeout
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": output,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

    result.wall_time_sec = time.time() - start
    return result
