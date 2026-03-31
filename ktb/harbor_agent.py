"""Harbor-native OpenRouter agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .openrouter_common import SYSTEM_PROMPT, TOOLS, ensure_dir, get_openrouter_client, truncate_text

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


def _format_exec_output(stdout: str | None, stderr: str | None, return_code: int) -> str:
    parts = [f"[exit_code={return_code}]"]
    if stdout:
        parts.append(stdout.rstrip())
    if stderr:
        parts.append(f"[stderr]\n{stderr.rstrip()}")
    return truncate_text("\n\n".join(part for part in parts if part))


INFRA_BLOCKERS = (
    "lacks support for the sse3 instruction set",
    "sessionnotcreatedexception: message: session not created: chrome instance exited",
)


def _is_infra_blocker(output: str) -> bool:
    lowered = output.lower()
    return any(marker in lowered for marker in INFRA_BLOCKERS)


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
        temperature: float = 1.0,
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
        pass

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

        agent_logs = ensure_dir(self.logs_dir / "episodes")
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": f"Task:\n{instruction}",
            }
        ]

        for episode in range(self._max_episodes):
            try:
                response = self._client.messages.create(
                    model=self.model_name or "anthropic/claude-opus-4.6",
                    max_tokens=16384,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                    temperature=self._temperature,
                )
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

            usage = response.usage
            total_input_tokens += usage.input_tokens
            total_output_tokens += usage.output_tokens
            total_cost += getattr(usage, "cost", 0.0) or 0.0
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

                result = await environment.exec(command, timeout_sec=timeout_sec)
                output = _format_exec_output(
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.return_code,
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                    }
                )

                if _is_infra_blocker(output):
                    (episode_dir / "tool-results.json").write_text(
                        json.dumps(tool_results, indent=2)
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

            (episode_dir / "tool-results.json").write_text(
                json.dumps(tool_results, indent=2)
            )
            messages.append({"role": "user", "content": tool_results})

        self._update_context(
            context,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_cost=total_cost,
            generation_ids=generation_ids,
            episodes_completed=len(list(agent_logs.glob("episode-*"))),
        )
