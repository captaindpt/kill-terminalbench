# Usage And Cost

## What We Can Measure With Only The API Key
The OpenRouter key alone currently allows access to:
- key-level usage and remaining limit
- account-level credits and total usage
- per-generation usage and cost embedded in model responses

## Current Snapshot
Recorded on `2026-03-31` from this repo environment.

### Key Endpoint Snapshot
- Key label: `[redacted]`
- Remaining limit: `199.62498`
- Current key usage: `0.37502`
- Daily usage: `0.37502`
- Weekly usage: `0.37502`
- Monthly usage: `0.37502`
- Expires at: `2026-04-07T17:26:00.002+00:00`

### Credits Endpoint Snapshot
- Total credits: `1659.65`
- Total usage: `1263.7506178`

## Local Accounting
The repo now supports:
- per-run usage summarization from saved response artifacts
- optional pre/post OpenRouter key snapshots
- optional pre/post credits snapshots

## Current Implementation
- helper module: `ktb/openrouter_usage.py`
- local TB runner writes `openrouter-usage.json` for new runs

## Known Example
For `runs/2026-03-31__13-43-35`:
- cost: `$0.016095`
- input tokens: `2494`
- output tokens: `145`
- generation IDs captured:
  - `gen-1774979019-47g8JICNeZyvXEtqX3fJ`
  - `gen-1774979021-srO68F3kkDdlMoa7gdoD`
  - `gen-1774979024-8ikDXj1Rie0WO4AIQUAJ`
