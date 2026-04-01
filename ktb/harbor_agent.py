"""Harbor-native OpenRouter agent."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .harbor_compaction import compact_messages, is_prompt_too_long_error, should_compact
from .harbor_tooling import ToolExecution, ensure_remote_artifact_dir, format_exec_output, prepare_tool_results
from .openrouter_common import SYSTEM_PROMPT, TOOLS, ensure_dir, get_openrouter_client

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

INFRA_BLOCKERS = (
    "lacks support for the sse3 instruction set",
    "sessionnotcreatedexception: message: session not created: chrome instance exited",
)

# Loop detection: track recent (command, output_hash) pairs.
# If the same set of commands repeats 3 times, nudge the agent.
LOOP_WINDOW = 3  # consecutive episodes to compare


def _usage_value(usage: Any, field: str) -> int | float:
    if usage is None:
        return 0
    value = getattr(usage, field, 0)
    return value or 0


def _commands_signature(tool_results: list[ToolExecution]) -> tuple[tuple[str, int], ...]:
    """Fingerprint an episode's commands by (command, return_code)."""
    return tuple((t.command.strip(), t.return_code) for t in tool_results)


def _detect_loop(history: list[tuple[tuple[str, int], ...]], window: int = LOOP_WINDOW) -> bool:
    """True if the last `window` episodes have identical command signatures."""
    if len(history) < window:
        return False
    recent = history[-window:]
    return all(sig == recent[0] for sig in recent) and len(recent[0]) > 0


def _is_infra_blocker(output: str) -> bool:
    lowered = output.lower()
    return any(marker in lowered for marker in INFRA_BLOCKERS)


# --- No-op and re-read detection helpers ---

_FILE_PATH_RE = re.compile(r'(/(?:app|root|home|tmp|var|etc|opt|srv|mnt)/\S+\.\w{1,5})\b')

# Paths likely to be required deliverables in the task instruction
_DELIVERABLE_PATH_RE = re.compile(r'(/app/\S+\.\w{1,5})\b')


def _is_noop_command(command: str) -> bool:
    """Detect bash commands with no side effects (only comments and/or plain echo)."""
    for line in command.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Plain echo with no redirects or pipes
        if re.match(r'^echo\b', stripped) and not re.search(r'[>|&]', stripped):
            continue
        return False
    return True


def _extract_read_paths(tool_results: list[ToolExecution]) -> set[str]:
    """Extract file paths from read-like commands (cat, sed, head, tail)."""
    paths: set[str] = set()
    for t in tool_results:
        tokens = t.command.strip().split()
        if not tokens:
            continue
        if tokens[0] in ("cat", "sed", "head", "tail", "less", "more"):
            for m in _FILE_PATH_RE.finditer(t.command):
                paths.add(m.group(1))
    return paths


class OpenRouterHarborAgent(BaseAgent):
    @staticmethod
    def name() -> str:
        return "ktb-openrouter"

    def __init__(
        self,
        logs_dir: Path,
        model_name: str | None = None,
        max_episodes: int = 75,
        command_timeout: int = 300,
        temperature: float = 0.7,
        **kwargs,
    ):
        super().__init__(logs_dir=logs_dir, model_name=model_name, **kwargs)
        self._client = get_openrouter_client()
        self._max_episodes = max_episodes
        self._command_timeout = command_timeout
        self._temperature = temperature

    def version(self) -> str | None:
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        await ensure_remote_artifact_dir(environment)

    @staticmethod
    def _update_context(
        context: AgentContext,
        *,
        total_input_tokens: int,
        total_output_tokens: int,
        total_cost: float,
        generation_ids: list[str],
        episodes_completed: int,
        metadata_extra: dict[str, Any] | None = None,
    ) -> None:
        metadata: dict[str, Any] = {
            "generation_ids": generation_ids,
            "episodes": episodes_completed,
        }
        if metadata_extra:
            metadata.update(metadata_extra)
        context.n_input_tokens = total_input_tokens
        context.n_output_tokens = total_output_tokens
        context.cost_usd = round(total_cost, 8)
        context.metadata = metadata

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        generation_ids: list[str] = []
        compaction_count = 0
        last_compaction_episode: int | None = None

        agent_logs = ensure_dir(self.logs_dir / "episodes")
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": f"Task:\n{instruction}",
            }
        ]
        episode_signatures: list[tuple[tuple[str, int], ...]] = []
        noop_streak = 0
        file_read_streak: dict[str, int] = {}

        # Extract candidate deliverable paths from the instruction
        deliverable_paths = list(dict.fromkeys(_DELIVERABLE_PATH_RE.findall(instruction)))
        deliverable_checked = False

        for episode in range(self._max_episodes):
            model_attempts = 0
            try:
                current_max_tokens = 8192
                while True:
                    try:
                        response = self._client.messages.create(
                            model=self.model_name or "anthropic/claude-opus-4.6",
                            max_tokens=current_max_tokens,
                            system=SYSTEM_PROMPT,
                            tools=TOOLS,
                            messages=messages,
                            temperature=self._temperature,
                        )
                    except Exception as exc:
                        if (
                            is_prompt_too_long_error(exc)
                            and model_attempts < 3
                            and len(messages) > 2
                        ):
                            messages = compact_messages(
                                client=self._client,
                                messages=messages,
                                logs_dir=self.logs_dir,
                                compaction_index=compaction_count,
                            )
                            compaction_count += 1
                            last_compaction_episode = episode
                            model_attempts += 1
                            continue
                        raise

                    if response.stop_reason == "max_tokens" and current_max_tokens < 65536:
                        current_max_tokens = 65536
                        model_attempts += 1
                        continue
                    break
            except Exception as exc:
                self._update_context(
                    context,
                    total_input_tokens=total_input_tokens,
                    total_output_tokens=total_output_tokens,
                    total_cost=total_cost,
                    generation_ids=generation_ids,
                    episodes_completed=episode,
                    metadata_extra={
                        "failure_kind": "model_call_error",
                        "failure_episode": episode,
                    },
                )
                raise RuntimeError(
                    f"Model call failed at episode {episode}: {exc}"
                ) from exc

            usage = getattr(response, "usage", None)
            total_input_tokens += int(_usage_value(usage, "input_tokens"))
            total_output_tokens += int(_usage_value(usage, "output_tokens"))
            total_cost += float(_usage_value(usage, "cost"))
            if response.id:
                generation_ids.append(response.id)

            episode_dir = ensure_dir(agent_logs / f"episode-{episode}")
            (episode_dir / "request.json").write_text(
                json.dumps(
                    {
                        "system": SYSTEM_PROMPT,
                        "tools": TOOLS,
                        "messages": messages,
                        "model": self.model_name,
                        "temperature": self._temperature,
                    },
                    indent=2,
                    default=str,
                )
            )
            (episode_dir / "response.json").write_text(
                json.dumps(response.model_dump(mode="json"), indent=2)
            )

            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            self._update_context(
                context,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                total_cost=total_cost,
                generation_ids=generation_ids,
                episodes_completed=episode + 1,
            )

            tool_results = []
            for block in assistant_content:
                if block.type != "tool_use" or block.name != "bash":
                    continue

                command = block.input.get("command", "")
                timeout_sec = int(block.input.get("timeout_sec", self._command_timeout))
                timeout_sec = min(timeout_sec, self._command_timeout)

                # Reject empty/whitespace-only commands without executing
                if not command or not command.strip():
                    execution = ToolExecution(
                        tool_use_id=block.id,
                        command=command,
                        return_code=1,
                        stdout=None,
                        stderr="[Harness] Empty command. Provide a real command to execute.",
                        timeout_sec=timeout_sec,
                    )
                    tool_results.append(execution)
                    continue

                result = await environment.exec(command, timeout_sec=timeout_sec)
                execution = ToolExecution(
                    tool_use_id=block.id,
                    command=command,
                    return_code=result.return_code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    timeout_sec=timeout_sec,
                )
                tool_results.append(execution)

                output = format_exec_output(
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.return_code,
                    command=command,
                    timeout_sec=timeout_sec,
                )

                if _is_infra_blocker(output):
                    persisted_tool_results = await prepare_tool_results(
                        executions=tool_results,
                        episode=episode,
                        logs_dir=self.logs_dir,
                        environment=environment,
                    )
                    (episode_dir / "tool-results.json").write_text(
                        json.dumps(persisted_tool_results, indent=2)
                    )
                    self._update_context(
                        context,
                        total_input_tokens=total_input_tokens,
                        total_output_tokens=total_output_tokens,
                        total_cost=total_cost,
                        generation_ids=generation_ids,
                        episodes_completed=episode + 1,
                        metadata_extra={
                            "failure_kind": "infra_blocker",
                            "failure_episode": episode,
                            "failure_command": command,
                            "failure_output": output,
                        },
                    )
                    raise RuntimeError(
                        "Infra blocker detected in task environment: "
                        "Chromium/WebDriver cannot start on this ARM/qemu setup "
                        f"(episode {episode})."
                    )

            if not tool_results:
                break

            persisted_tool_results = await prepare_tool_results(
                executions=tool_results,
                episode=episode,
                logs_dir=self.logs_dir,
                environment=environment,
            )
            (episode_dir / "tool-results.json").write_text(
                json.dumps(persisted_tool_results, indent=2)
            )
            messages.append({"role": "user", "content": persisted_tool_results})

            # --- No-op detection ---
            all_noop = tool_results and all(
                _is_noop_command(t.command) for t in tool_results
            )
            if all_noop:
                noop_streak += 1
                if noop_streak == 1:
                    messages.append({
                        "role": "user",
                        "content": (
                            "[Harness] Your last command(s) had no side effects (comments/echo only). "
                            "Do not use bash as a scratchpad. Execute real commands that make progress."
                        ),
                    })
                elif noop_streak >= 2:
                    messages.append({
                        "role": "user",
                        "content": (
                            "[Harness] Multiple consecutive no-op commands. "
                            "You must execute a command that changes state or produces output. "
                            "If you are stuck, try a different approach."
                        ),
                    })
            else:
                noop_streak = 0

            # --- Re-read detection ---
            episode_reads = _extract_read_paths(tool_results)
            updated_streaks: dict[str, int] = {}
            for path in episode_reads:
                updated_streaks[path] = file_read_streak.get(path, 0) + 1
            file_read_streak = updated_streaks

            reread_path = next(
                (p for p, c in file_read_streak.items() if c >= 3),
                None,
            )
            if reread_path:
                messages.append({
                    "role": "user",
                    "content": (
                        f"[Harness] You have read {reread_path} in "
                        f"{file_read_streak[reread_path]} consecutive episodes without "
                        "modifying it. Stop re-reading and implement the needed changes."
                    ),
                })
                file_read_streak[reread_path] = 0  # Reset after nudge

            # --- Loop detection ---
            episode_signatures.append(_commands_signature(tool_results))
            if _detect_loop(episode_signatures):
                messages.append({
                    "role": "user",
                    "content": (
                        "[Harness] You have run the same commands 3 episodes in a row with identical results. "
                        "Either take a different action to make progress, or if the task is already complete, "
                        "respond with no tool calls to finish."
                    ),
                })

            # --- Budget warnings ---
            pct = (episode + 1) / self._max_episodes
            if self._max_episodes >= 10:
                if episode + 1 == self._max_episodes // 2:
                    messages.append({
                        "role": "user",
                        "content": f"[Harness] 50% of episode budget used ({episode + 1}/{self._max_episodes}).",
                    })

                    # --- Missing-deliverable check at 50% ---
                    if deliverable_paths and not deliverable_checked:
                        check_cmd = " && ".join(
                            f"test -f {p} && echo 'EXISTS {p}' || echo 'MISSING {p}'"
                            for p in deliverable_paths[:5]
                        )
                        check_result = await environment.exec(check_cmd, timeout_sec=10)
                        check_output = (check_result.stdout or "") + (check_result.stderr or "")
                        missing = [
                            p for p in deliverable_paths
                            if f"MISSING {p}" in check_output
                        ]
                        if missing:
                            missing_list = ", ".join(missing)
                            messages.append({
                                "role": "user",
                                "content": (
                                    f"[Harness] Required deliverable(s) still missing: {missing_list}. "
                                    "Produce a minimally valid version now, then refine."
                                ),
                            })
                        deliverable_checked = True

                elif episode + 1 == (self._max_episodes * 3) // 4:
                    messages.append({
                        "role": "user",
                        "content": (
                            f"[Harness] 75% of episode budget used ({episode + 1}/{self._max_episodes}). "
                            "Wrap up soon — if the task is done, stop with no tool calls."
                        ),
                    })

            if should_compact(
                total_input_tokens,
                messages,
                episode=episode,
                last_compaction_episode=last_compaction_episode,
            ):
                messages = compact_messages(
                    client=self._client,
                    messages=messages,
                    logs_dir=self.logs_dir,
                    compaction_index=compaction_count,
                )
                compaction_count += 1
                last_compaction_episode = episode

        self._update_context(
            context,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_cost=total_cost,
            generation_ids=generation_ids,
            episodes_completed=len(list(agent_logs.glob("episode-*"))),
            metadata_extra={"compactions": compaction_count},
        )
