# Live Provider Minimal Probe Report

## Scope
- Canonical repository: `D:\Sumo\sumo_train`
- Provider: `Groq`
- Model: `openai/gpt-oss-20b`
- Prompt/request format: canonical structured prompt with `response_format={"type":"json_object"}`
- This probe only covered live provider validation. It did not run SUMO, any pilot matrix, or any dissertation changes.

## 1. Single Request Probe

### Outcome
- Result: `SUCCESS`
- HTTP status: `200`
- Provider success: `true`
- Parser success: `true`
- Retry count: `0`
- Request attempts: `1`

### Request-level evidence
- `request_id`: `probe_01`
- `http_attempt_id`: `1`
- `request_simulation_step`: `1`
- `prompt_hash`: `AE70C86BC125DB64E91BD83E64D7084C12E9D5743321F740B93C14883D82A7B4`
- `request_started_at`: `2026-08-17T20:59:09.985+00:00`
- `request_finished_at`: `2026-08-17T20:59:11.250+00:00`
- Wall-clock latency: `1265.9 ms`

### Response evidence
- Response format: `JSON`
- Finish reason: `stop`
- Prompt tokens: `806`
- Completion tokens: `87`
- Total tokens: `893`
- Reasoning tokens: `28`
- Visible completion tokens: `59`

### Rate-limit headers
- `x-ratelimit-limit-tokens`: `8000`
- `x-ratelimit-remaining-tokens`: `6682`
- `x-ratelimit-reset-tokens`: not present
- `x-ratelimit-limit-requests`: `1000`
- `x-ratelimit-remaining-requests`: `809`
- `x-ratelimit-reset-requests`: not present

## 2. Two Request Sequential Probe

### Outcome
- Result: `FAIL`
- The second request did not complete within the outer validation window.
- The probe was interrupted after more than `90 s` of waiting.
- Because the second request did not complete, no second-request response metadata was captured.

### What is known
- First request in the sequential probe completed normally.
- The second request did not complete within a reasonable live-validation timeout.
- This is not consistent with the expected post-first-request pacing derived from the current limiter configuration.

## 3. Limiter Timing Audit

### Current limiter configuration
- TPM ceiling: `8000`
- RPM ceiling: no explicit default ceiling in the client state; live responses can populate `x-ratelimit-limit-requests`
- Safety margin: none explicit
- Estimated tokens per request: default `768` tokens
- Retry backoff: `1 s`, `2 s`, `4 s`, `8 s` capped at `8 s`
- Retry-After behavior: if a `Retry-After` header exists, or the body says `try again in Xs`, that delay is respected; 429s enforce budget pacing

### Theoretical pacing
- Minimum spacing before the first observed request update:
  - `60 * 768 / 8000 = 5.76 s`
- After the single successful probe, observed total tokens were `893`
  - Updated spacing estimate:
  - `60 * 893 / 8000 = 6.6975 s`

### Comparison with probe behavior
- Expected inter-request spacing after the first success: about `6.70 s`
- Observed second-probe behavior: the second request did not finish within `> 90 s`
- Conclusion: the observed live behavior is not normal relative to the limiter’s theoretical wait

## 4. Diagnostic Validation

The new request-level fields were present in the live result:
- `request_id`
- `http_attempt_id`
- `request_simulation_step`
- `prompt_hash`
- `request_started_at`
- `request_finished_at`

This probe distinguishes:
- provider request: the live Groq call itself
- HTTP attempt: the attempt counter exposed as `http_attempt_id`
- trace row: not applicable in this minimal probe because no vehicle trace was generated

## 5. Assessment

- Single request live validation: pass
- Sequential two-request live validation: fail
- Limiter behavior: not yet validated as normal under sequential use
- Larger smoke test justification: not yet justified

## 6. Verdict

`LIVE_PROVIDER_MINIMAL_PROBE_FAIL`

