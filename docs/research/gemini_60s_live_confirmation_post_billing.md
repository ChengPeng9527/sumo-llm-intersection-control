# Gemini 60s Live Confirmation Post-Billing

## Scope

- Provider: `Gemini`
- Model: `gemini-3.6-flash`
- Timeout: `60.0 s`
- Execution mode: `RESILIENT_MULTI_PROVIDER`
- Provider chain: `Gemini` only
- Prompt: canonical 4-vehicle structured prompt used in the prior Gemini live confirmation

## 1. Sequential 5-Request Smoke

- provider success: `5/5`
- parser success: `0/5`
- HTTP 429 count: `0`
- HTTP 403 count: `0`
- timeout count: `0`
- MAX_TOKENS count: `5`
- fallback-triggered count: `0`
- provider switch events: `0`
- mean latency: `14984.31 ms`
- median latency: `4500.63 ms`
- total wall-clock time: `74921.86 ms`

### Per-request finish_reason and diagnostics

- `gemini_postbilling_001`: provider_success=`True`, parser_success=`False`, finish_reason=`MAX_TOKENS`, http_status=`200`, latency=`3535.02 ms`, prompt_tokens=`903`, completion_tokens=`18`, total_tokens=`1411`
- `gemini_postbilling_002`: provider_success=`True`, parser_success=`False`, finish_reason=`MAX_TOKENS`, http_status=`200`, latency=`4494.48 ms`, prompt_tokens=`903`, completion_tokens=`19`, total_tokens=`1411`
- `gemini_postbilling_003`: provider_success=`True`, parser_success=`False`, finish_reason=`MAX_TOKENS`, http_status=`200`, latency=`25921.5 ms`, prompt_tokens=`903`, completion_tokens=`21`, total_tokens=`1411`
- `gemini_postbilling_004`: provider_success=`True`, parser_success=`False`, finish_reason=`MAX_TOKENS`, http_status=`200`, latency=`36469.92 ms`, prompt_tokens=`903`, completion_tokens=`18`, total_tokens=`1411`
- `gemini_postbilling_005`: provider_success=`True`, parser_success=`False`, finish_reason=`MAX_TOKENS`, http_status=`200`, latency=`4500.63 ms`, prompt_tokens=`903`, completion_tokens=`16`, total_tokens=`1411`

## 2. Fallback-Related Diagnostics

- provider switch count: `0` on every request
- provider failure reason: empty on successful requests
- fallback-triggered count: `0`
- no deterministic fallback was used in this confirmation smoke

## 3. Interpretation

- Parser success remained below `5/5` (`0/5`).
- I am stopping here and not attempting any fix yet, per instruction.
- This is evidence of a parser/output-length issue, not a billing or quota issue, because provider-side requests succeeded without 429/403/timeouts.
- No SUMO formal experiment was started.

## 4. Verdict

- Post-billing 5-request smoke: `provider PASS`
- Post-billing 5-request smoke: `parser PARTIAL`
- Verdict: `GEMINI_POST_BILLING_5_REQUEST_SMOKE_PARTIAL`
