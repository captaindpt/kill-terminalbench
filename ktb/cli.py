"""CLI entry point."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .tb_runtime import maybe_reexec_python312
from .task_sets import TASK_SETS, get_task_set


TASKS_DIR = Path(__file__).parent.parent / "terminal-bench" / "original-tasks"

# Our initial test subset — 10 diverse tasks
DEFAULT_TASKS = [
    "hello-world",
    "fix-permissions",
    "csv-to-parquet",
    "fix-pandas-version",
    "openssl-selfsigned-cert",
    "sqlite-db-truncate",
    "heterogeneous-dates",
    "nginx-request-logging",
    "git-multibranch",
    "polyglot-c-py",
]

ENV_PATH = Path(__file__).parent.parent / ".env"


def load_dotenv(path: Path = ENV_PATH) -> None:
    """Load a minimal .env file without adding another dependency."""
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        os.environ.setdefault("ANTHROPIC_BASE_URL", "https://openrouter.ai/api")
        os.environ.setdefault("ANTHROPIC_AUTH_TOKEN", openrouter_key)
        os.environ.setdefault("ANTHROPIC_API_KEY", "")


def load_docker_host_from_context() -> None:
    """Make Docker SDK follow the active Docker CLI context."""
    if os.environ.get("DOCKER_HOST"):
        return

    try:
        context = subprocess.check_output(
            ["docker", "info", "--format", "{{.ClientInfo.Context}}"],
            text=True,
        ).strip()
        if not context:
            return

        context_info = subprocess.check_output(
            ["docker", "context", "inspect", context],
            text=True,
        )
        payload = json.loads(context_info)
        host = payload[0]["Endpoints"]["docker"].get("Host")
        if host:
            os.environ["DOCKER_HOST"] = host
    except Exception:
        pass


def main():
    load_dotenv()
    load_docker_host_from_context()
    maybe_reexec_python312()

    parser = argparse.ArgumentParser(description="kill-terminalbench: minimal agent harness")
    parser.add_argument(
        "--backend",
        choices=["openrouter", "solution"],
        default="openrouter",
        help="Execution backend: OpenRouter-routed Anthropic Messages API or reference solution",
    )
    parser.add_argument(
        "--runner",
        choices=["harbor", "tb", "local"],
        default="harbor",
        help="Use Harbor on terminal-bench@2.0, the local Terminal-Bench harness, or the lightweight local runner",
    )
    parser.add_argument(
        "--dataset",
        default="terminal-bench@2.0",
        help="Dataset identifier for Harbor runs",
    )
    parser.add_argument(
        "--task-set",
        choices=sorted(TASK_SETS),
        default=None,
        help="Named repeatable task subset",
    )
    parser.add_argument("--tasks", nargs="*", default=None, help="Task IDs to run (default: 10-task subset)")
    parser.add_argument("--tasks-dir", type=Path, default=TASKS_DIR, help="Path to tasks directory")
    parser.add_argument("--model", default=os.environ.get("OPENROUTER_MODEL", "anthropic/claude-opus-4.6"), help="Model to use")
    parser.add_argument("--max-turns", type=int, default=75, help="Max agent turns per task")
    parser.add_argument(
        "--n-attempts",
        "-k",
        type=int,
        default=1,
        help="Number of attempts per task/trial for Harbor runs (use 5 for leaderboard-comparable TB2 runs)",
    )
    parser.add_argument("--output", type=Path, default=None, help="Output JSON file for results")
    parser.add_argument("--single", type=str, default=None, help="Run a single task by ID")
    parser.add_argument("--no-rebuild", action="store_true", help="Skip rebuilding task containers")
    parser.add_argument("--cleanup", action="store_true", help="Remove built images after the run")
    parser.add_argument("--n-concurrent", type=int, default=1, help="Concurrent trials for the Terminal-Bench harness")
    args = parser.parse_args()

    if args.single and args.task_set:
        parser.error("--single and --task-set are mutually exclusive")
    if args.tasks and args.task_set:
        parser.error("--tasks and --task-set are mutually exclusive")

    named_task_set = get_task_set(args.task_set) if args.task_set else None
    task_ids = (
        [args.single]
        if args.single
        else list(named_task_set.tasks) if named_task_set else (args.tasks or DEFAULT_TASKS)
    )
    from .agent import AgentConfig

    config = AgentConfig(
        backend=args.backend,
        model=args.model,
        max_turns=args.max_turns,
    )

    print(f"kill-terminalbench v0.1.0")
    print(f"Backend: {config.backend}")
    print(f"Runner: {args.runner}")
    print(f"Model: {config.model}")
    print(f"Tasks: {len(task_ids)}")
    if named_task_set:
        print(f"Task set: {named_task_set.name}")
    print(f"Max turns: {config.max_turns}")
    if args.runner == "harbor":
        print(f"Attempts per task: {args.n_attempts}")
    print()

    if args.runner in {"tb", "harbor"} and config.backend != "openrouter":
        parser.error(f"--runner {args.runner} only supports --backend openrouter")

    if args.runner == "harbor":
        from .harbor_runner import run_harbor

        job_dir = run_harbor(
            config=config,
            output_path=args.output,
            dataset=args.dataset,
            task_names=task_ids,
            n_concurrent_trials=args.n_concurrent,
            n_attempts=args.n_attempts,
        )
        print(f"Job saved to {job_dir}")
        return

    if args.runner == "tb":
        from .tb_runner import run_terminal_bench

        run_dir = run_terminal_bench(
            task_ids=task_ids,
            tasks_dir=args.tasks_dir,
            config=config,
            output_path=args.output,
            no_rebuild=args.no_rebuild,
            cleanup=args.cleanup,
            n_concurrent_trials=args.n_concurrent,
        )
        print(f"Run saved to {run_dir}")
        return

    results: list[TaskResult] = []
    start = time.time()
    from .runner import TaskResult, load_task, run_task

    for i, task_id in enumerate(task_ids):
        task_dir = args.tasks_dir / task_id
        if not task_dir.exists():
            print(f"[{i+1}/{len(task_ids)}] {task_id}: SKIP (not found)")
            continue

        print(f"[{i+1}/{len(task_ids)}] {task_id}")
        task = load_task(task_dir)
        result = run_task(task, config)
        results.append(result)
        print()

    elapsed = time.time() - start
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    print("=" * 60)
    print(f"Results: {passed}/{total} ({100*passed/total:.1f}%)")
    print(f"Total time: {elapsed:.0f}s")
    print()

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        tokens = r.agent_result.total_input_tokens + r.agent_result.total_output_tokens
        print(f"  {status}  {r.task_id} ({r.agent_result.num_turns}t, {tokens:,} tok)")

    # Save results
    output_path = args.output or Path(f"results-{int(time.time())}.json")
    output_data = {
        "model": config.model,
        "max_turns": config.max_turns,
        "total_tasks": total,
        "passed": passed,
        "accuracy": passed / total if total > 0 else 0,
        "wall_time_sec": elapsed,
        "tasks": [
            {
                "task_id": r.task_id,
                "passed": r.passed,
                "turns": r.agent_result.num_turns,
                "input_tokens": r.agent_result.total_input_tokens,
                "output_tokens": r.agent_result.total_output_tokens,
                "wall_time_sec": r.agent_result.wall_time_sec,
                "error": r.error,
            }
            for r in results
        ],
    }
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
