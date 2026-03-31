# Infrastructure

## Docker
- Docker is running via Colima.
- Active Docker context: `colima`
- Resolved Docker socket used by SDK: `unix:///Users/manirashahmadi/.colima/default/docker.sock`

## Compose
- Installed via Homebrew: Docker Compose `5.1.1`
- Docker plugin discovery configured in `~/.docker/config.json`

## Python Runtime
- System `python3`: `3.9.6`
- Benchmark/runtime interpreter: `.venv/bin/python` -> Python `3.12.12`
- CLI re-execs into Python 3.12 automatically for benchmark paths

## Installed Tooling
- `terminal-bench` installed editable into `.venv`
- `harbor` installed into `.venv`

## OpenRouter
- API key loaded from `.env`
- Model default: `anthropic/claude-opus-4.6`
- Client path: Anthropic SDK pointed at OpenRouter-compatible base URL

## Verified Environment Facts
- Official local Terminal-Bench harness path works
- Official Harbor dataset resolution works for `terminal-bench@2.0`
- OpenRouter API key can access:
  - key usage endpoint
  - credits endpoint
- This ARM/Colima machine is suitable for harness development and synthetic validation.
- This ARM/Colima machine is not a trustworthy source of final TB2 benchmark results for browser-sensitive x86 task images.
- Score-bearing Harbor runs should be executed on the rented `x86_64` machine.

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
- Default summary model: `anthropic/claude-3.5-haiku`
- Model calls now use an explicit client timeout and reduced retries.
