# Process-Wide Limiter Logic Audit

## 1. Exact Bug Found

- The process-wide limiter was over-pacing sequential live requests because the limiter path was not consistently treating Groq headers as diagnostics only.
- `x-ratelimit-limit-requests` was previously being misread as an RPM-like ceiling. Groq documents that this is an RPD-style limit, not RPM.
- `retry-after` parsing also needed to accept duration-style values such as `2.5`, `7.66s`, and `2m59.56s`.
- The shared limiter now uses a rolling-window reservation model with local token accounting only. It does not inflate the local RPM ceiling from the provider's `limit-requests` header.

## 2. Remaining Tokens Interpretation

- `x-ratelimit-remaining-tokens` is now recorded as provider diagnostics only.
- The limiter does not use provider `remaining-tokens` to enlarge local budget or to suppress the rolling-window model.
- Local pacing is driven by:
  - `tokens_per_minute_limit`
  - `request_tokens_estimate`
  - the rolling 60-second reservation window

## 3. Double Counting Check

- The limiter no longer double counts the provider's remaining token budget against a local estimate.
- The local estimate is tracked through committed reservation entries in the rolling window.
- A request is reserved once, committed once, and then aged out of the 60-second window.

## 4. RPM Header Issue

- Groq's `x-ratelimit-limit-requests` header is now stored in diagnostics only.
- It does not overwrite `requests_per_minute_limit`.
- The shared limiter remains at the configured local RPM ceiling of `30` unless the caller explicitly changes it.

## 5. Reset Parsing

- `retry-after` now parses duration-style values through the same duration parser used for reset headers.
- `x-ratelimit-reset-tokens` and `x-ratelimit-reset-requests` now parse values such as:
  - `7.66s`
  - `2m59.56s`
  - `3h14m24s`

## 6. Before / After Waits

### Before fix

- The previous live sequential probe stalled for more than 90 seconds on the second request, which was the symptom of over-conservative process-wide pacing.

### After fix

- The synthetic limiter trace for two sequential requests now produces:
  - `calculated_token_wait = 0.0`
  - `calculated_request_wait = 0.0`
  - `chosen_sleep = 0.0`

- The live two-request probe produced:
  - `sleep_events = []`
  - request 1 pacing delay = `0.0 ms`
  - request 2 pacing delay = `0.0 ms`
  - request 1 to request 2 transition with no limiter sleep

## 7. Unit Test Result

- `python -m pytest tests/test_live_provider_client.py -q`
- Result: `11 passed`

### Key test coverage

- sequential token budget pacing does not over-throttle
- shared limiter state is process-wide across clients
- trace output reports zero wait for the verified two-request sequence
- heavy token usage waits for the rolling window to expire
- `x-ratelimit-limit-requests` does not set RPM
- reset header duration parsing works

## 8. Live Two-Request Result

### Request 1

- provider success: `true`
- HTTP status: `200`
- retry count: `0`
- request attempt count: `1`
- request pacing delay: `0.0 ms`
- request latency: `1046.0 ms`
- request ID: `live_probe_1`
- HTTP attempt ID: `1`
- request simulation step: `1`
- response format: `JSON`
- parser success: `true`
- finish reason: `stop`
- prompt tokens: `580`
- completion tokens: `61`
- total tokens: `641`
- rate limit headers:
  - `x-ratelimit-limit-tokens = 8000`
  - `x-ratelimit-remaining-tokens = 6908`
  - `x-ratelimit-limit-requests = 1000`
  - `x-ratelimit-remaining-requests = 865`
  - `x-ratelimit-reset-tokens = 8.19s`
  - `x-ratelimit-reset-requests = 3h14m24s`

### Request 2

- provider success: `true`
- HTTP status: `200`
- retry count: `0`
- request attempt count: `1`
- request pacing delay: `0.0 ms`
- request latency: `313.0 ms`
- request ID: `live_probe_2`
- HTTP attempt ID: `1`
- request simulation step: `2`
- response format: `JSON`
- parser success: `true`
- finish reason: `stop`
- prompt tokens: `580`
- completion tokens: `46`
- total tokens: `626`
- rate limit headers:
  - `x-ratelimit-limit-tokens = 8000`
  - `x-ratelimit-remaining-tokens = 5797`
  - `x-ratelimit-limit-requests = 1000`
  - `x-ratelimit-remaining-requests = 864`
  - `x-ratelimit-reset-tokens = 16.522s`
  - `x-ratelimit-reset-requests = 3h15m50.4s`

### Process-wide limiter state after probe

- `tokens_per_minute_limit = 8000`
- `requests_per_minute_limit = 30`
- `request_tokens_estimate = 768`
- `safety_margin = 0.9`
- `last_provider_limit_tokens = 8000`
- `last_provider_remaining_tokens = 5797`
- `last_provider_limit_requests = 1000`
- `last_provider_remaining_requests = 864`
- `last_retry_after_seconds = null`
- rolling window entries retained: `2`

## 9. Verdict

LIMITER_LOGIC_FIXED

