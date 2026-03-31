"""Wrapper around Harbor CLI for official TB 2.0 runs."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

from .agent import AgentConfig
from .openrouter_usage import (
    fetch_credits,
    fetch_key_info,
    write_run_usage_summary,
)


def run_harbor(
    *,
    config: AgentConfig,
    output_path: Path | None = None,
    dataset: str = "terminal-bench@2.0",
    task_names: list[str] | None = None,
    n_concurrent_trials: int = 1,
) -> Path:
    jobs_dir = output_path or Path("jobs")
    job_name = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
    harbor_bin = Path(".venv/bin/harbor")

    key_info_before = fetch_key_info()
    credits_before = fetch_credits()

    cmd = [
        str(harbor_bin),
        "run",
        "--yes",
        "--env-file",
        str(Path(".env").resolve()),
        "--jobs-dir",
        str(jobs_dir),
        "--job-name",
        job_name,
        "--dataset",
        dataset,
        "--agent-import-path",
        "ktb.harbor_agent:OpenRouterHarborAgent",
        "--model",
        config.model,
        "--n-concurrent",
        str(n_concurrent_trials),
        "--ak",
        f"max_episodes={config.max_turns}",
        "--ak",
        f"temperature={config.temperature}",
        "--ak",
        f"command_timeout={config.bash_timeout}",
    ]

    for task_name in task_names or []:
        cmd.extend(["--include-task-name", task_name])

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd()) + os.pathsep + env.get("PYTHONPATH", "")

    subprocess.run(cmd, check=True, env=env)

    job_dir = jobs_dir / job_name
    usage_path = write_run_usage_summary(
        job_dir,
        key_info_before=key_info_before,
        key_info_after=fetch_key_info(),
        credits_before=credits_before,
        credits_after=fetch_credits(),
    )
    print(f"OpenRouter usage saved to {usage_path}")
    return job_dir
