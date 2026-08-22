# Gemini Raw LLM 4V Pilot Report

## Verdict

`GEMINI_RAW_LLM_4V_PILOT_NOT_USABLE`

## 1. Run Identity

- run_id: `GEMINI_RAW_LLM_4V_S1_PILOT_v4_seed1_gemini2_real`
- controller: `raw_llm`
- provider_name in rows: `Gemini`
- model_name in rows: `gemini-3.6-flash`
- scenario: `formal_low_v4_seed1`
- scale: `4V`
- seed: `1`
- termination_reason: `ALL_VEHICLES_COMPLETED`
- residual SUMO processes: `0`

## 2. Provenance Validation

- vehicle_row_count: `132`
- unique_request_id_count: `0`
- unique_request_simulation_step_count: `0`
- provider_request_count: `0`
- vehicle_rows != provider_requests: `YES`
- request_id missing on rows: `132`
- request_simulation_step missing on rows: `132`
- http_attempt_id missing on rows: `132`
- prompt_hash missing on rows: `132`
- request_started_at missing on rows: `132`
- request_finished_at missing on rows: `132`
- requested_provider missing on rows: `132`
- requested_model missing on rows: `132`
- actual_provider missing on rows: `132`
- actual_model missing on rows: `132`
- provider_switch_count missing on rows: `0`

## 3. Row-Level Probe

First row shows:

- provider_request_attempted: `True`
- provider_request_success: `True`
- parser_success: `True`
- fallback_used: `False`
- decision_source: `DETERMINISTIC_INTERFACE_RULE`
- provider_name: `Gemini`
- model_name: `gemini-3.6-flash`
- request_id: blank
- request_simulation_step: blank
- http_attempt_id: blank
- prompt_hash: blank
- request_started_at: blank
- request_finished_at: blank
- requested_provider: blank
- requested_model: blank
- actual_provider: blank
- actual_model: blank
- live_provider_gate_entered: `False`
- live_provider_enabled: `False`
- credential_available: `False`
- live_client_constructed: `False`
- provider_call_function_entered: `False`
- provider_request_kwargs_built: `False`

## 4. Traffic Outcome

- departed: `4`
- arrived: `4`
- completion rate: `100%`
- collision count: `0`
- operational mean waiting: `11.0`
- mean speed: `7.58 m/s`
- throughput: `4`
- episode duration: normal completion

## 5. Readiness Decision

The episode completed normally, but request-level provenance is still absent in `step_records.csv`. That means the provenance validation gate failed and this pilot cannot be used as a provenance-confirmed live Gemini pilot.

Final verdict: `GEMINI_RAW_LLM_4V_PILOT_NOT_USABLE`
