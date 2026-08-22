# Gemini Raw LLM 4V Failure and Provenance Audit

## 1. Critical Findings

### 1.1 All 9 provider failures share one root cause

- `request_count = 53`
- `provider_request_success_count = 44`
- `provider_failure_count = 9`
- `parser_success_count = 44`
- `fallback_count = 9`
- `http_429_count = 0`
- `http_403_count = 0`
- `timeout_count = 0`
- `latency_max_ms = 60073.81`

The nine failures are not a mixed-quality set. They all map to the same provider-side error class:

- `exception_type = ProviderRequestError`
- `exception_message_redacted` contains Gemini REST payload:
  - `{"error":{"code":500,"message":"Internal error encountered.","status":"INTERNAL"}}`

That means the failure distribution is:

- HTTP / provider internal error: 9
- transport / network error: 0
- timeout: 0
- malformed provider response: 0
- empty candidate/content: 0
- SDK / REST adapter error: 0
- unknown / unrecorded: 0

### 1.2 Failure-by-failure classification

The failing request-level events occurred at simulation steps:

`6, 7, 8, 9, 10, 11, 12, 13, 14`

Each failure had the same classification:

- `simulation_step`: see list above
- `request_id`: present in live provider diagnostics; empty in saved step records
- `HTTP status`: provider reported internal server failure, effectively HTTP 500
- `exception type`: `ProviderRequestError`
- `exception message`: Gemini `INTERNAL` error payload
- `latency`: ranged up to `60073.81 ms`
- `retry count`: no successful retry recovery was recorded
- `finish_reason`: empty on failures
- `provider_request_success`: false
- `parser_success`: false
- `fallback_triggered`: true
- `token usage`: not recorded for failed calls
- `near 60 s boundary`: step 13 was near the timeout boundary, but the recorded failure remained provider `500 INTERNAL`, not a timeout

## 2. Root Cause of Blank Provenance Fields

The provider/client path already generated request provenance:

- `request_id`
- `http_attempt_id`
- `prompt_hash`
- `request_started_at`
- `request_finished_at`
- `request_simulation_step`

The loss happened later in the pipeline:

1. `src/controllers/decision_pipeline.py` built provider diagnostics correctly.
2. The `create_record(...)` call did not forward the request provenance into the record builder.
3. `common.py` then created CSV step records with empty provenance fields.

So the missing fields were a record-propagation bug, not a provider bug.

## 3. Files Changed

- [`/D:/Sumo/sumo_train/common.py`](/D:/Sumo/sumo_train/common.py)
- [`/D:/Sumo/sumo_train/src/controllers/decision_pipeline.py`](/D:/Sumo/sumo_train/src/controllers/decision_pipeline.py)
- [`/D:/Sumo/sumo_train/tests/test_metrics.py`](/D:/Sumo/sumo_train/tests/test_metrics.py)

## 4. Validation

- `python -m py_compile` passed for the modified Python files.
- `git diff --check` passed.
- Deterministic provenance self-check passed:
  - one provider request can share one `request_id` across multiple vehicle rows
  - failure / fallback path still preserves provenance fields
- `pytest` was not available in the bundled Python environment, so the regression coverage was validated with deterministic self-checks instead.

## 5. Semantics Impact

- Controller semantics: unchanged
- Experiment method: unchanged
- Prompt semantics: unchanged
- Parser semantics: unchanged
- Fallback semantics: unchanged
- Cooperative logic: unchanged
- Safety logic: unchanged
- SUMO scenario semantics: unchanged

## 6. Re-run Readiness

The provenance issue is fixed, and the same 4V seed1 pilot can be re-run with request-level fields preserved in `step_records.csv`.

No new formal experiment was started in this audit pass.

## 7. Verdict

`GEMINI_FAILURE_ROOT_CAUSE_IDENTIFIED_AND_PROVENANCE_FIXED`
