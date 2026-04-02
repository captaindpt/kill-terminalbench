# Run Status and Task Triage

Last updated: 2026-04-02 ~02:30 UTC

## Summary

- TB2 total tasks: 241
- Attempted so far: 43
- Passed at least once: 32
- Never passed (scored fail): 4
- Never scored (errors/timeouts only): 7
- Not yet attempted: 198

## Current Harness Version

Commit `1ccb471` — thinking budget enabled, verification gate removed (soft prompt instead), compaction at 100K tokens / 20 turns / 50 messages, structured failure reflection, parallel bash hint.

## Task Classification

### A. Reliable (>=75% pass rate, 3+ attempts)

- code-from-image (3/3)
- fix-code-vulnerability (3/3)
- fix-git (4/5)
- log-summary-date-ranges (5/6)
- nginx-request-logging (5/7)
- multi-source-data-merger (3/4)
- financial-document-processor (2/2)
- large-scale-text-editing (2/2)
- headless-terminal (3/4)

### B. Moderate (25-74% pass rate)

- llm-inference-batching-scheduler (4/8)
- git-multibranch (4/7)
- openssl-selfsigned-cert (3/5)
- break-filter-js-from-html (3/7)
- reshard-c4-data (3/7)
- chess-best-move (2/4)
- portfolio-optimization (2/4)
- count-dataset-tokens (2/5)
- password-recovery (2/4)
- sqlite-db-truncate (2/3)
- pypi-server (2/4)
- modernize-scientific-stack (2/5)
- hf-model-inference (2/5)

### C. Fragile (<25% pass rate, has passed once)

- configure-git-webserver (1/7)
- build-cython-ext (1/3)
- crack-7z-hash (1/4)
- polyglot-c-py (1/4)
- polyglot-rust-c (1/3)
- pytorch-model-cli (1/4)
- qemu-alpine-ssh (1/2)
- qemu-startup (1/4)
- query-optimize (1/3)
- vulnerable-secret (1/1)

### D. Never Passed (scored 0.0)

- gcode-to-text (0/3)
- raman-fitting (0/2)
- regex-chess (0/5)
- write-compressor (0/6)

### E. Never Scored (errors/timeouts/unscored only)

- adaptive-rejection-sampler (0/5 — RuntimeErrors)
- cobol-modernization (0/4 — all unscored)
- compile-compcert (0/4 — all unscored)
- custom-memory-heap-crash (0/4 — all unscored)
- db-wal-recovery (0/5 — mix of fail and unscored)
- gpt2-codegolf (0/9 — mostly fails + unscored)
- mteb-retrieve (0/5 — mostly unscored)

### F. Not Yet Attempted (198 tasks)

These are the remaining TB2 tasks. Run in batches after stabilizing A-E.

## Batch Run Log

### Batch 1 (canary) — job 2026-04-02__02-07-04
- 7/8 passed
- Failed: count-dataset-tokens (wrong tokenization: 79566 vs 79586)
- Harness: clean, no blunders, thinking active on ep 0

### Batch 2 (complete) — job 2026-04-02__02-21-26
- 18/21 scored pass = 85.7%, 3 errors (unscored)
- 8 pass, 3 fail, 3 error

Passes: break-filter-js-from-html, chess-best-move, financial-document-processor, hf-model-inference, large-scale-text-editing, modernize-scientific-stack, openssl-selfsigned-cert, polyglot-c-py

Errors (all timeout/infra — not harness bugs):
- crack-7z-hash: John the Ripper brute force exceeded 300s command timeout
- password-recovery: forensic binary analysis (dd/strings over .bin files) exceeded 300s command timeout
- llm-inference-batching-scheduler: Docker container died during setup (ProcessLookupError on mkdir)
- Action: bump command_timeout to 600 would likely save crack-7z-hash and password-recovery

Fails (genuine task failures):
- configure-git-webserver (1/8 lifetime): verifier curl gets HTTP 404. Model sets up nginx, tests locally, works — but verifier hits a different URL path. Likely document root or location block mismatch with what verifier expects. Persistent regression.
- git-multibranch: verifier uses expect script (git_push.exp) for password-based SSH push. Error: "spawn id exp3 not open" — expect session dies. Model tested with sshpass which has different behavior. Subtle compat between model's test method and verifier's.
- build-cython-ext: 10/11 verifier tests passed. Sole failure: test_ccomplexity hits numpy 2.x AttributeError in ccomplexity.pyx. Model fixed np.float/np.int everywhere but missed a remaining compat issue in this specific Cython file. Very close — 34 episodes of solid work.

### Batch 3 (complete) — job 2026-04-02__03-57-51
- 7/25 passed = 28%, command_timeout=700

Passes: cancel-async-tasks, circuit-fibsqrt, compile-compcert, constraints-scheduling, custom-memory-heap-crash, distribution-search, feal-differential-cryptanalysis

Agent timeout (900s wall clock — Harbor limit, not ours):
- adaptive-rejection-sampler, db-wal-recovery, extract-moves-from-video, gcode-to-text, gpt2-codegolf, raman-fitting, write-compressor

Command timeout (700s per-command):
- build-pov-ray, caffe-cifar-10

Container died (ProcessLookupError — Docker contention at n=2):
- cobol-modernization

API/JSON error:
- regex-chess (OpenRouter returned garbage JSON)

Verifier fails (model got wrong answer):
- bn-fit-modify, build-pmars, dna-assembly, dna-insert, extract-elf, feal-linear-cryptanalysis, mteb-retrieve

### Batch 4 (complete) — job 2026-04-02__06-56-25
- 9/25 passed = 36%, command_timeout=700

Passes: kv-store-grpc, largest-eigenval, mailman, make-mips-interpreter, mcmc-sampling-stan, overfull-hbox, prove-plus-comm, sanitize-git-repo, sparql-university

Agent timeout (900s/1800s wall clock):
- make-doom-for-mips, path-tracing, path-tracing-reverse

Command timeout (700s per-command):
- model-extraction-relu-logits, sam-cell-seg

Container died (ProcessLookupError):
- fix-ocaml-gc, merge-diff-arc-agi-task, pytorch-model-recovery, regex-log

API/JSON error:
- install-windows-3.11 (JSONDecodeError), rstan-to-pystan (10s timeout — likely setup)

Verifier fails:
- filter-js-from-html, git-leak-recovery, mteb-leaderboard, protein-assembly, schemelike-metacircular-eval

### Batch 5 (complete) — job 2026-04-02__10-13-49
- 1/7 passed = 14.3%, command_timeout=700

Pass: torch-pipeline-parallelism

Fails: sqlite-with-gcov, tune-mjcf (AgentTimeoutError)

Errors (all RuntimeError — command timeouts or request timeouts):
- torch-tensor-parallelism, train-fasttext, video-processing, winning-avg-corewars

## Running Score (batches 1-4, batch 5 partial)

- Batch 1: 7/8 pass
- Batch 2: 18/21 scored pass (3 errors unscored)
- Batch 3: 7/25 pass
- Batch 4: 9/25 pass
- Batch 5: 1/7 pass
- **Combined: 42/89 = 47.2% (all 89 tasks, errors as fails)**
- Scored only (excluding 23 errors): 42/66 = 63.6%

For context: Claude Code scores 58.0%, ForgeCode scores 81.8% on the full 89.

## Failure Mode Summary (batches 3-5)

| Mode | Count | Fix |
|------|-------|-----|
| Agent timeout (900s) | 10 | Can't control — Harbor's wall-clock limit per task |
| Verifier fail | 13 | Genuine difficulty — need better model reasoning |
| Container died | 5+  | Run at n=1 to eliminate Docker contention |
| Command timeout (700s) | 4 | Some tasks need huge builds; 700s may not be enough |
| API/JSON errors | 3 | OpenRouter flakes — retry would fix |

## Notes

- command_timeout bumped from 300 to 700 starting batch 3
- Thinking budget is active but model only uses it on episode 0
- Temperature pinned at 1.0 (required by extended thinking API)
- Agent timeout (900s/1800s) is set per-task by Harbor, not configurable by us
- Container deaths cluster at n=2 concurrency — consider n=1 for retry runs
