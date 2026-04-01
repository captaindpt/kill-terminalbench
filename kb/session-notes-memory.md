# Session Notes Memory

## Status
- Proposed feature only
- Not implemented in the harness

## Idea
- Maintain a lightweight per-task notes file, for example `/tmp/ktb-session-notes.md`, inside the task environment.
- The agent would update it at milestone boundaries:
  - confirmed discoveries
  - failed approaches
  - successful fixes
  - remaining concrete next steps
- Compaction would prefer those notes as a grounded source of truth instead of re-deriving state from raw message history every time.

## Why It May Help
- Reduces compaction amnesia on long tasks
- Preserves resolved trial-and-error arcs:
  - what was tried
  - what failed
  - what worked
- Lowers the chance that a compaction summary promotes speculation into fact
- Gives the agent a stable anchor across repeated compactions

## Intended Shape
- Keep notes short and factual
- Use structured sections such as:
  - `Current State`
  - `Key Findings`
  - `Failed Approaches`
  - `Working Approach`
  - `Pending`

## Preferred Implementation Direction
- Prompt-driven first:
  - tell the agent to maintain a task-local notes file itself
- Avoid a separate extraction agent in the first version
  - cheaper
  - simpler
  - better fit for benchmark time budgets

## Risks
- If the agent writes poor notes, compaction could inherit bad state
- Extra note-writing commands could waste turns if overused
- Notes could become stale if the agent stops updating them

## Recommendation
- Keep this behind a feature flag if implemented
- Validate on long-horizon tasks first:
  - `db-wal-recovery`
  - `build-cython-ext`
  - `gpt2-codegolf`
  - `raman-fitting`
