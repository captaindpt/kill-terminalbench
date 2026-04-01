# Failure Ledger

This file records every observed benchmark or benchmark-blocking failure so far.

## Infra and Launch Blockers

### 2026-03-31: `git pull origin main` blocked by GitHub auth

- Context: x86_64 benchmark machine pre-run setup
- Failure class: repo access
- Exact blocker:
  - HTTPS remote initially failed due to missing credentials
  - SSH remote then failed on host trust, then on missing accepted public key
- Resolution:
  - GitHub host key added to `known_hosts`
  - working SSH access restored
  - final pull result was `Already up to date.`

### 2026-03-31: runtime dependencies missing for `python3 -m ktb.cli`

- Context: x86_64 benchmark machine pre-run setup
- Failure class: local Python environment
- Exact blocker:
  - `ModuleNotFoundError: No module named 'anthropic'`
- Resolution:
  - installed declared runtime dependencies
  - installed Harbor locally

### 2026-03-31: editable install path broken

- Context: x86_64 benchmark machine pre-run setup
- Failure class: packaging metadata
- Exact blocker:
  - setuptools refused editable install because multiple top-level packages were auto-discovered
- Impact:
  - this blocked `pip install -e .`
- Workaround used:
  - installed direct runtime dependencies instead of relying on editable install

### 2026-03-31: Harbor binary path mismatch

- Context: x86_64 benchmark machine pre-run setup
- Failure class: local tool path
- Exact blocker:
  - [ktb/harbor_runner.py](/root/kill-terminalbench/ktb/harbor_runner.py#L28) expects `.venv/bin/harbor`
  - Harbor was not initially present there
- Resolution:
  - Harbor installed locally and expected path satisfied

### 2026-03-31: Docker unavailable to Harbor

- Context: x86_64 benchmark machine pre-run setup
- Failure class: container runtime
- Exact blockers, in order:
  - Docker not installed / not on `PATH`
  - Docker daemon not running
  - `agent` user lacked Docker socket access
  - `docker compose` unavailable
- Final resolution:
  - Docker daemon running
  - `agent` user could run `docker info`
  - `docker compose version` returned `v5.1.1`

## Debug and Benchmark Run Failures

### 2026-03-31: Harbor smoke timeout on `adaptive-rejection-sampler`

- Run: [/root/kill-terminalbench/jobs/2026-03-31__13-58-56](/root/kill-terminalbench/jobs/2026-03-31__13-58-56)
- Scope: 1-task debug run
- Failure class: command timeout / long-horizon execution
- Artifact:
  - [/root/kill-terminalbench/jobs/2026-03-31__13-58-56/adaptive-rejection-sampler__MNUQjuc/exception.txt](/root/kill-terminalbench/jobs/2026-03-31__13-58-56/adaptive-rejection-sampler__MNUQjuc/exception.txt)
- Exact blocker:
  - Harbor environment exec path raised `RuntimeError: Command timed out after 300 seconds`
- Notes:
  - this happened on the ARM development machine, not the x86_64 benchmark host

### 2026-03-31: accidental full-dataset launch from `--task-set`

- Run: [/root/kill-terminalbench/jobs/2026-03-31__14-11-50](/root/kill-terminalbench/jobs/2026-03-31__14-11-50)
- Scope: debug run, unintentionally started as 89-task dataset run
- Failure class: CLI task-filter bug
- Exact blocker:
  - CLI passed the wrong task list into Harbor
  - first incorrect task observed was `gpt2-codegolf`
  - run was intentionally aborted
- Artifact:
  - [/root/kill-terminalbench/jobs/2026-03-31__14-11-50/result.json](/root/kill-terminalbench/jobs/2026-03-31__14-11-50/result.json)
- Resolution:
  - task-set handoff fixed in `ktb/cli.py`

### 2026-03-31: `break-filter-js-from-html` debug run cancelled after infra investigation

- Run: [/root/kill-terminalbench/jobs/2026-03-31__14-12-46](/root/kill-terminalbench/jobs/2026-03-31__14-12-46)
- Scope: 15-task debug slice
- Failure class: environment incompatibility on ARM dev host
- Artifacts:
  - [/root/kill-terminalbench/jobs/2026-03-31__14-12-46/result.json](/root/kill-terminalbench/jobs/2026-03-31__14-12-46/result.json)
  - [/root/kill-terminalbench/jobs/2026-03-31__14-12-46/break-filter-js-from-html__3jb4wK7/trial.log](/root/kill-terminalbench/jobs/2026-03-31__14-12-46/break-filter-js-from-html__3jb4wK7/trial.log)
- Exact blocker:
  - browser stack under ARM/qemu emulation was not trustworthy for this task
  - prior investigation recorded Chromium/Selenium startup incompatibility rather than a clean agent failure
- Notes:
  - this run was treated as harness-debug evidence, not benchmark evidence

### 2026-03-31: x86_64 Harbor run failed before trial start due to missing Compose support

- Run: [/root/kill-terminalbench/jobs/2026-03-31__19-53-42](/root/kill-terminalbench/jobs/2026-03-31__19-53-42)
- Scope: 5-task debug batch on x86_64
- Failure class: machine-level Docker Compose mismatch
- Affected tasks:
  - `git-multibranch`
  - `polyglot-c-py`
  - `nginx-request-logging`
  - `sqlite-db-truncate`
  - `openssl-selfsigned-cert`
- Artifacts:
  - [/root/kill-terminalbench/jobs/2026-03-31__19-53-42/result.json](/root/kill-terminalbench/jobs/2026-03-31__19-53-42/result.json)
  - task-level `exception.txt` files under the same job
- Exact blocker:
  - Harbor invoked `docker compose --project-name ...`
  - machine returned `unknown flag: --project-name`
  - later verified that `docker compose` itself was unavailable at that point
- Resolution:
  - Docker Compose support fixed on the benchmark machine

### 2026-03-31: official x86_64 debug subset scored `0.800` with one task failure

- Run: [/root/kill-terminalbench/jobs/2026-03-31__19-56-14](/root/kill-terminalbench/jobs/2026-03-31__19-56-14)
- Scope: 5-task debug batch on x86_64
- Result:
  - 5 trials
  - 4 passes
  - 1 fail
  - 0 runtime errors
- Failed task:
  - `polyglot-c-py`
- Artifact trail:
  - [/root/kill-terminalbench/jobs/2026-03-31__19-56-14/polyglot-c-py__QUr7czP/result.json](/root/kill-terminalbench/jobs/2026-03-31__19-56-14/polyglot-c-py__QUr7czP/result.json)
  - [/root/kill-terminalbench/jobs/2026-03-31__19-56-14/polyglot-c-py__QUr7czP/verifier/test-stdout.txt](/root/kill-terminalbench/jobs/2026-03-31__19-56-14/polyglot-c-py__QUr7czP/verifier/test-stdout.txt)
  - [/root/kill-terminalbench/jobs/2026-03-31__19-56-14/polyglot-c-py__QUr7czP/verifier/ctrf.json](/root/kill-terminalbench/jobs/2026-03-31__19-56-14/polyglot-c-py__QUr7czP/verifier/ctrf.json)
- Exact blocker:
  - verifier expected only `main.py.c` in `/app/polyglot`
  - agent left compiled binary `cmain` behind
  - task failed on a single-file constraint, not on Fibonacci correctness

## Current Failure Themes

- Environment readiness still matters:
  - Docker
  - Docker Compose
  - benchmark-user permissions
  - repo access
- We have at least one demonstrated process-hygiene miss:
  - leaving output artifacts that violate task constraints
- We have one demonstrated long-horizon cost/turn risk:
  - `git-multibranch` used the full 75-episode budget in the successful debug batch
