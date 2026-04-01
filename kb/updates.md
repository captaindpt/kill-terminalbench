# Updates

## 2026-03-31
- Repo moved from rough local harness experiments toward benchmark-faithful execution.
- Docker Compose installed and Docker SDK made to follow Colima via active Docker context.
- Local Terminal-Bench harness path validated on `hello-world`.
- Official Harbor path to `terminal-bench@2.0` wired into the repo.
- Harbor custom-agent smoke run started against `adaptive-rejection-sampler`.
- Run-tracking convention clarified:
  - selective or single-task Harbor/TB runs are `debug runs`
  - only a full Harbor sweep of `terminal-bench@2.0` counts as an `official run`
  - current official full-bench progress remains `0/89` until that sweep is launched
- Added a named official-TB2 debug slice:
  - `tb2-diverse-15`
  - intended for rapid gap-finding before a full 89-task run
- Fixed Harbor task-set handoff bug:
  - initial `tb2-diverse-15` launch accidentally started an unfiltered full-dataset run
  - cause: Harbor path used `args.tasks` instead of resolved `task_ids`
  - corrected run started at `jobs/2026-03-31__14-12-46`
- Harbor agent upgraded for longer tasks:
  - large tool outputs persist to disk and are uploaded back into the task container for later rereads
  - old conversation history is compacted through OpenRouter using a cheaper summary model
  - common non-error `exit_code=1` cases now include semantic notes
  - model calls now have an explicit timeout and retry budget
- Execution policy clarified:
  - this ARM machine is for development and synthetic harness checks
  - the rented `x86_64` machine is the source of truth for TB2 subset/full benchmark runs
- OpenRouter usage tracking added:
  - local artifact summarization
  - key usage snapshots
  - credits snapshots
- Knowledge base created under `kb/`.

## 2026-04-01
- Added a failure ledger covering all observed blockers to date:
  - repo/auth launch issues
  - Docker and Docker Compose readiness issues
  - debug-run timeouts and aborted runs
  - the verified `polyglot-c-py` single-file constraint miss on x86_64
- Added an operational bucket plan for the TB2 task inventory.
- Defined a new cross-bucket 24-task debug batch:
  - `tb2-buckets-24`
  - three representative tasks from each of eight planning buckets
