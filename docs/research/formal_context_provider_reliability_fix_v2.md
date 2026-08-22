# Formal Context Provider Reliability Fix v2

## What Was Fixed in This Pass

This pass made the live provider diagnostics more complete without changing controller semantics.

Implemented changes:
- `src/llm/live_provider_sdk_client.py`
  - switched successful live calls to the SDK `with_raw_response` path
  - successful responses now retain raw headers and feed `rate_limit_info` into the diagnostics pipeline
- `tests/test_live_provider_client.py`
  - added coverage that successful responses preserve `x-ratelimit-*` header values in diagnostics

Why this matters:
- the historical SUMO pilot did not persist `retry-after` or `x-ratelimit-*` values in the step records
- after this change, future live runs can be audited for provider-side pacing evidence without altering the controller’s decisions

## Root Cause Summary

The provider itself is healthy.
The SUMO integration was the problem.

Evidence:
- provider-only smoke: `50/50` success, `50/50` parser success
- raw SUMO pilot: `39/148` provider success, `109/148` provider failures
- all 109 failures are `HTTP 429` / `RateLimitError` TPM errors
- the pilot compresses live requests into a bursty control-loop pattern with repeated state signatures

## Timing Comparison

Historical evidence summary:
- provider-only smoke: `50` unique requests, about `5.01` requests/min, about `7` requests in any 60-second window
- SUMO raw pilot: `53` unique requests, about `318.33` requests/min on the reconstructed request-start timeline, `53` requests in any 10-second window

This is the key difference:
- the smoke harness spreads requests out
- the SUMO control loop fires rapidly enough to exhaust TPM

## Duplicate Request Pattern

Historical raw pilot request structure:
- `148` provider-attempt rows
- `53` unique simulation-step requests
- row-level duplicate ratio: `64.19%`
- step-signature duplicates: `12` consecutive repeated signatures

Interpretation:
- the model was not being asked 148 independent times
- the same step-level live request was duplicated across multiple vehicle rows in the trace
- the repeated-state pattern is real, but it is not the sole issue; the main issue is burst cadence under a TPM limit

## Current Status of the Reliability Fix

This pass did **not** yet introduce the full process-wide shared rate-limit scheduler required to make the SUMO pilot scientifically ready.

Still needed for a true fix:
- a global provider limiter shared across the whole SUMO process
- retry-after aware pacing
- bounded exponential backoff with jitter
- no per-vehicle limiter reset
- optional exact-state deduplication only if it can be proven semantics-preserving

## Metrics

Historical metrics before any scheduler fix:
- provider success rate: `39/148 = 26.35%`
- parser success given provider success: `39/39 = 100%`
- fallback rate: `109/148 = 73.65%`
- mean provider-call latency in the SUMO pilot: `188 ms` on the logged unique-request stream

After metrics:
- not remeasured in this pass, because the turn was explicitly constrained to diagnostics-only work and no new formal experiment was run

## Scientific Gate

- `provider success >= 80%`: not yet met
- `provider success >= 95%`: not yet met
- `parser success given provider success >= 95%`: met on the historical evidence
- `fallback <= 20%`: not yet met

## Recommended Next Step

Implement the shared global scheduler, then rerun only the same `raw_llm`, `4V`, `seed1`, `formal_low_v4_seed1` pilot.

Do not expand to 8V or the full formal matrix until the provider success gate clears.

## Verdict

`FORMAL_CONTEXT_PROVIDER_IMPROVED_BUT_INSUFFICIENT`
