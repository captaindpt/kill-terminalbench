"""Wrapper around Terminal-Bench's native harness."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .agent import AgentConfig
from .openrouter_usage import (
    fetch_credits,
    fetch_key_info,
    write_run_usage_summary,
)
from .tb_runtime import ensure_terminal_bench_importable

ensure_terminal_bench_importable()

from terminal_bench import Harness


def run_terminal_bench(
    *,
    task_ids: list[str],
    tasks_dir: Path,
    config: AgentConfig,
    output_path: Path | None = None,
    no_rebuild: bool = False,
    cleanup: bool = False,
    n_concurrent_trials: int = 1,
) -> Path:
    run_id = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
    runs_dir = output_path or Path("runs")
    key_info_before = fetch_key_info()
    credits_before = fetch_credits()

    harness = Harness(
        dataset_path=tasks_dir,
        output_path=runs_dir,
        run_id=run_id,
        agent_import_path="ktb.tb_agent:OpenRouterBenchAgent",
        model_name=config.model,
        agent_kwargs={
            "max_episodes": config.max_turns,
            "temperature": config.temperature,
            "bash_timeout": config.bash_timeout,
        },
        no_rebuild=no_rebuild,
        cleanup=cleanup,
        log_level=logging.INFO,
        task_ids=task_ids,
        n_concurrent_trials=n_concurrent_trials,
    )
    harness.run()
    run_dir = runs_dir / run_id
    usage_path = write_run_usage_summary(
        run_dir,
        key_info_before=key_info_before,
        key_info_after=fetch_key_info(),
        credits_before=credits_before,
        credits_after=fetch_credits(),
    )
    print(f"OpenRouter usage saved to {usage_path}")
    return run_dir
