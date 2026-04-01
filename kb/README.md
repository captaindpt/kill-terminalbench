# Knowledge Base

This folder is the project-local knowledge base for `kill-terminalbench`.

Purpose:
- capture benchmark facts we want to preserve
- record infra decisions and verified environment details
- track run status and notable outcomes
- keep operational notes out of the main source tree

Suggested reading order:
1. `project-overview.md`
2. `benchmark-target.md`
3. `infrastructure.md`
4. `runs.md`
5. `failures.md`
6. `task-buckets.md`
7. `usage-and-cost.md`

Conventions:
- Prefer dated, factual entries over long narrative notes.
- Record exact commands, paths, dataset IDs, and run IDs when relevant.
- Update this KB when benchmark setup, infra, or observed metrics materially change.
- Treat run records as one of two classes only:
  - `debug run`: selective task checks, smoke tests, local harness validation, patching support
  - `official run`: Harbor + `terminal-bench@2.0` full 89-task sweep intended for score comparison
- Never describe a `debug run` as progress against the official 89-task benchmark.
