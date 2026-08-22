# Gemini 60s Live Confirmation

## Scope

- Provider: `Gemini`
- Model: `gemini-3.6-flash`
- Timeout: `60.0 s`
- Execution mode: `RESILIENT_MULTI_PROVIDER`
- Provider chain: `Gemini` only
- Prompt: the same canonical structured prompt used in the prior timeout audit

## 1. Single-Request Validation

Result:
- provider success: `1/1`
- parser success: `1/1`
- HTTP 429 count: `0`
- HTTP 403 count: `0`
- timeout count: `0`
- latency: `3442.91 ms`
- prompt tokens: `912`
- completion tokens: `87`
- total tokens: `1419`
- finish reason: `STOP`
- provider switch count: `0`
- provider failure reason: empty
- fallback count: `0`

Interpretation:
- The first live Gemini request succeeded cleanly under the current 60-second timeout.
- There was no quota or rate-limit error.

## 2. Five-Request Sequential Smoke

Because the first request succeeded without quota/rate-limit errors, the sequential smoke was continued to five requests.

Result:
- provider success: `5/5`
- parser success: `1/5`
- HTTP 429 count: `0`
- HTTP 403 count: `0`
- timeout count: `0`
- fallback count: `0`
- provider switch events: `0`
- mean latency: `5683.52 ms`
- median latency: `3505.79 ms`
- max latency: `13142.66 ms`
- mean prompt tokens: `912`
- mean completion tokens: `54.8`
- mean total tokens: `1419.6`

Per-request notes:
- Request 1: provider success and parser success, `finish_reason = STOP`
- Requests 2-5: provider success but parser failure, each returned `HTTP 200` and `finish_reason = MAX_TOKENS`

## 3. Fallback-Related Diagnostics

- provider switch count: `0` for every request
- provider failure reason: empty on successful requests
- fallback count: `0`
- no deterministic fallback was needed in this minimal live check

## 4. Interpretation

What this confirms:
- The Gemini 60-second timeout is live and usable.
- The earlier 30-second timeout problem is no longer blocking the first request.
- The live path now gets a successful response under the updated timeout.

What this does not confirm:
- The 5-request smoke did not achieve parser success on every request.
- I therefore do not treat this as full provider reliability validation for SUMO use yet.
- No SUMO formal experiment was started.

## 5. Verdict

- Minimal live validation: `PASS`
- Sequential smoke: `provider PASS`, `parser PARTIAL`
- SUMO readiness: not yet asserted from this smoke alone
