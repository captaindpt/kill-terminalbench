# Project Overview

## Mission
Build an agent harness that beats Claude Code on Terminal-Bench 2.0.

## Current Benchmark Target
- Public target: `terminal-bench@2.0`
- Public leaderboard reference: Claude Code with Claude Opus 4.6 at `58.0% ± 2.9`
- Stretch target: top agents around `81.8%`

## Current Execution Paths
- `harbor` runner: intended source of truth for TB2-comparable runs
- `tb` runner: local Terminal-Bench harness path, useful for debugging
- `local` runner: lightweight fallback, not leaderboard-comparable

## Current Code Boundaries
- Harbor-specific adapter:
  - `ktb/harbor_agent.py`
  - `ktb/harbor_runner.py`
- Local Terminal-Bench harness adapter:
  - `ktb/tb_agent.py`
  - `ktb/tb_runner.py`
  - `ktb/tb_runtime.py`
- Shared OpenRouter logic:
  - `ktb/openrouter_common.py`
  - `ktb/openrouter_usage.py`
- Main entrypoint:
  - `ktb/cli.py`

## Current Principle
Keep the source tree clean while iterating:
- isolate benchmark adapters instead of spreading hacks
- keep CLI thin
- prefer environment/config fixes over invasive code changes
- preserve detailed run artifacts for debugging
