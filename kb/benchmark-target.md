# Benchmark Target

## What Counts As Comparable
To compare fairly against Claude Code's public score, runs should use:
- Harbor
- dataset `terminal-bench@2.0`
- the official TB2 task set
- default task containers and verifier flow
- no ad hoc task substitutions

## Important Distinctions
- `terminal-bench@2.0`: the benchmark path we want for public-score comparison
- `terminal-bench-core==0.1.1`: older beta/current-at-that-time leaderboard dataset, not the same target
- local `original-tasks/`: useful for debugging and harness development, not the same as the official TB2 evaluation set

## Known Counts
- TB2 official dataset size: `89` tasks
- Local cloned repo `original-tasks/` directories: `241`

## Verified Harbor Fact
Harbor resolved `terminal-bench@2.0` and reported:
- `89` tasks available in that dataset

## Smoke-Task Note
Attempting Harbor with `--single hello-world` failed because `hello-world` is not in the TB2 official 89-task dataset.
Harbor reported example TB2 task names such as:
- `adaptive-rejection-sampler`
- `bn-fit-modify`
- `break-filter-js-from-html`
- `build-cython-ext`
- `build-pmars`
