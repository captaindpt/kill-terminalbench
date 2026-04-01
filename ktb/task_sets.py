"""Named task sets for repeatable benchmark slices."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskSet:
    name: str
    description: str
    tasks: tuple[str, ...]


TB2_DIVERSE_15 = TaskSet(
    name="tb2-diverse-15",
    description=(
        "Fifteen official TB2 tasks selected to cover a broad range of"
        " categories and failure modes without leaning too heavily on one"
        " domain."
    ),
    tasks=(
        "break-filter-js-from-html",
        "build-cython-ext",
        "code-from-image",
        "configure-git-webserver",
        "count-dataset-tokens",
        "db-wal-recovery",
        "financial-document-processor",
        "git-multibranch",
        "large-scale-text-editing",
        "nginx-request-logging",
        "openssl-selfsigned-cert",
        "polyglot-c-py",
        "qemu-alpine-ssh",
        "raman-fitting",
        "sqlite-db-truncate",
    ),
)

TB2_BUCKETS_24 = TaskSet(
    name="tb2-buckets-24",
    description=(
        "Twenty-four official TB2 tasks selected as a cross-bucket diagnostic"
        " run: three representative tasks from each operational bucket."
    ),
    tasks=(
        "fix-permissions",
        "fix-pandas-version",
        "npm-conflict-resolution",
        "csv-to-parquet",
        "heterogeneous-dates",
        "jsonl-aggregator",
        "git-multibranch",
        "fix-git",
        "configure-git-webserver",
        "nginx-request-logging",
        "openssl-selfsigned-cert",
        "home-server-https",
        "broken-python",
        "classifier-debug",
        "mnist-learning-fix",
        "build-cython-ext",
        "polyglot-c-py",
        "cpp-compatibility",
        "fix-code-vulnerability",
        "vulnerable-secret",
        "sql-injection-attack",
        "solve-sudoku",
        "gomoku-planner",
        "countdown-game",
    ),
)


TASK_SETS: dict[str, TaskSet] = {
    TB2_DIVERSE_15.name: TB2_DIVERSE_15,
    TB2_BUCKETS_24.name: TB2_BUCKETS_24,
}


def get_task_set(name: str) -> TaskSet:
    try:
        return TASK_SETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(TASK_SETS))
        raise ValueError(f"Unknown task set '{name}'. Available: {available}") from exc
