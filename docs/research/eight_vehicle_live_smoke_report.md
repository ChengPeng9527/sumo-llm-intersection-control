# Eight Vehicle Live Smoke Report

## Objective

Verify that the canonical 8-vehicle live controller path can complete end-to-end under the frozen Groq request configuration without changing the dissertation method.

## Frozen Configuration

- Repository: `D:\Sumo\sumo_train`
- Branch: `phase-18-decision-pipeline-separation`
- Controller: `raw_llm`
- Scenario: `formal_low_v8_seed1`
- Vehicle count: `8`
- Seed: `1`
- Provider: `Groq`
- Model: `openai/gpt-oss-20b`
- Request config: `max_completion_tokens = 256`, `reasoning_effort = low`, `timeout = 30.0`, `max_retries = 0`
- Prompt contract: canonical multi-vehicle JSON contract

## Run Result

- Run id: `SMOKE_8V_RAW_V2_v8_seed1_real`
- Raw evidence directory: `results/raw/SMOKE_8V_RAW_V2_v8_seed1_real/`
- Diagnostic summary directory: `results/diagnostics/eight_vehicle_live_smoke_v1/`

### System-level outcome

- Vehicles observed: `8`
- Departed: `8`
- Arrived: `8`
- Throughput: `8`
- Completion rate: `100.00%`
- SUMO completion: `passed`
- TraCI cleanup: `passed`
- Residual SUMO processes: none observed

### Request-level evidence

- Request-row count observed in the artifact trace: `106`
- Provider success count: `16`
- Parser success count given provider success: `16 / 16 = 100%`
- Finish reason distribution: `stop` only
- Truncated response count: `0`
- Completion-token values observed: `35, 36, 37, 56, 67, 73, 74, 75, 84, 119, 123, 130, 235`
- Reasoning-token values observed: `9, 10, 11, 15, 19, 20, 21, 26, 41, 47, 78, 82, 89, 168`

## Interpretation

This smoke run shows that the frozen 8-vehicle live path can complete end-to-end and that the token metadata is now preserved in the unified logging schema. The run also shows provider unreliability during the episode, so the evidence should be used as execution-readiness evidence rather than as a performance claim.

## Evidence Paths

- `results/raw/SMOKE_8V_RAW_V2_v8_seed1_real/step_records.csv`
- `results/raw/SMOKE_8V_RAW_V2_v8_seed1_real/run_metadata.json`
- `results/raw/SMOKE_8V_RAW_V2_v8_seed1_real/events.jsonl`
- `results/diagnostics/eight_vehicle_live_smoke_v1/eight_vehicle_live_smoke_summary.json`
- `results/diagnostics/eight_vehicle_live_smoke_v1/eight_vehicle_live_smoke_trace.jsonl`

## Verdict

**EIGHT_VEHICLE_LIVE_SMOKE_PASSED**
