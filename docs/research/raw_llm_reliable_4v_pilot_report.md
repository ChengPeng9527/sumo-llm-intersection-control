# Raw LLM 4V SUMO Pilot Report

## Scope
- Controller: `raw_llm`
- Scenario: `formal_low_v4_seed1`
- Vehicle count: 4
- Seed: 1
- Intended run suffix: `recheck4`
- Intended output directory: `results/diagnostics/raw_llm_reliable_4v_pilot_v1/`

## What Was Validated
- The process-wide limiter fix remained in place.
- The raw controller now compiles after the inner live-request helper signature fix.
- The earlier completed pilot attempt (`recheck3`) showed the controller was still failing before provider calls because the inner `run_live_llm_request` helper did not accept `llm_model`.

## Current Pilot Status
- The final live SUMO rerun (`recheck4`) was started and left running beyond the validation window.
- No completed `step_records.csv` was produced for `recheck4` before the run was stopped.
- Therefore, there is no validated live 4V pilot dataset from this turn.

## Evidence From the Completed Failed Attempt
- Completed fallback-only run: `results/raw/E04_RAW_LLM_4V_S1_v4_seed1_recheck3_real/`
- Metadata showed:
  - `llm_mode = real`
  - `llm_model = openai/gpt-oss-20b`
  - `status = completed`
  - `departed_count = 4`
  - `arrived_count = 4`
- Step rows showed `TypeError` on the inner helper:
  - `run_pipeline_controller.<locals>.run_live_llm_request() got an unexpected keyword argument 'llm_model'`
- Because of that helper bug, provider requests were not actually issued in that completed run.

## Unavailable Metrics For The Intended Live Pilot
- decision_events: not available from a completed live pilot run in this turn
- provider_requests: not available from a completed live pilot run in this turn
- actual HTTP attempts: not available from a completed live pilot run in this turn
- successful requests: not available from a completed live pilot run in this turn
- failed requests: not available from a completed live pilot run in this turn
- 429 count: not available from a completed live pilot run in this turn
- retries: not available from a completed live pilot run in this turn
- parser success: not available from a completed live pilot run in this turn
- duplicate prompt count: not available from a completed live pilot run in this turn
- request rate: not available from a completed live pilot run in this turn
- token rate: not available from a completed live pilot run in this turn
- traffic metrics: not available from a completed live pilot run in this turn
- wall-clock runtime: not available from a completed live pilot run in this turn

## Readiness Gates
- ENGINEERING_EXECUTION: FAIL
- LIVE_PROVIDER_RELIABILITY: FAIL
- SCIENTIFIC_EXPERIMENT_READINESS: FAIL

## Verdict
- RAW_LLM_LIVE_PATH_NOT_READY
