# Runs

## Official Score Status

- Current official TB2 full-bench progress: `0/89`
- Current official TB2 full-bench status: not started
- Rule: only a Harbor run against the full `terminal-bench@2.0` dataset counts here

## Named Debug Task Sets

### `tb2-diverse-15`

- Purpose: fast diagnostic slice before the full 89-task Harbor run
- Source: official `terminal-bench@2.0` dataset only
- Size: `15`
- Selection goals:
  - span multiple TB2 categories
  - expose likely agent weaknesses across shell use, debugging, data handling, security, and systems work
  - avoid over-indexing on the longest verifier-heavy tasks
- Tasks:
  - `break-filter-js-from-html`
  - `build-cython-ext`
  - `code-from-image`
  - `configure-git-webserver`
  - `count-dataset-tokens`
  - `db-wal-recovery`
  - `financial-document-processor`
  - `git-multibranch`
  - `large-scale-text-editing`
  - `nginx-request-logging`
  - `openssl-selfsigned-cert`
  - `polyglot-c-py`
  - `qemu-alpine-ssh`
  - `raman-fitting`
  - `sqlite-db-truncate`
- Run command:
  - `python3 -m ktb.cli --runner harbor --task-set tb2-diverse-15 --n-concurrent 1`

### `tb2-buckets-24`

- Purpose: cross-bucket diagnostic batch for iterative benchmarking
- Source: official `terminal-bench@2.0` dataset only
- Size: `24`
- Selection goals:
  - choose three representative tasks from each operational bucket
  - measure whether failures cluster by bucket rather than by individual task
  - rerun one known x86_64 miss (`polyglot-c-py`) alongside known passes and fresh tasks
- Tasks:
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
- Run command:
  - `python3 -m ktb.cli --runner harbor --task-set tb2-buckets-24 --n-concurrent 1`

## Debug Runs

### Official Local TB Harness Smoke

- Path: `runs/2026-03-31__13-43-35`
- Mode: local Terminal-Bench harness
- Task: `hello-world`
- Result: pass

- This run used the official local Terminal-Bench harness path, not Harbor.
- It was useful to validate:
  - Docker SDK access
  - compose path
  - task container lifecycle
  - local parser/test flow

- Episodes: `3`
- Input tokens: `2494`
- Output tokens: `145`
- Cost: `$0.016095`

### Local TB Subset Run

- Path: `runs/2026-03-31__13-44-56`
- Mode: local Terminal-Bench harness
- Purpose: debugging subset, not public-score comparable

- At least the following task directories exist:
  - `nginx-request-logging`
  - `polyglot-c-py`

- `nginx-request-logging` produced detailed command/session artifacts and appears to have made concrete progress.

### Harbor TB2 Smoke

- Path: `jobs/2026-03-31__13-58-56`
- Mode: Harbor
- Dataset: `terminal-bench@2.0`
- Task: `adaptive-rejection-sampler`
- Purpose: validate Harbor + TB2 + custom agent import path
- Classification: debug run, not official full-bench progress

- Task source repo: `https://github.com/laude-institute/terminal-bench-2.git`
- Task commit: `69671fbaac6d67a7ef0dfec016cc38a64ef7a77c`
- Agent import path: `ktb.harbor_agent:OpenRouterHarborAgent`
- Model: `anthropic/claude-opus-4.6`

- `job.log`
- `trial.log`
- `config.json`
- `agent/episodes/episode-0/request.json`
- `agent/episodes/episode-0/response.json`
- `agent/episodes/episode-0/tool-results.json`
- additional episode artifacts as the run progresses
- Current observed state:
  - only one task directory exists under the job
  - the active Harbor command includes `--include-task-name adaptive-rejection-sampler`
  - this means the run scope is `1/1`, not `89/89`

## Official Runs

No official Harbor full-dataset TB2 run has been launched yet.

## Latest Debug Run

### Harbor TB2 Diverse Subset

- Path: `jobs/2026-03-31__14-12-46`
- Mode: Harbor
- Dataset: `terminal-bench@2.0`
- Task set: `tb2-diverse-15`
- Status: stopped after task 1 investigation
- Concurrency: `1`
- First observed task: `break-filter-js-from-html`
- Run command:
  - `python3 -m ktb.cli --runner harbor --task-set tb2-diverse-15 --n-concurrent 1`
- Outcome:
  - did not progress past task 1
  - task exposed an ARM/qemu browser incompatibility rather than a trustworthy benchmark failure
  - run was stopped so the harness could be patched before the x86_64 rerun
- Key blocker from task logs:
  - Chromium inside the task image reports missing `sse3` support under emulation
  - Selenium then fails with `SessionNotCreatedException`
- Follow-up harness changes made after this run:
  - fail-fast infra blocker detection
  - model-call timeout/retry limits
  - output persistence with reread paths
  - message compaction

### Aborted Run Record

- Path: `jobs/2026-03-31__14-11-50`
- Status: aborted intentionally
- Reason: CLI bug caused `--task-set tb2-diverse-15` to start an unfiltered full-dataset Harbor run
- First observed incorrect task: `gpt2-codegolf`
- Fix applied in [ktb/cli.py](/Users/manirashahmadi/ccode/kill-terminalbench/ktb/cli.py): Harbor now receives the resolved `task_ids` list rather than raw `args.tasks`
