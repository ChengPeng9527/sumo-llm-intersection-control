# Formal V4 Metric Definition Audit

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

## Scope
This audit checks the metric definitions used by the dissertation against the actual implementation in `src/common/metrics.py`, `src/llm/diagnostics.py`, and the raw formal experiment artifacts under `results/formal_experiment/dissertation_formal_v2/` and `results/formal_experiment/dissertation_formal_v4/`.

## Key implementation facts
- `stop_speed = 0.1` from `project_config.yaml`.
- `mean_waiting_time` is implemented as the count of rows whose `speed_after_action < stop_speed`, divided by the number of unique vehicles in the run.
- `mean_speed` is the arithmetic mean of `speed_after_action` across rows.
- `completion_rate` is `arrived_count / departed_count`.
- `throughput` is `arrived_count`.
- `collision_count` is read from run metadata when available, otherwise row flags.
- Provider metadata can be extracted from `finish_reason`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `reasoning_tokens`, `response_content_length`, `provider_request_success`, `parser_success`, `fallback_used`, `latency_ms`, `safety_override`, and `postprocess_applied`.

## Formal v2 validity split
- `formal_v2` contains **24 planned runs**: 12 with `vehicle_count = 4` and 12 with `vehicle_count = 8`.
- The 4-vehicle portion is valid and internally consistent.
- The 8-vehicle portion is invalid because the raw traces only show 4 observed/departed/arrived vehicles despite the planned 8-vehicle configuration.

## Formal v4 validity
- `formal_v4` contains **12 runs**, all at `vehicle_count = 8`.
- All 12 runs observed 8 vehicles, departed 8, arrived 8, and had zero collisions.
- Therefore `formal_v4` is the corrected 8-vehicle evidence set.

## Metric-definition audit table
| Metric | Implementation / evidence | Audit result | Notes |
|---|---|---:|---|
| Completion rate | `arrived_count / departed_count` in `src/common/metrics.py` | VERIFIED_EXISTING_REFERENCE | Safe for dissertation use when departure count is visible. |
| Throughput | `arrived_count` in `src/common/metrics.py` | VERIFIED_EXISTING_REFERENCE | Use only when scenario duration is comparable. |
| Mean waiting time | stop-speed count / unique vehicles in `src/common/metrics.py` | VERIFIED_EXISTING_REFERENCE | This is a stop-like occupancy proxy, not queueing-theory delay. |
| Mean speed | average `speed_after_action` in `src/common/metrics.py` | VERIFIED_EXISTING_REFERENCE | Descriptive traffic-efficiency metric. |
| Episode duration | max simulation time in `src/common/metrics.py` | VERIFIED_EXISTING_REFERENCE | Comparable only within the same scenario configuration. |
| Collision count | metadata or row flags in `src/common/metrics.py` | VERIFIED_EXISTING_REFERENCE | Zero collisions do not imply full safety proof. |
| Provider success / parser success | `src/llm/diagnostics.py` + `step_records.csv` | VERIFIED_EXISTING_REFERENCE | Distinguish provider availability from parser correctness. |
| Fallback rate | `fallback_used` in trace | VERIFIED_EXISTING_REFERENCE | High fallback rates materially affect interpretation. |
| Latency | `latency_ms` / `llm_response_time_ms` in trace | VERIFIED_EXISTING_REFERENCE | Use only for live requests. |
| Safety override | `safety_override` in trace | VERIFIED_EXISTING_REFERENCE | No overrides were observed in formal v2 / v4. |
| Postprocessor intervention | `postprocess_applied` in trace | VERIFIED_EXISTING_REFERENCE | Not observed in the valid corrected evidence; the only historical intervention was in the invalid nominal `formal_v2` 8V traces. |
| Finish reason | `extract_finish_reason()` in `src/llm/diagnostics.py` | VERIFIED_EXISTING_REFERENCE | `stop` appears only on successful live provider rows; `NOT_AVAILABLE` otherwise. |
| Token usage | `extract_usage_metadata()` in `src/llm/diagnostics.py` | VERIFIED_EXISTING_REFERENCE | `completion_tokens` and `reasoning_tokens` are available only on successful live rows. |

## Key caution
The dissertation should **not** describe the observed traffic performance as pure LLM performance. The live LLM-bearing controllers in formal v2 and formal v4 are heavily mediated by fallback behavior and provider unreliability.

