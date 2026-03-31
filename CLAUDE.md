# kill-terminalbench

## Mission
Build an agent harness that beats Claude Code on Terminal-Bench 2.0.

## Target Benchmark
- **Terminal-Bench 2.0** — 89 hard tasks, each in its own Docker environment with automated test verification.
- Website: https://www.tbench.ai/
- GitHub: https://github.com/laude-institute/terminal-bench (cloned to `./terminal-bench/`)
- Paper: https://arxiv.org/abs/2601.11868
- Evaluation harness: **Harbor** (https://github.com/laude-institute/harbor)
- Baseline agent: **Terminus** (bare tmux pane, no tools/scaffolding)

## Competition Target
- **Claude Code (Anthropic)** — rank 39, **58.0% ± 2.9** with Opus 4.6 (2026-02-07)
- Claude Code with Opus 4.5: 52.1%, Sonnet 4.5: 40.1%, Opus 4.1: 34.8%, Haiku 4.5: 27.5%
- Goal: beat 58.0% (Claude Code Opus 4.6), stretch goal: beat 82% (ForgeCode)

## Leaderboard Snapshot (TB 2.0, as of 2026-03-31)
| Rank | Agent | Model | Score |
|------|-------|-------|-------|
| 1 | ForgeCode | Claude Opus 4.6 | 81.8% ± 1.7 |
| 2 | ForgeCode | GPT-5.4 | 81.8% ± 2.0 |
| 3 | TongAgents | Gemini 3.1 Pro | 80.2% ± 2.6 |
| 4 | SageAgent | GPT-5.3-Codex | 78.4% ± 2.2 |
| 5 | ForgeCode | Gemini 3.1 Pro | 78.4% ± 1.8 |
| 6 | Droid | GPT-5.3-Codex | 77.3% ± 2.2 |
| 7 | Capy | Claude Opus 4.6 | 75.3% ± 2.4 |
| 8 | Simple Codex | GPT-5.3-Codex | 75.1% ± 2.4 |
| 9 | Terminus-KIRA | Gemini 3.1 Pro | 74.8% ± 2.6 |
| 10 | Terminus-KIRA | Claude Opus 4.6 | 74.7% ± 2.6 |
| ... | ... | ... | ... |
| 39 | **Claude Code** | **Claude Opus 4.6** | **58.0% ± 2.9** |

### Key Insight
Same model (Opus 4.6) powers both ForgeCode at 81.8% and Claude Code at 58.0%.
The 24-point gap is pure agent scaffolding/strategy — not model capability.
This means we can beat Claude Code without a better model. Just a better harness.

## Terminal-Bench Architecture (from cloned repo)

### How Tasks Work
Each task lives in `original-tasks/<task-id>/` and contains:
- `task.yaml` — instruction (English), difficulty, category, timeouts, parser
- `Dockerfile` + `docker-compose.yaml` — isolated Docker environment
- `solution.sh` — reference oracle solution
- `run-tests.sh` — test execution script
- `tests/` — pytest or custom test files

Task config fields: `instruction`, `difficulty`, `category`, `tags`, `parser_name`, `max_agent_timeout_sec`, `max_test_timeout_sec`, `run_tests_in_same_shell`

### How Agents Integrate
Two integration paths:

**1. Installed Agent (container-based)** — `AbstractInstalledAgent`
- Agent gets installed INTO the task Docker container
- Provides: install script, env vars, run commands
- Claude Code uses this: `npm install -g @anthropic-ai/claude-code`, then runs `claude -p <instruction>`
- Pros: full filesystem/network access inside container
- Cons: adds dependencies, may conflict with task container

**2. External Agent (tmux-based)** — `BaseAgent` directly (e.g., Terminus)
- Agent sends keystrokes to tmux session from OUTSIDE the container
- Gets terminal output back via `capture_pane()`
- Loop: LLM sees terminal state → generates commands → sends keystrokes → repeats
- Pros: zero container contamination, cleaner separation
- Cons: limited to what you can do via terminal I/O

### How Claude Code Runs on TB
```
ClaudeCodeAgent(AbstractInstalledAgent)
  → installs via claude-code-setup.sh.j2 into container
  → runs: claude --verbose --output-format stream-json -p <instruction> --allowedTools Bash Edit Write Read Glob Grep LS WebFetch NotebookEdit NotebookRead TodoRead TodoWrite Agent
  → single shot, blocks until complete
```

### Terminus (Baseline Agent)
- Sends structured JSON commands (keystrokes, is_blocking, timeout_sec)
- LLM outputs: state_analysis, explanation, commands[], is_task_complete
- Max 50 episodes per task
- Retries LLM calls up to 3x on parse errors
- Uses LiteLLM for model routing

### Registered Agents
claude-code, aider, codex, cursor-cli, gemini-cli, goose, grok-cli, mini-swe-agent, opencode, openhands, qwen-code, terminus-1, terminus-2, mcp-terminus, oracle, naive, nop

### Key Datasets
- `terminal-bench-core` v0.1.0 — 70 tasks (original launch)
- `terminal-bench-core` v0.1.1 — patched for TB 0.2.4+
- `terminal-bench-core` head — latest from main branch

### Running
```bash
# Install
uv tool install terminal-bench
# or: pip install terminal-bench

# Run
tb run --agent terminus --model anthropic/claude-3-7-latest --dataset-name terminal-bench-core --dataset-version 0.1.1

# Run specific task
tb run --task-id hello-world --agent claude-code --model anthropic/claude-3-7-latest
```

## Claude Code Prompt Audit (from ~/ccode/claude-code-source)

### Total Prompt Size
- System prompt + all tool descriptions: **~42,000-46,000 chars (~10,500-11,500 tokens)**
- Estimated useful content for benchmark: **~6,000-8,000 chars (~1,500-2,000 tokens)**
- **Bloat ratio: 75-85% of the prompt is irrelevant for non-interactive benchmark tasks**

### Biggest Offenders (ranked by wasted context)

1. **BashTool prompt (~10,000 chars, ~80% irrelevant)**
   - Git commit/PR playbook: ~4,000 chars (step-by-step commit workflow, HEREDOC examples, safety protocol)
   - Sandbox section: ~2,000 chars (filesystem/network restriction JSON, override rules)
   - Tool-steering: ~400 chars ("use Glob not find", "use Read not cat")
   - Useful for benchmark: ~1,500 chars

2. **AgentTool prompt (~8,000 chars, ~85% irrelevant)**
   - Fork semantics, coaching, multi-turn examples, "don't peek/race" rules
   - Benchmark needs: "launch subprocess with prompt, get result" = ~200 chars

3. **TodoWriteTool prompt (~7,500 chars, ~95% irrelevant)**
   - 8 XML examples with reasoning tags. Pure UX chrome for human progress tracking.

4. **"Doing Tasks" system section (~3,500 chars, ~70% irrelevant)**
   - Coding style, "don't add docstrings", security reminders, help/feedback instructions

5. **"Actions" system section (~2,200 chars, ~90% irrelevant)**
   - "Measure twice, cut once" blast radius analysis. Useless in a sandbox.

6. **Repeated patterns**:
   - Emoji prohibition: appears 3 times (~240 chars)
   - "Use dedicated tools not bash": duplicated in system prompt AND bash tool
   - "Read before edit/write" gate: appears 2 times

### The Core Lesson
The git commit/PR playbook alone (~4,000 chars) takes more prompt space than GrepTool + FileEditTool + FileWriteTool + FileReadTool + GlobTool combined (~3,150 chars).

Claude Code is optimized for **interactive developer experience**, not **benchmark performance**. Every byte of prompt spent on UX, safety rails, and human interaction patterns is context the model could use for actual problem solving.

### Tool Description Sizes (Terminal-Bench relevant)
| Tool | Prompt Chars | Useful % |
|------|-------------|----------|
| BashTool | ~10,000 | ~20% |
| AgentTool | ~8,000 | ~15% |
| FileReadTool | ~1,100 | ~60% |
| FileEditTool | ~700 | ~60% |
| GrepTool | ~620 | ~90% |
| FileWriteTool | ~450 | ~50% |
| GlobTool | ~280 | ~85% |

## Strategy Notes
- Claude Code runs as an installed agent (inside container) with full tool access
- We can either:
  1. Build an installed agent (like Claude Code) — gets installed in container, runs our harness
  2. Build an external agent (like Terminus) — sends commands via tmux from outside
  3. Hybrid — external orchestrator that can also install tools in container
- Key advantages to exploit:
  - **Minimal system prompt** — strip 75-85% bloat, give model more context for actual task
  - **Minimal tool descriptions** — core semantics only, no UX/safety/coaching overhead
  - **No redundant steering** — say it once, not 3 times
  - Better error recovery and retry logic
  - Domain-specific strategies per task category
  - Multi-model routing (best model per domain)
  - Better timeout/episode management

## Task Domains (TB 2.0)
- Software engineering (compiling exotic code, fixing broken environments)
- Machine learning (training, data pipelines)
- Security (vuln resolution, CTF-style)
- Data science / scientific computing
- System administration (network config, kernel builds, QEMU)
- API usage, gaming, misc

## Dev Notes
- Terminal-bench repo cloned to `./terminal-bench/`
- Need to also clone Harbor: https://github.com/laude-institute/harbor
- Study ForgeCode and TongAgents approaches if public
- Identify specific tasks where Claude Code fails
