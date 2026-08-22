# Provenance Trace Fix Audit

## Root Cause

Request-level provenance was present in the provider/client diagnostics, but `src/controllers/decision_pipeline.py` dropped it when building the per-vehicle trace.

Specifically, `build_decision_trace()` did not copy these fields from `llm_meta` into each trace entry:

- `request_id`
- `request_simulation_step`
- `http_attempt_id`
- `prompt_hash`
- `request_started_at`
- `request_finished_at`
- `requested_provider`
- `requested_model`
- `actual_provider`
- `actual_model`
- `provider_switch_count`
- `provider_chain`
- `provider_failure_reason`
- `provider_success`

Because `create_record()` reads from the trace entry, the final `step_records.csv` rows were blank even when the live provider succeeded.

## Fix

`build_decision_trace()` now preserves the request-level provenance and provider provenance fields in every trace entry, so `create_record()` can write them into `step_records.csv`.

## Validation

- `py_compile` passed for `src/controllers/decision_pipeline.py` and `tests/test_decision_pipeline.py`
- deterministic provenance regression script passed: `provenance-trace-validation-ok`
- `git diff --check` passed earlier in this pass

## Verdict

`PROVENANCE_TRACE_FIX_APPLIED`
