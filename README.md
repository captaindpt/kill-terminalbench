# kill-terminalbench

A custom agent harness targeting [Terminal-Bench 2.0](https://www.tbench.ai/), an 89-task benchmark for LLM agents solving hard Linux terminal tasks in Docker containers.

## Results

**42/89 tasks passed (47.2%)** on the first full run across all 89 scored TB2 tasks, with 23 tasks lost to infrastructure errors (container deaths, API timeouts, resource limits) rather than wrong answers. Excluding infra errors: **42/66 scored = 63.6%**.

A retry run with resource fixes (6 CPUs, 16GB RAM per container, adaptive thinking) was prepared but blocked by an OpenRouter credit limit before execution.

### Leaderboard Context

| Agent | Model | Score |
|-------|-------|-------|
| ForgeCode | Claude Opus 4.6 | 81.8% |
| Claude Code | Claude Opus 4.6 | 58.0% |
| **kill-terminalbench** | **Claude Opus 4.6** | **47.2% (42/89)** |

The gap is largely infrastructure: 23 of 47 failures were runtime errors, not wrong answers. With the pending retry run (more CPU/RAM, no concurrency, adaptive thinking), projected score is 55-65%.

### Batch Results

All results from jobs run on 2026-04-02, using commit `1ccb471` (batches 1-2) and `52072b5` (batches 3-5).

| Batch | Job | Tasks | Passed | Rate | Notes |
|-------|-----|-------|--------|------|-------|
| 1 (canary) | `2026-04-02__02-07-04` | 8 | 7 | 87.5% | Reliable tasks, 1 model error |
| 2 | `2026-04-02__02-21-26` | 24 | 18 | 75.0% | 3 fails, 3 infra errors |
| 3 | `2026-04-02__03-57-51` | 25 | 7 | 28.0% | Hard tasks + retries of never-passed |
| 4 | `2026-04-02__06-56-25` | 25 | 9 | 36.0% | Mixed fresh tasks |
| 5 | `2026-04-02__10-13-49` | 7 | 1 | 14.3% | Final 7, heavy compute tasks |

### Failure Breakdown (47 failures)

| Category | Count | Description |
|----------|-------|-------------|
| Agent timeout (900s) | 10 | Harbor's per-task wall-clock limit, not configurable |
| Command timeout (700s) | 8 | Heavy builds/downloads exceeding per-command limit |
| Container died | 6 | Docker ProcessLookupError at n=2 concurrency |
| API/JSON errors | 5 | OpenRouter returning errors or garbage JSON |
| Verifier fail | 18 | Model got wrong answer |

## Architecture

The harness plugs into [Harbor](https://github.com/laude-institute/harbor) (the official TB2 evaluation framework) as a `BaseAgent` subclass. It routes API calls through OpenRouter using the Anthropic Python SDK.

### Core Loop

```
For each episode (up to 75):
  1. Send system prompt + conversation history to model
  2. Model responds with bash tool calls
  3. Execute commands in Docker container
  4. Feed results back, repeat
  5. Model responds with no tool calls → task complete
```

### Key Design Decisions

**Minimal system prompt (~1,500 tokens).** Claude Code uses ~11,000 tokens of prompt for git workflows, safety rails, UX chrome. Our prompt is pure execution: inspect, act, verify, stop. The 75-85% bloat reduction gives the model more context for actual problem-solving.

**Single tool: bash.** No Read, Write, Edit, Glob, Grep. Everything through shell commands. Eliminates tool description overhead.

**Adaptive thinking with effort control.** Uses Anthropic's adaptive thinking API (`thinking: {type: "adaptive"}`) with dynamic effort:
- Early episodes (first 20%): `max` effort for planning
- Mid/late episodes: `high` effort for execution
- After failures: bumps to `max` for 2 episodes to force deep reassessment

**Aggressive compaction.** When context grows too large (100K tokens, 20 turns, or 50 messages), older conversation history is summarized by Sonnet 4.6 into a structured format (COMPLETED / KEY FINDINGS / PENDING / AUTHORED FILES) while preserving the 8 most recent messages.

**Anti-stall heuristics:**
- Sequence-aware loop detection (catches both A,A,A and A,B,A,B patterns)
- Per-command-family failure budget with structured reflection nudges
- No-op and re-read detection
- Budget warnings at 50% and 75% episode usage
- Missing deliverable check at 50%

### Files

```
ktb/
  harbor_agent.py       # Main agent loop (OpenRouterHarborAgent)
  harbor_compaction.py  # Context compaction with Sonnet 4.6
  harbor_tooling.py     # Tool result formatting and persistence
  harbor_runner.py      # Harbor CLI wrapper
  openrouter_common.py  # System prompt, tool definitions, client setup
  task_sets.py          # Named task sets for all 89 TB2 tasks
  cli.py                # CLI entry point
  agent.py              # AgentConfig dataclass
kb/
  run-status.md         # Detailed per-task results and failure analysis
```

## Usage

### Prerequisites

- Python 3.12+
- Docker
- OpenRouter API key with access to `anthropic/claude-opus-4.6`

### Setup

```bash
# Clone with submodules
git clone --recursive <repo-url>
cd kill-terminalbench

# Create virtualenv and install
uv venv && uv sync

# Configure
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY
```

### Running

```bash
# Run a specific batch
python3 -m ktb.cli --runner harbor --task-set tb2-batch-1 --n-concurrent 1 -k 1

# Run with resource overrides (recommended for heavy tasks)
python3 -m ktb.cli --runner harbor --task-set tb2-batch-3 \
    --n-concurrent 1 --override-cpus 6 --override-memory-mb 16000 -k 1

# Run all remaining batches sequentially
./run-all-batches.sh

# Retry all failed tasks with max resources
./run-retry-all-failures.sh
```

### Task Sets

| Set | Tasks | Description |
|-----|-------|-------------|
| `tb2-batch-1` | 8 | Canary: historically reliable tasks |
| `tb2-batch-2` | 24 | Previously-passed tasks at varying consistency |
| `tb2-batch-3` | 25 | Never-passed retries + fresh unattempted |
| `tb2-batch-4` | 25 | Fresh unattempted tasks |
| `tb2-batch-5` | 7 | Final tasks to complete 89-task coverage |

Batches 1-5 cover all 89 official TB2 scored tasks with no overlaps.

## What's Next

1. **Top up OpenRouter credits** and run `./run-retry-all-failures.sh` — 47 tasks with 6 CPUs, 16GB RAM, adaptive thinking, n=1
2. **Run k=3 or k=5 attempts** on flaky tasks (ForgeCode uses 5 trials per task for their leaderboard score)
3. **Investigate the 18 verifier fails** — most are subtle model reasoning errors (signed vs unsigned ints, off-by-one, reversed causal edges) that won't be fixed by harness changes
