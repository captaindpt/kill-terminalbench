# Task Buckets

This is an operational classification for planning batch runs. It is not meant to replace the benchmark's own per-task metadata. The goal is to group the 89-task space into failure-mode buckets that are useful for iterative evaluation.

## Bucket Model

### 1. Environment And Dependency Repair

- Typical failure mode:
  - wrong package version
  - missing package
  - broken runtime setup
- Representative tasks:
  - `fix-permissions`
  - `fix-pandas-version`
  - `npm-conflict-resolution`

### 2. Data Transformation And Validation

- Typical failure mode:
  - wrong output schema
  - parsing edge cases
  - silent data-loss or formatting mistakes
- Representative tasks:
  - `csv-to-parquet`
  - `heterogeneous-dates`
  - `jsonl-aggregator`

### 3. Git, Branching, And Deployment Workflows

- Typical failure mode:
  - partial Git setup
  - missed hook or branch mapping
  - deployment path not connected to source control events
- Representative tasks:
  - `git-multibranch`
  - `fix-git`
  - `configure-git-webserver`

### 4. System Administration And Web Services

- Typical failure mode:
  - service boots but config is wrong
  - file location mismatch
  - logs, ports, TLS, or process control not verifier-clean
- Representative tasks:
  - `nginx-request-logging`
  - `openssl-selfsigned-cert`
  - `home-server-https`

### 5. Debugging And Code Repair

- Typical failure mode:
  - patch fixes symptom but not root cause
  - tests partly pass
  - hidden regression or missed edge case
- Representative tasks:
  - `broken-python`
  - `classifier-debug`
  - `mnist-learning-fix`

### 6. Build, Compile, And Toolchain Constraints

- Typical failure mode:
  - compiler/build command works but violates task constraint
  - artifact hygiene mistakes
  - platform/toolchain assumptions break verifier
- Representative tasks:
  - `build-cython-ext`
  - `polyglot-c-py`
  - `cpp-compatibility`

### 7. Security And Vulnerability Work

- Typical failure mode:
  - exploit or patch incomplete
  - verifier requires precise state change
  - subtle security condition left unmet
- Representative tasks:
  - `fix-code-vulnerability`
  - `vulnerable-secret`
  - `sql-injection-attack`

### 8. Algorithmic, Search, And Quantitative Reasoning

- Typical failure mode:
  - logically wrong output
  - solver heuristic stalls
  - correct-looking intermediate work but wrong final answer
- Representative tasks:
  - `solve-sudoku`
  - `gomoku-planner`
  - `countdown-game`

## Recommended Cross-Bucket Batch

Name: `tb2-buckets-24`

Purpose:
- sample every major operational bucket
- expose different failure modes in one run
- keep the batch large enough to be meaningful without jumping straight to all 89 tasks

Tasks:
- `fix-permissions`
- `fix-pandas-version`
- `npm-conflict-resolution`
- `csv-to-parquet`
- `heterogeneous-dates`
- `jsonl-aggregator`
- `git-multibranch`
- `fix-git`
- `configure-git-webserver`
- `nginx-request-logging`
- `openssl-selfsigned-cert`
- `home-server-https`
- `broken-python`
- `classifier-debug`
- `mnist-learning-fix`
- `build-cython-ext`
- `polyglot-c-py`
- `cpp-compatibility`
- `fix-code-vulnerability`
- `vulnerable-secret`
- `sql-injection-attack`
- `solve-sudoku`
- `gomoku-planner`
- `countdown-game`

Rationale:
- repeats one known miss:
  - `polyglot-c-py`
- repeats several known passes:
  - `git-multibranch`
  - `nginx-request-logging`
  - `openssl-selfsigned-cert`
- adds new tasks from each bucket so we learn whether failures cluster by:
  - environment repair
  - service setup
  - debugging
  - security
  - algorithmic reasoning

Run command:
- `python3 -m ktb.cli --runner harbor --task-set tb2-buckets-24 --n-concurrent 1`

## Interpretation Rule

When this batch runs, review results by bucket, not just overall score. The first question should be:

- which bucket failed most often?

The second question should be:

- did the failures cluster by one failure mode, such as environment hygiene, artifact cleanup, or long-horizon reasoning?
