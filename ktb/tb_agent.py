"""Terminal-Bench-native agent that talks to OpenRouter via Anthropic's SDK."""

from __future__ import annotations

import json
from pathlib import Path

from .openrouter_common import SYSTEM_PROMPT, TOOLS, get_openrouter_client, truncate_text
from .tb_runtime import ensure_terminal_bench_importable

ensure_terminal_bench_importable()

from terminal_bench.agents.base_agent import AgentResult, BaseAgent
from terminal_bench.agents.failure_mode import FailureMode
from terminal_bench.terminal.tmux_session import TmuxSession

class OpenRouterBenchAgent(BaseAgent):
    @staticmethod
    def name() -> str:
        return "ktb-openrouter"

    def __init__(
        self,
        model_name: str = "anthropic/claude-opus-4.6",
        max_episodes: int = 75,
        bash_timeout: int = 300,
        temperature: float = 1.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._client = get_openrouter_client()
        self._model_name = model_name
        self._max_episodes = max_episodes
        self._bash_timeout = bash_timeout
        self._temperature = temperature

    def perform_task(
        self,
        instruction: str,
        session: TmuxSession,
        logging_dir: Path | None = None,
    ) -> AgentResult:
        total_input_tokens = 0
        total_output_tokens = 0

        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"Task:\n{instruction}\n\n"
                    f"Initial terminal state:\n{session.capture_pane(capture_entire=True)}"
                ),
            }
        ]

        for episode in range(self._max_episodes):
            response = self._client.messages.create(
                model=self._model_name,
                max_tokens=16384,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
                temperature=self._temperature,
            )

            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            if logging_dir is not None:
                episode_dir = logging_dir / f"episode-{episode}"
                episode_dir.mkdir(parents=True, exist_ok=True)
                (episode_dir / "response.json").write_text(
                    json.dumps(response.model_dump(mode="json"), indent=2)
                )

            tool_results = []
            for block in assistant_content:
                if block.type != "tool_use" or block.name != "bash":
                    continue

                command = block.input.get("command", "")
                timeout_sec = int(block.input.get("timeout_sec", self._bash_timeout))
                timeout_sec = min(timeout_sec, self._bash_timeout)

                try:
                    session.send_keys(
                        [command, "Enter"],
                        block=True,
                        max_timeout_sec=timeout_sec,
                    )
                    output = session.get_incremental_output()
                except TimeoutError:
                    output = (
                        f"Command timed out after {timeout_sec}s.\n"
                        f"Current terminal screen:\n{session.capture_pane()}"
                    )

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": truncate_text(output),
                    }
                )

            if not tool_results:
                return AgentResult(
                    total_input_tokens=total_input_tokens,
                    total_output_tokens=total_output_tokens,
                    failure_mode=FailureMode.NONE,
                )

            messages.append({"role": "user", "content": tool_results})

        return AgentResult(
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            failure_mode=FailureMode.NONE,
        )
