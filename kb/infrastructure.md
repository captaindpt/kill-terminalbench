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
- trial config
- Harbor job/trial logs

This is sufficient to reconstruct prompt/context progression when the model fails, even without full ATIF trajectory emission.
