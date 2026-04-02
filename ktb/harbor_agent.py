"""Harbor-native OpenRouter agent."""

from __future__ import annotations

import json
import os
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

# ---------------------------------------------------------------------------
# Loop detection: sequence-aware pattern matching on recent episodes.
# Detects both identical repeats (A,A,A) and cycling patterns (A,B,A,B,A,B).
# ---------------------------------------------------------------------------
LOOP_MIN_REPS = 3  # minimum repetitions to trigger


def _usage_value(usage: Any, field: str) -> int | float:
    if usage is None:
        return 0
    value = getattr(usage, field, 0)
    return value or 0


def _commands_signature(tool_results: list[ToolExecution]) -> tuple[tuple[str, int], ...]:
    """Fingerprint an episode's commands by (command, return_code)."""
    return tuple((t.command.strip(), t.return_code) for t in tool_results)


def _detect_repeating_pattern(
    history: list[tuple[tuple[str, int], ...]],
    max_pattern_len: int = 3,
    min_reps: int = LOOP_MIN_REPS,
) -> int | None:
    """Detect repeating patterns in episode signature history.

    Checks pattern lengths 1..max_pattern_len, working backwards from the tail.
    Returns the number of consecutive repetitions if a pattern repeats >= min_reps
    times, or None if no pattern is found.

    Pattern length 1: A, A, A          (identical episodes)
    Pattern length 2: A, B, A, B, A, B (two-step cycle)
    Pattern length 3: A, B, C, A, B, C (three-step cycle)
    """
    n = len(history)
    for plen in range(1, max_pattern_len + 1):
        if n < plen * min_reps:
            continue
        # Extract the candidate pattern from the tail
        pattern = history[-plen:]
        # Count how many times it repeats backwards
        reps = 1
        pos = n - plen * 2
        while pos >= 0:
            chunk = history[pos : pos + plen]
            if chunk == pattern:
                reps += 1
                pos -= plen
            else:
                break
        if reps >= min_reps:
            return reps
    return None


def _is_infra_blocker(output: str) -> bool:
    lowered = output.lower()
    return any(marker in lowered for marker in INFRA_BLOCKERS)


# ---------------------------------------------------------------------------
# Per-command-family failure budget with recovery.
# ---------------------------------------------------------------------------
_CMD_FAMILY_RE = re.compile(
    r'^(?:sudo\s+)?'                  # optional sudo
    r'(?:(?:[\w]+=\S+\s+)*)'         # optional env vars
    r'([\w./-]+)'                     # the actual command name
)

MAX_COMMAND_FAMILY_FAILURES = 5  # hard-stop threshold per family


def _command_family(command: str) -> str:
    """Normalize a command to its 'family' for failure tracking.

    Groups by the base command name: python, cargo, gcc, make, pytest, etc.
    Multi-line commands use the first meaningful line.
    """
    for raw_line in command.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        m = _CMD_FAMILY_RE.match(line)
        if m:
            # Normalize path-based commands to basename
            return os.path.basename(m.group(1))
        return line.split()[0] if line.split() else "unknown"
    return "unknown"


class _FailureBudget:
    """Track per-command-family failures with reset-on-success."""

    def __init__(self, limit: int = MAX_COMMAND_FAMILY_FAILURES):
        self._counts: dict[str, int] = {}
        self._limit = limit

    def record(self, family: str, success: bool) -> None:
        if success:
            self._counts.pop(family, None)
        else:
            self._counts[family] = self._counts.get(family, 0) + 1

    def remaining(self, family: str) -> int:
        return max(0, self._limit - self._counts.get(family, 0))

    def exhausted(self, family: str) -> bool:
        return self._counts.get(family, 0) >= self._limit

    def any_exhausted(self) -> str | None:
        """Return the first family that has hit its limit, or None."""
        for family, count in self._counts.items():
            if count >= self._limit:
                return family
        return None

    def nudge_text(self, family: str) -> str:
        remaining = self.remaining(family)
        count = self._counts.get(family, 0)
        return (
            f"[Harness] `{family}` has failed {count} time(s). "
            f"{remaining} attempt(s) remaining before this command family is blocked. "
            f"Before retrying: 1) Pinpoint exactly what went wrong. "
            f"2) Explain why — wrong flags, missing dependency, bad path? "
            f"3) Only then make the corrected attempt."
        )


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


class _ThinkingEffort:
    """Adaptive thinking effort that responds to episode progress and failures.

    Uses Anthropic's adaptive thinking API with effort levels instead of
    deprecated budget_tokens. The model decides how much to think, but
    effort controls the ceiling.

    Strategy:
    - Early episodes (first 20%): max effort for planning and understanding
    - Mid episodes (20-70%): high effort (default — thinks when useful)
    - Late episodes (70%+): high effort (still need correctness)
    - After failures: bump to max for deep reassessment
    """

    def __init__(self):
        self._failure_bump_episodes = 0

    def bump_for_failure(self, episodes: int = 2) -> None:
        """Temporarily increase effort after failures."""
        self._failure_bump_episodes = max(self._failure_bump_episodes, episodes)

    def effort(self, episode: int, max_episodes: int) -> str:
        if self._failure_bump_episodes > 0:
            self._failure_bump_episodes -= 1
            return "max"

        pct = episode / max_episodes if max_episodes > 0 else 0
        if pct < 0.20:
            return "max"
        return "high"

    def thinking_config(self) -> dict:
        """Return the thinking parameter for the API call."""
        return {"type": "adaptive"}

    def output_config(self, episode: int, max_episodes: int) -> dict:
        """Return the output_config parameter for the API call."""
        return {"effort": self.effort(episode, max_episodes)}


class OpenRouterHarborAgent(BaseAgent):
    @staticmethod
    def name() -> str:
        return "ktb-openrouter"

    def __init__(
        self,
        logs_dir: Path,
        model_name: str | None = None,
        max_episodes: int = 75,
        command_timeout: int = 700,
        temperature: float = 0.7,
        **kwargs,
    ):
        # Pop deprecated thinking kwargs silently so old configs don't break
        kwargs.pop("thinking_high", None)
        kwargs.pop("thinking_standard", None)
        kwargs.pop("thinking_low", None)
        super().__init__(logs_dir=logs_dir, model_name=model_name, **kwargs)
        self._client = get_openrouter_client()
        self._max_episodes = max_episodes
        self._command_timeout = command_timeout
        self._temperature = temperature
        self._thinking = _ThinkingEffort()

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
        failure_budget = _FailureBudget()

        # Extract candidate deliverable paths from the instruction
        deliverable_paths = list(dict.fromkeys(_DELIVERABLE_PATH_RE.findall(instruction)))
        deliverable_checked = False

        for episode in range(self._max_episodes):
            model_attempts = 0
            try:
                current_max_tokens = 16000
                thinking_config = self._thinking.thinking_config()
                output_config = self._thinking.output_config(episode, self._max_episodes)
                while True:
                    try:
                        response = self._client.messages.create(
                            model=self.model_name or "anthropic/claude-opus-4.6",
                            max_tokens=current_max_tokens,
                            system=SYSTEM_PROMPT,
                            tools=TOOLS,
                            messages=messages,
                            temperature=1.0,  # required by adaptive thinking API
                            thinking=thinking_config,
                            output_config=output_config,
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
                    # thinking content blocks must be preserved in conversation
                    # history for extended thinking to work across turns
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
                        "thinking": thinking_config,
                        "output_config": output_config,
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

            # --- Per-command failure budget ---
            failure_nudges: list[str] = []
            for t in tool_results:
                family = _command_family(t.command)
                success = t.return_code == 0
                failure_budget.record(family, success)
                if not success and failure_budget.remaining(family) <= 2 and failure_budget.remaining(family) > 0:
                    failure_nudges.append(failure_budget.nudge_text(family))

            blocked_family = failure_budget.any_exhausted()
            if blocked_family:
                messages.append({
                    "role": "user",
                    "content": (
                        f"[Harness] Command family `{blocked_family}` has exhausted its failure budget "
                        f"({MAX_COMMAND_FAMILY_FAILURES} consecutive failures). "
                        "You must use a fundamentally different approach. "
                        "Do not retry this command family without significant changes to your strategy."
                    ),
                })
                self._thinking.bump_for_failure(2)
            elif failure_nudges:
                messages.append({
                    "role": "user",
                    "content": "\n".join(failure_nudges),
                })

            # Bump thinking budget when multiple commands fail in one episode
            episode_failures = sum(1 for t in tool_results if t.return_code != 0)
            if episode_failures >= 2:
                self._thinking.bump_for_failure(1)

            # --- Sequence-aware loop detection ---
            episode_signatures.append(_commands_signature(tool_results))
            reps = _detect_repeating_pattern(episode_signatures)
            if reps is not None:
                messages.append({
                    "role": "user",
                    "content": (
                        f"[Harness] Repeating pattern detected: the same command sequence has repeated "
                        f"{reps} times. You are not making progress. "
                        "Take a fundamentally different approach, or if the task is already complete, "
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
