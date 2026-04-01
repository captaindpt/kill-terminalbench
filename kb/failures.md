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

## 2026-04-01: `tb2-diverse-15` rerun on patched Harbor harness

- Run: [/root/kill-terminalbench/jobs/2026-04-01__15-01-02](/root/kill-terminalbench/jobs/2026-04-01__15-01-02)
- Scope: 15-task official-TB2 debug slice on x86_64 after:
  - Harbor prompt fixes
  - Sonnet compaction
  - high compaction threshold
  - compaction cooldown
  - anti-speculation summary rules
  - explicit timeout notes

### Notable Successes

- `break-filter-js-from-html`
  - flipped from prior fail to pass
  - finished with `0` compactions
- `polyglot-c-py`
  - flipped from prior fail to pass
  - no stray artifact failure on this run
- `build-cython-ext`
  - flipped from prior fail to pass
  - passed despite still needing `6` compactions
- `git-multibranch`
  - passed in `21` episodes with `0` compactions

### Failure: `configure-git-webserver`

- Artifact:
  - [/root/kill-terminalbench/jobs/2026-04-01__15-01-02/configure-git-webserver__qurewzg/verifier/test-stdout.txt](/root/kill-terminalbench/jobs/2026-04-01__15-01-02/configure-git-webserver__qurewzg/verifier/test-stdout.txt)
- Failure class: task correctness
- Exact blocker:
  - verifier reached the web server but got HTTP `404`
- Interpretation:
  - execution-model guidance helped relative to earlier HTTP `000`
  - the remaining miss is content/deployment correctness, not service availability

### Failure: `openssl-selfsigned-cert`

- Artifact:
  - [/root/kill-terminalbench/jobs/2026-04-01__15-01-02/openssl-selfsigned-cert__2vkktKA/verifier/test-stdout.txt](/root/kill-terminalbench/jobs/2026-04-01__15-01-02/openssl-selfsigned-cert__2vkktKA/verifier/test-stdout.txt)
- Failure class: dependency completeness
- Exact blocker:
  - `/app/check_cert.py` existed but failed with `ModuleNotFoundError: No module named 'cryptography'`
- Interpretation:
  - output files were mostly present
  - the agent missed a required Python runtime dependency for the verification script

### Failure: `raman-fitting`

- Artifacts:
  - [/root/kill-terminalbench/jobs/2026-04-01__15-01-02/raman-fitting__fYpnnSa/result.json](/root/kill-terminalbench/jobs/2026-04-01__15-01-02/raman-fitting__fYpnnSa/result.json)
  - [/root/kill-terminalbench/jobs/2026-04-01__15-01-02/raman-fitting__fYpnnSa/verifier/test-stdout.txt](/root/kill-terminalbench/jobs/2026-04-01__15-01-02/raman-fitting__fYpnnSa/verifier/test-stdout.txt)
- Failure class: timeout / incomplete deliverable
- Exact blockers:
  - Harbor recorded `AgentTimeoutError: Agent execution timed out after 900.0 seconds`
  - verifier found `/app/results.json` missing
- Interpretation:
  - this is still a long-horizon failure, not a harness-crash failure

### Failure: `db-wal-recovery`

- Artifact:
  - [/root/kill-terminalbench/jobs/2026-04-01__15-01-02/db-wal-recovery__Epu9ntv/result.json](/root/kill-terminalbench/jobs/2026-04-01__15-01-02/db-wal-recovery__Epu9ntv/result.json)
- Failure class: per-command timeout
- Exact blocker:
  - Harbor raised `RuntimeError: Command timed out after 300 seconds`
  - verifier did not run
- Interpretation:
  - improved compaction policy removed the compaction storm
  - remaining issue is a long single command inside the agent loop

### Failure: `qemu-alpine-ssh`

- Artifact:
  - [/root/kill-terminalbench/jobs/2026-04-01__15-01-02/qemu-alpine-ssh__P2wegmN/result.json](/root/kill-terminalbench/jobs/2026-04-01__15-01-02/qemu-alpine-ssh__P2wegmN/result.json)
- Failure class: per-command timeout
- Exact blocker:
  - Harbor raised `RuntimeError: Command timed out after 300 seconds`
  - verifier did not run
- Interpretation:
  - another case where explicit timeout notes are relevant, but the command still overran the 300s ceiling
