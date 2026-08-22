# Gemini Timeout Audit

## 1. Effective Current Timeout

- Current frozen timeout in code: `30.0` seconds.
- Source of truth: `src/llm/request_config.py` sets `LIVE_TIMEOUT_SECONDS = 30.0`.
- The live client factory forwards that value to the provider client.
- Gemini REST path uses `urllib.request.urlopen(..., timeout=self.timeout)`, so the effective transport timeout is the same `30.0` seconds.
- Official Gemini SDK comparison was not possible in this environment because `google.genai` is not installed.

## 2. Probe Setup

- Provider: `Gemini`
- Model: `gemini-3.6-flash`
- Provider mode: `RESILIENT_MULTI_PROVIDER`
- Provider chain: `Gemini` only
- Prompt hash: `505B557D83F9B133E92637E893C07400001E40728AD47895D6416CE9B8BAB615`
- Prompt tokens observed on successful responses: `902`
- Sequential probe sizes:
  - `30 s` timeout, `5` requests
  - `60 s` timeout, `5` requests
  - `90 s` timeout, `5` requests

The probe used one fixed structured prompt repeated across all groups.

## 3. Controlled Timeout Results

### 30 s Group

- Provider success: `2/5`
- Parser success: `1/5`
- Timeout count: `1/5`
- HTTP 429 count: `2/5`
- Mean latency: `7447.45 ms`
- Median latency: `3310.47 ms`
- p95 latency: `24772.26 ms`
- Max latency: `30074.62 ms`
- Total wall-clock: `37237.40 ms`

Timeout row:
- `request_id`: `gemini_timeout_30s_002`
- elapsed before failure: `30074.62 ms`
- exception: `ProviderRequestError`
- message: `The read operation timed out`
- `http_status`: `null`
- `provider_failure_reason`: `TIMEOUT`

### 60 s Group

- Provider success: `3/5`
- Parser success: `0/5`
- Timeout count: `0/5`
- HTTP 429 count: `2/5`
- Mean latency: `6175.93 ms`
- Median latency: `4151.48 ms`
- p95 latency: `14871.27 ms`
- Max latency: `15965.14 ms`
- Total wall-clock: `30879.80 ms`

### 90 s Group

- Provider success: `0/5`
- Parser success: `0/5`
- Timeout count: `0/5`
- HTTP 429 count: `5/5`
- Mean latency: `112.87 ms`
- Median latency: `108.57 ms`
- p95 latency: `133.74 ms`
- Max latency: `134.53 ms`
- Total wall-clock: `564.52 ms`

## 4. Success vs Timeout Token Comparison

Successful responses:
- Prompt tokens: `902` on every success
- Completion tokens observed: `19`, `30`, `47`, `79`
- Total tokens observed: `1410` on every success in this probe

Timeout response:
- No prompt / completion / total token values were returned because the request timed out before a response payload was received.

Interpretation:
- The timed-out request does not show a larger prompt.
- The prompt hash is identical across all groups.
- This does not support a request-complexity explanation.

## 5. Why the Full 60 s / 90 s Confirmation Is Incomplete

The 60 s and 90 s groups were interrupted by Gemini free-tier quota exhaustion:

- `60 s` group: `2` requests returned `HTTP 429`
- `90 s` group: all `5` requests returned `HTTP 429`

The quota errors are provider-side rate limits, not timeouts.

Because of that quota exhaustion, the full `5/5` validation at `60 s` and `90 s` could not be completed in this environment.

## 6. Official SDK Check

- `google.genai` was not available in the Python runtime used for this audit.
- Result: official SDK comparison could not be performed.

## 7. Interpretation

Best-supported diagnosis:
- The observed timeout is consistent with a client-side timeout threshold at roughly `30 s`.
- The failure occurs at `30074.62 ms`, which is extremely close to the configured timeout.
- Longer timeout settings did not reveal a provider-side hang before quota exhaustion.
- The data do not support a request-complexity explanation.

Residual limitation:
- The planned `60 s` and `90 s` confirmation runs were not fully completable because the Gemini free-tier quota was already exhausted.

## 8. Recommended Timeout

- Recommended operational timeout for Gemini live probes: `60 s`
- Expected wall-clock impact:
  - successful requests that already complete in `4-16 s` will not materially change
  - only tail requests that exceed `30 s` gain headroom

## 9. Readiness for SUMO Pilot

- Gemini is not fully validated for a large SUMO pilot from this audit alone because quota exhaustion blocked the full controlled comparison.
- The current evidence is still much more consistent with `client timeout too short` than with provider-side instability.

## 10. Verdict

`GEMINI_TIMEOUT_INCONCLUSIVE`

## 11. Post-Fix Note

- Gemini default live timeout has been updated from `30.0 s` to `60.0 s` in code.
- This audit remains the evidence base for why the change was made.
- The follow-up minimal live confirmation is recorded in `docs/research/gemini_60s_timeout_validation.md`.

