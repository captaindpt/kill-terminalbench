# Dynamic Temperature

This note records a possible harness improvement for using different sampling temperatures at different phases of a task.

## Core Idea

Do not use one fixed temperature for the whole task.

The agent needs different behavior in different phases:

- exploration when the task is unclear
- disciplined execution when a path is known
- stable verification and cleanup near the end

## Why It Matters

A single fixed temperature forces a tradeoff:

- high temperature helps generate novel approaches
- low temperature improves consistency, verifier alignment, and exact execution

Benchmark tasks often need both.

## Where Lower Temperature Helps

Rough range: `0.0` to `0.3`

Use lower temperature when:

- the failing component is already known
- the file or command to edit is already known
- the task is mostly procedural
- the agent is following explicit test/verifier output
- the agent is doing final verification or cleanup
- the task needs stable formatting or exact output

Examples:

- artifact cleanup
- deployment correctness
- structured data output
- final stop decision
- deterministic fix execution after the root cause is known

## Where Higher Temperature Helps

Rough range: `0.6` to `1.0`

Use higher temperature when:

- the task is ambiguous
- multiple hypotheses are plausible
- the agent needs a fresh angle after repeated failures
- the task is exploit-heavy, parser-heavy, or search-heavy
- early reconnaissance is still ongoing

Examples:

- bypass generation
- exploit payload search
- reverse engineering
- debugging with multiple plausible causes
- algorithmic or heuristic search

## Candidate Policies

### 1. Phase-Based

- opening phase: higher temperature
- execution phase: lower temperature
- final verification phase: lowest temperature

Simple and likely the safest first version.

### 2. Failure-Responsive

- start medium
- raise temperature after repeated failed attempts on the same subgoal
- lower temperature again after the first concrete success signal

This is useful for escaping local minima.

### 3. Task-Bucket-Based

- higher base temperature for exploit/search/forensics tasks
- lower base temperature for data formatting, deployment, and exact-fix tasks

This is attractive but depends on a reliable task classifier.

## Recommended First Version

Keep it simple:

- default temperature: `0.3`
- first 2-3 episodes: `0.6`
- if loop detector fires or repeated failures occur on the same subgoal: temporarily raise to `0.8`
- once a concrete success signal appears: drop to `0.2`
- in the final quarter of the budget: cap at `0.2`

This preserves some exploration while improving stability after convergence.

## Signals That Temperature Should Go Up

- no clear root cause yet
- repeated failures on the same subgoal
- many hypotheses and little narrowing
- exploit/search-heavy task characteristics

## Signals That Temperature Should Go Down

- exact fix target is known
- verifier/test output already identifies the next step
- a working direction has been found
- final output is being prepared
- cleanup/hygiene/final checks are underway

## Risks

- too much temperature switching can make behavior hard to reason about
- raising temperature late can destabilize a nearly-correct task
- lowering temperature too early can trap the agent in a weak local plan

## Recommendation

If implemented, start with a small, explicit schedule driven by:

- episode number
- loop detection
- presence of a concrete success signal

Avoid a complex task classifier in the first version.

## Status

Concept only. Not implemented.
