# Request Provenance Static Validation

## 1. Final Schema Fields

The request-level provenance fields are present in the final record schema and are expected to reach `step_records.csv`:

- `request_id`
- `request_simulation_step`
- `http_attempt_id`
- `prompt_hash`
- `request_started_at`
- `request_finished_at`

The additional provider provenance fields are also represented in the schema path and should persist when available:

- `requested_provider`
- `requested_model`
- `actual_provider`
- `actual_model`
- `provider_switch_count`

## 2. Static Schema Chain

The provenance path is aligned end-to-end:

1. `src/common/logging_schema.py` declares the CSV field names.
2. `src/common/metrics.py` initializes the record slots.
3. `common.py` now forwards request provenance into `create_record(...)`.
4. `src/controllers/decision_pipeline.py` now passes the request provenance and provider provenance into `create_record(...)`.
5. The CSV writer receives the populated record and writes the fields unchanged.

This means the earlier blank columns were caused by propagation loss before the writer, not by schema absence.

## 3. Success-Path Synthetic Record

Validated design for one logical provider request producing two vehicle decisions:

- `simulation_step = 100`
- `request_id = test_req_001`
- `http_attempt_id = 1`
- `prompt_hash = abc123`
- `request_started_at = present`
- `request_finished_at = present`

Expected rows:

- two vehicle rows
- same `request_id`
- same `request_simulation_step`
- same `prompt_hash`
- same timestamps
- different `vehicle_id`

This preserves the invariant that one logical request may map to multiple vehicle rows.

## 4. Failure / Fallback Path

Validated design for provider failure followed by deterministic fallback:

- `request_id = test_req_002`
- `provider_success = false`
- failure reason = `500 INTERNAL`

Expected behavior:

- the vehicle row still retains `request_id`
- `http_attempt_id`
- `prompt_hash`
- `request_started_at`
- `request_finished_at`
- failure reason
- fallback status

Provider failure must not clear request provenance.

## 5. Retry Semantics

The schema distinguishes:

- logical provider request
- HTTP attempt

If a logical request retries, `http_attempt_id` is the discriminant.  
If only the final attempt is persisted, that design must be documented explicitly and should not invent attempt history that was not recorded.

## 6. One-Request / Multiple-Row Invariant

The record model must satisfy:

- `unique request_id count = 1`
- `vehicle row count = 2`
- `provider request count = 1`

Vehicle row count must never be used as a proxy for provider request count.

## 7. CSV Round-Trip Result

The static schema design supports a CSV round-trip with no field loss:

- headers remain stable
- provenance fields remain non-empty when populated upstream
- timestamps remain serializable
- `http_attempt_id` remains readable as an attempt discriminator

## 8. Tests Executed

From the prior provenance fix pass:

- `python -m py_compile` passed
- `git diff --check` passed
- deterministic provenance self-check passed

This static validation pass did not call any live provider and did not run SUMO.

## 9. Safe-to-Run Assessment

The next live pilot is safe to run from a provenance schema perspective because:

- the provenance fields exist in the schema
- the record builder forwards them
- the controller path passes them
- the regression invariant is preserved

## 10. Verdict

`REQUEST_PROVENANCE_STATIC_VALIDATION_PASS`
