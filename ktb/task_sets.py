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

TB2_CROSS_SECTION_30 = TaskSet(
    name="tb2-cross-section-30",
    description=(
        "Thirty official TB2 tasks chosen as a broader cross-section run:"
        " the full diverse-15 slice plus fifteen additional bucket tasks to"
        " increase category coverage without jumping straight to all 89."
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
        "fix-permissions",
        "fix-pandas-version",
        "npm-conflict-resolution",
        "csv-to-parquet",
        "heterogeneous-dates",
        "jsonl-aggregator",
        "fix-git",
        "home-server-https",
        "broken-python",
        "classifier-debug",
        "mnist-learning-fix",
        "cpp-compatibility",
        "fix-code-vulnerability",
        "vulnerable-secret",
        "sql-injection-attack",
    ),
)

TB2_NEXT_25 = TaskSet(
    name="tb2-next-25",
    description=(
        "Twenty-five official TB2 tasks not yet exercised in the current"
        " debugging cycle, chosen to extend coverage without repeating the"
        " previously run slices."
    ),
    tasks=(
        "gpt2-codegolf",
        "llm-inference-batching-scheduler",
        "reshard-c4-data",
        "write-compressor",
        "log-summary-date-ranges",
        "pytorch-model-cli",
        "password-recovery",
        "portfolio-optimization",
        "regex-chess",
        "modernize-scientific-stack",
        "mteb-retrieve",
        "pypi-server",
        "custom-memory-heap-crash",
        "adaptive-rejection-sampler",
        "multi-source-data-merger",
        "crack-7z-hash",
        "chess-best-move",
        "cobol-modernization",
        "polyglot-rust-c",
        "hf-model-inference",
        "compile-compcert",
        "headless-terminal",
        "qemu-startup",
        "gcode-to-text",
        "query-optimize",
    ),
)

TB2_NEXT_25_RETRY_N2 = TaskSet(
    name="tb2-next-25-retry-n2",
    description=(
        "Reordered retry of the tb2-next-25 slice for n=2 runs: prior"
        " scored fails and timeout/setup failures first, prior passes moved"
        " to the end so new harness changes are exercised against the hard"
        " cases as early as possible."
    ),
    tasks=(
        "adaptive-rejection-sampler",
        "gpt2-codegolf",
        "write-compressor",
        "mteb-retrieve",
        "chess-best-move",
        "pytorch-model-cli",
        "regex-chess",
        "cobol-modernization",
        "custom-memory-heap-crash",
        "portfolio-optimization",
        "reshard-c4-data",
        "gcode-to-text",
        "compile-compcert",
        "qemu-startup",
        "query-optimize",
        "llm-inference-batching-scheduler",
        "polyglot-rust-c",
        "crack-7z-hash",
        "hf-model-inference",
        "modernize-scientific-stack",
        "pypi-server",
        "headless-terminal",
        "log-summary-date-ranges",
        "multi-source-data-merger",
        "password-recovery",
    ),
)


TASK_SETS: dict[str, TaskSet] = {
    TB2_DIVERSE_15.name: TB2_DIVERSE_15,
    TB2_BUCKETS_24.name: TB2_BUCKETS_24,
    TB2_CROSS_SECTION_30.name: TB2_CROSS_SECTION_30,
    TB2_NEXT_25.name: TB2_NEXT_25,
    TB2_NEXT_25_RETRY_N2.name: TB2_NEXT_25_RETRY_N2,
}


def get_task_set(name: str) -> TaskSet:
    try:
        return TASK_SETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(TASK_SETS))
        raise ValueError(f"Unknown task set '{name}'. Available: {available}") from exc
