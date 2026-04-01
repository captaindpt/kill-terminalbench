# Semantic Compaction

This note records a possible harness improvement beyond ordinary position-based prompt compaction.

## Idea

Detect a resolved local exploration arc and compress it semantically instead of preserving every failed step verbatim.

Pattern:

- attempt A
- fail
- attempt B
- fail
- attempt C
- fail
- attempt D
- succeed

After `D` succeeds, the agent does not need the raw transcript of `A/B/C` in full. It needs the learning:

- what goal it was trying to achieve
- what was already tried
- why those attempts failed
- what finally worked
- what constraint or lesson was learned

## Why It Matters

Ordinary compaction is mostly positional:

- keep recent messages
- summarize older messages
- drop or persist large tool outputs

That manages prompt size, but it does not specifically preserve trial-and-error learning. A resolved exploration arc is not just "old context"; it is a local search result.

This is especially relevant for:

- build/debug loops
- shell command iteration
- exploit payload iteration
- config/service setup retries
- SQL / SQLite forensics

## Relationship To Existing Compaction

This should not replace normal compaction.

Use two layers:

1. Positional compaction
   - keeps overall context under control
2. Semantic arc compression
   - collapses resolved local search into a structured lesson

The second is benchmark-native and should operate on a smaller recent window.

## Candidate Detection Heuristic

Minimal version:

- inspect the last 6-10 tool executions
- require at least 3 failed attempts followed by a success
- require the attempts to belong to the same local subgoal
- keep the successful final step verbatim
- compress only the failed lead-up

Signals for "same local subgoal":

- same file/path touched
- same tool or command family (`pytest`, `sqlite3`, `curl`, `git`, `python`, `sed`, etc.)
- same service/port/resource target
- same explicit assistant intent in surrounding text

## Desired Summary Shape

Preserve:

- Goal
- Failed attempts
- Winning attempt
- Constraint learned

Example:

```text
[Harness] Resolved exploration summary:
- Goal: make the web service persist into verification
- Failed attempts:
  - `python3 -m http.server 8080 &` died when the shell exited
  - `nohup python3 -m http.server 8080 &` also was not durable here
- Winning attempt:
  - switched to a real daemon/service strategy
- Constraint learned:
  - one-shot shell background jobs are not durable in this harness
```

## Benefit

This preserves local learning without carrying every failed turn forward in raw form. It should reduce context noise while improving continuity.

## Risk

False positives are dangerous.

If unrelated failures are compressed into one narrative, the harness rewrites history incorrectly and can hide useful distinctions. That is worse than simple positional compaction.

## Recommendation

If implemented, keep it behind a flag and roll it out narrowly:

- only on recent local windows
- only after explicit failure-to-success arcs
- only when confidence is high that the attempts share one subgoal
- keep the final successful tool result untouched

## Status

Concept only. Not implemented.
