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

TB2_NEXT_25_RETRY_N2_HARDER = TaskSet(
    name="tb2-next-25-retry-n2-harder",
    description=(
        "Reordered n=2 retry slice for harder-task debugging after the"
        " initial front pair. Starts with three previously successful but"
        " trusted anchor tasks, then prioritizes harder or still-unstable"
        " tasks from the current 25-task slice. `gpt2-codegolf` and"
        " `llm-inference-batching-scheduler` are moved out of the front"
        " position so the next rerun can probe broader failure modes first."
    ),
    tasks=(
        "fix-git",
        "count-dataset-tokens",
        "nginx-request-logging",
        "adaptive-rejection-sampler",
        "write-compressor",
        "mteb-retrieve",
        "gcode-to-text",
        "regex-chess",
        "cobol-modernization",
        "custom-memory-heap-crash",
        "compile-compcert",
        "reshard-c4-data",
        "pytorch-model-cli",
        "portfolio-optimization",
        "query-optimize",
        "qemu-startup",
        "chess-best-move",
        "polyglot-rust-c",
        "crack-7z-hash",
        "hf-model-inference",
        "modernize-scientific-stack",
        "pypi-server",
        "headless-terminal",
        "multi-source-data-merger",
        "password-recovery",
    ),
)

TB2_ANCHORS_PLUS_5 = TaskSet(
    name="tb2-anchors-plus-5",
    description=(
        "Small 8-task debug batch: three trusted anchor tasks first, then"
        " five medium/hard unresolved tasks for faster iteration without"
        " Harbor reordering a large queue into unhelpful front pairs."
    ),
    tasks=(
        "fix-git",
        "count-dataset-tokens",
        "nginx-request-logging",
        "adaptive-rejection-sampler",
        "write-compressor",
        "mteb-retrieve",
        "regex-chess",
        "reshard-c4-data",
    ),
)


# ---------------------------------------------------------------------------
# Full 89-task TB2 coverage: batches 1-5
# 8 + 24 + 25 + 25 + 7 = 89, no overlaps, no gaps.
# ---------------------------------------------------------------------------

TB2_BATCH_1 = TaskSet(
    name="tb2-batch-1",
    description="Canary batch: 8 historically reliable (100% pass rate) tasks.",
    tasks=(
        "fix-git",
        "count-dataset-tokens",
        "nginx-request-logging",
        "code-from-image",
        "fix-code-vulnerability",
        "headless-terminal",
        "multi-source-data-merger",
        "log-summary-date-ranges",
    ),
)

TB2_BATCH_2 = TaskSet(
    name="tb2-batch-2",
    description="24 previously-passed tasks at varying consistency.",
    tasks=(
        "break-filter-js-from-html",
        "build-cython-ext",
        "chess-best-move",
        "configure-git-webserver",
        "crack-7z-hash",
        "financial-document-processor",
        "git-multibranch",
        "hf-model-inference",
        "large-scale-text-editing",
        "llm-inference-batching-scheduler",
        "modernize-scientific-stack",
        "openssl-selfsigned-cert",
        "password-recovery",
        "polyglot-c-py",
        "polyglot-rust-c",
        "portfolio-optimization",
        "pypi-server",
        "pytorch-model-cli",
        "qemu-alpine-ssh",
        "qemu-startup",
        "query-optimize",
        "reshard-c4-data",
        "sqlite-db-truncate",
        "vulnerable-secret",
    ),
)

TB2_BATCH_3 = TaskSet(
    name="tb2-batch-3",
    description=(
        "11 never-passed retries (with 700s timeout) + 14 fresh unattempted tasks."
    ),
    tasks=(
        # Retries — never passed in any prior run
        "adaptive-rejection-sampler",
        "cobol-modernization",
        "compile-compcert",
        "custom-memory-heap-crash",
        "db-wal-recovery",
        "gcode-to-text",
        "gpt2-codegolf",
        "mteb-retrieve",
        "raman-fitting",
        "regex-chess",
        "write-compressor",
        # Fresh — never attempted
        "bn-fit-modify",
        "build-pmars",
        "build-pov-ray",
        "caffe-cifar-10",
        "cancel-async-tasks",
        "circuit-fibsqrt",
        "constraints-scheduling",
        "distribution-search",
        "dna-assembly",
        "dna-insert",
        "extract-elf",
        "extract-moves-from-video",
        "feal-differential-cryptanalysis",
        "feal-linear-cryptanalysis",
    ),
)

TB2_BATCH_4 = TaskSet(
    name="tb2-batch-4",
    description="25 fresh unattempted TB2 tasks.",
    tasks=(
        "filter-js-from-html",
        "fix-ocaml-gc",
        "git-leak-recovery",
        "install-windows-3.11",
        "kv-store-grpc",
        "largest-eigenval",
        "mailman",
        "make-doom-for-mips",
        "make-mips-interpreter",
        "mcmc-sampling-stan",
        "merge-diff-arc-agi-task",
        "model-extraction-relu-logits",
        "mteb-leaderboard",
        "overfull-hbox",
        "path-tracing",
        "path-tracing-reverse",
        "protein-assembly",
        "prove-plus-comm",
        "pytorch-model-recovery",
        "regex-log",
        "rstan-to-pystan",
        "sam-cell-seg",
        "sanitize-git-repo",
        "schemelike-metacircular-eval",
        "sparql-university",
    ),
)

TB2_BATCH_5 = TaskSet(
    name="tb2-batch-5",
    description="Final 7 unattempted TB2 tasks to complete full 89-task coverage.",
    tasks=(
        "sqlite-with-gcov",
        "torch-pipeline-parallelism",
        "torch-tensor-parallelism",
        "train-fasttext",
        "tune-mjcf",
        "video-processing",
        "winning-avg-corewars",
    ),
)

TASK_SETS: dict[str, TaskSet] = {
    TB2_DIVERSE_15.name: TB2_DIVERSE_15,
    TB2_BUCKETS_24.name: TB2_BUCKETS_24,
    TB2_CROSS_SECTION_30.name: TB2_CROSS_SECTION_30,
    TB2_NEXT_25.name: TB2_NEXT_25,
    TB2_NEXT_25_RETRY_N2.name: TB2_NEXT_25_RETRY_N2,
    TB2_NEXT_25_RETRY_N2_HARDER.name: TB2_NEXT_25_RETRY_N2_HARDER,
    TB2_ANCHORS_PLUS_5.name: TB2_ANCHORS_PLUS_5,
    TB2_BATCH_1.name: TB2_BATCH_1,
    TB2_BATCH_2.name: TB2_BATCH_2,
    TB2_BATCH_3.name: TB2_BATCH_3,
    TB2_BATCH_4.name: TB2_BATCH_4,
    TB2_BATCH_5.name: TB2_BATCH_5,
}


def get_task_set(name: str) -> TaskSet:
    try:
        return TASK_SETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(TASK_SETS))
        raise ValueError(f"Unknown task set '{name}'. Available: {available}") from exc
