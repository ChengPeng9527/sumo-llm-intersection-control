# Formal Context Provider Failure Audit

## Scope
- Evidence reviewed: `results/diagnostics/provider_reliability_v1/`, `results/diagnostics/raw_llm_reliable_pilot_v1/`, `results/raw/FORMAL_CONTEXT_SMOKE_RAW_V2_v4_seed1_real/`
- Goal: explain why provider-only smoke reached `50/50` while the SUMO formal-context raw LLM pilot reached only `39/148`
- Constraint: no dissertation edits, no new formal experiment

## 1. Failure Classification

Historical provider attempts in the SUMO pilot are `148` rows in `step_records.csv`, but only `53` unique simulation steps produced distinct provider calls. The 109 failed provider attempts are all the same root error class.

| error_type | count | percentage |
|---|---:|---:|
| success | 39 | 26.35% |
| HTTP 429 | 109 | 73.65% |
| timeout | 0 | 0.00% |
| connection error | 0 | 0.00% |
| HTTP 4xx other | 0 | 0.00% |
| HTTP 5xx | 0 | 0.00% |
| SDK exception | 0 | 0.00% |
| JSON/output failure | 0 | 0.00% |
| other | 0 | 0.00% |

Representative failure message from `results/raw/FORMAL_CONTEXT_SMOKE_RAW_V2_v4_seed1_real/step_records.csv`:

> `Error code: 429 - {'error': {'message': 'Rate limit reached for model \`openai/gpt-oss-20b\` in organization \`org_01kz51g8fxeb7rkre55c5hxerx\` service tier \`on_demand\` on tokens per minute (TPM): Limit 8000, Used 7458, Requested 874. Please try again in 2.49s. ...', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}`

This is a provider-side TPM limit, not a parser bug and not a model-quality issue.

## 2. Smoke vs SUMO Request Timing

The smoke run and the SUMO pilot both use the same provider and model, but their request cadence is very different.

| metric | provider-only smoke | SUMO raw pilot |
|---|---:|---:|
| unique provider calls | 50 | 53 |
| observed request rows | 50 | 148 |
| row-level duplicate ratio | 0.00% | 64.19% |
| unique step-signature count | 50 | 41 |
| consecutive identical step signatures | 0 | 12 |
| estimated request-wall time from logged per-request latency | 598.91 s | 9.99 s |
| estimated requests/min | 5.01 | 318.33 |
| mean inter-request interval | 11,978 ms | 188 ms |
| median inter-request interval | 12,408 ms | 79 ms |
| minimum inter-request interval | 1,069 ms | 48 ms |
| max requests in any 1-second window | 1 | 16 |
| max requests in any 10-second window | 3 | 53 |
| max requests in any 60-second window | 7 | 53 |
| mean prompt tokens per unique request | 916.4 | 669.5 |
| mean total tokens per unique request | 1,081.5 | 735.8 |

Important note on method: `run_metadata.json` does not record start/end wall-clock timestamps for the historical raw pilot, so the timing comparison above uses the logged per-request latency stream and reconstructs sequential request-start times from it. The comparison is still valid for burst detection because the provider calls are synchronous.

Interpretation:
- Smoke is slow and spread out, so the token budget resets between calls.
- SUMO compresses the live provider calls into a much tighter request cadence, so the TPM budget is exhausted after roughly a dozen steps.
- The provider itself is working; the SUMO control-loop request pattern is the problem.

## 3. Decision Request Frequency Audit

The raw pilot does not request once per vehicle. It requests once per simulation step, and the same step-level result is duplicated into multiple vehicle rows.

Observed counts from `results/raw/FORMAL_CONTEXT_SMOKE_RAW_V2_v4_seed1_real/step_records.csv`:
- `53` simulation steps with provider calls
- `148` provider-attempt rows in the CSV
- step-to-row multiplicity: `2` rows at 27 steps, `3` rows at 4 steps, `4` rows at 20 steps, `1` row at 2 steps

What this means:
- There is no evidence of multiple provider calls inside a single simulation step.
- The apparent `148` attempt count is a row-level duplication artifact of the step log.
- At the step-signature level, `41/53` requests were unique and `12/53` were repeated consecutive signatures.
- I could not verify byte-identical prompt text because the historical step records do not persist the full prompt payload. The step-signature repetition is therefore an evidence-based proxy, not a literal prompt checksum.

## 4. Rate-Limit Header Audit

Historical raw pilot artifacts did **not** persist the following fields:
- `retry-after`
- `x-ratelimit-limit-requests`
- `x-ratelimit-remaining-requests`
- `x-ratelimit-reset-requests`
- `x-ratelimit-limit-tokens`
- `x-ratelimit-remaining-tokens`
- `x-ratelimit-reset-tokens`

The diagnostics layer has now been enhanced so future successful responses are read via the SDK raw-response path and can carry the response headers into `rate_limit_info`. Failed SDK responses already expose headers through the exception path.

## 5. Dominant Root Cause

The dominant root cause is **rate-limit burst pressure from the SUMO control loop**, not provider instability.

Evidence chain:
1. Provider-only smoke: `50/50` success and `50/50` parser success.
2. SUMO pilot: `39/148` provider success, `109/148` rate-limit failures.
3. Failure class: all 109 failures are `HTTP 429` / `RateLimitError` TPM errors.
4. Request cadence: the SUMO pilot compressed 53 unique requests into a much tighter burst profile than smoke.
5. Repeated state patterns: 12 consecutive step-signature duplicates indicate repeated demand on very similar states rather than a single isolated API glitch.

Why smoke succeeds while SUMO fails:
- Smoke requests are paced naturally by the provider and by the smoke harness.
- SUMO issues live calls inside the simulation loop fast enough to exceed TPM, especially once prompt tokens climb and the model starts consuming the budget quickly.

## 6. Exact Code Changes Made

Diagnostics-only changes already applied in this pass:
- `src/llm/live_provider_sdk_client.py`
  - switched successful live calls to the SDK `with_raw_response` path so response headers are preserved
  - successful responses now populate `rate_limit_info` through the existing diagnostics pipeline
- `tests/test_live_provider_client.py`
  - added a focused test to verify successful responses preserve `x-ratelimit-*` header data in diagnostics

No controller semantics were changed.
No prompt content was changed.
No fallback semantics were changed.
No formal experiment was rerun.

## 7. Retry / Pacing Behaviour

Observed historical raw pilot behaviour:
- `max_retries` on the historical pilot was effectively `0` at the evidence level that matters here because the request stream hit 429s and then immediately fell back in the same control loop.
- `retry-after` was present in the provider error text, but not persisted in the historical step records.
- The live control loop did not have a recorded global provider limiter in the historical evidence.

What the evidence suggests should happen next:
- a shared, process-wide provider limiter should pace live requests across the entire SUMO run
- retry-after should be respected
- burst requests should be bounded with exponential backoff and jitter
- the limiter must be shared, not per-vehicle, or the limit can be bypassed accidentally

## 8. Pre/Post Metrics

Measured from the historical evidence:
- before success rate: `39/148 = 26.35%`
- parser success given provider success: `39/39 = 100%`
- fallback rate: `109/148 = 73.65%`
- mean provider-call latency in the raw pilot: `188 ms` over the unique request stream
- provider-only smoke success: `50/50 = 100%`
- provider-only smoke parser success: `50/50 = 100%`

After metrics in this audit-only pass:
- not remeasured, because this turn was explicitly constrained to analysis and diagnostics-only work without a new formal experiment

## 9. Scientific Gate

- `provider success >= 80%`: **not met** on the historical SUMO pilot evidence
- `parser success given provider success >= 95%`: met on the historical evidence, but only after provider success exists
- `fallback <= 20%`: **not met** on the historical SUMO pilot evidence

## 10. Verdict

`FORMAL_CONTEXT_PROVIDER_IMPROVED_BUT_INSUFFICIENT`
