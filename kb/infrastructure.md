# Infrastructure

## Score-Bearing Benchmark Host
- Current benchmark truth host: rented `x86_64` machine
- Current size: `8 vCPU / 32 GB RAM`
- This is the machine to use for Harbor TB2 debug batches and score-bearing runs.
- The older ARM/Colima machine should be treated as development-only.

## Docker
- Docker is running on the benchmark host.
- Docker is accessible to the benchmark user and Harbor can launch task environments.

## Compose
- `docker compose` is available on the benchmark host.
- Harbor TB2 task environments depend on Compose support and should be validated after machine rebuilds or resizes.

## Python Runtime
- Harbor runs use the repo-local `.venv`.
- Benchmark/runtime interpreter should remain the `.venv` Python on the x86 host.

## Installed Tooling
- `terminal-bench` is installed in the repo environment.
- `harbor` is installed in the repo environment.

## OpenRouter
- API key loaded from `.env`
- Model default: `anthropic/claude-opus-4.6`
- Client path: Anthropic SDK pointed at OpenRouter-compatible base URL

## Verified Environment Facts
- Official Harbor dataset resolution works for `terminal-bench@2.0`
- OpenRouter API key can access:
  - key usage endpoint
  - credits endpoint
- Score-bearing Harbor runs should be executed on the rented `x86_64` machine, not on the ARM development host.

## Concurrency Policy
- Strictest benchmark-truth reruns:
  - use `--n-concurrent 1`
- Comparison-grade Harbor runs on the current `8 vCPU / 32 GB` x86 host:
  - default to `--n-concurrent 2`
- Exploratory/debug Harbor runs on the current `8 vCPU / 32 GB` x86 host:
  - default to `--n-concurrent 3`
- Do not increase beyond `3` by default without confirming stability on the current task mix.

## Logging Guarantees
Current adapters write detailed artifacts for debugging:

Local TB runner:
- per-episode `response.json`
- pane captures
- command log
- session logs / casts

Harbor runner:
- `agent/episodes/episode-N/request.json`
- `agent/episodes/episode-N/response.json`
- `agent/episodes/episode-N/tool-results.json`
- `agent/persisted-tool-results/episode-N/tool-XX.txt`
- `agent/compactions/compaction-XX.json`
- trial config
- Harbor job/trial logs

This is sufficient to reconstruct prompt/context progression when the model fails, even without full ATIF trajectory emission.

## Harbor Agent Behavior
- Large tool outputs are now persisted and uploaded into the task container under `/tmp/ktb-agent-artifacts/...`.
- Tool results now return a short preview plus a reread path when output is persisted.
- Long conversations now compact older history through the same OpenRouter client using a cheaper summary model.
- Default summary model: `anthropic/claude-sonnet-4.6`
- Model calls now use an explicit client timeout and reduced retries.
