# Evaluation Specification v1

## Purpose

Define metrics in a way that is reproducible from the current logging schema.

## Source Fields

Primary source fields available in `step_records.csv` include:

- `run_id`
- `experiment_id`
- `controller`
- `safety_enabled`
- `scenario_id`
- `vehicle_count`
- `seed`
- `simulation_step`
- `simulation_time_seconds`
- `vehicle_id`
- `route_id`
- `speed_before_action`
- `speed_after_action`
- `distance_to_intersection`
- `time_to_intersection`
- `inside_control_zone`
- `raw_decision`
- `llm_raw_decision`
- `validated_llm_decision`
- `postprocessed_decision`
- `final_decision`
- `conflict_detected`
- `conflict_type`
- `priority_reason`
- `outside_control_zone_rule_applied`
- `postprocess_applied`
- `postprocess_reason`
- `safety_override`
- `safety_reason`
- `decision_source`
- `llm_called`
- `llm_mode`
- `llm_model`
- `llm_response_time_ms`
- `json_parse_success`
- `retry_count`
- `fallback_used`
- `departed`
- `arrived`
- `collision`

## Primary Metrics

### 1. Completion Rate

- **Research purpose**: measure whether scheduled vehicles complete the episode.
- **Corresponding RQ**: RQ1, RQ2, RQ3, RQ4
- **Formula**: `arrived vehicles / departed vehicles`
- **Source fields**: `departed`, `arrived`, `run_metadata.departed_count`, `run_metadata.arrived_count`
- **Unit**: ratio
- **Aggregation**: mean across seeds and scenarios
- **Missing-data handling**: if departed count is missing, derive from row flags; if still missing, mark as unavailable
- **Interpretation**: higher is better
- **Limitations**: completion can remain 1.0 even if waiting is excessive

### 2. Throughput

- **Research purpose**: measure how many vehicles finish during the episode
- **Corresponding RQ**: RQ1, RQ2, RQ3, RQ4
- **Formula**: `arrived count`
- **Source fields**: `arrived`, `run_metadata.arrived_count`
- **Unit**: vehicles
- **Aggregation**: mean or sum, depending on comparison
- **Missing-data handling**: derive from row flags if metadata is absent
- **Interpretation**: higher is better
- **Limitations**: should be compared only on equal scenario duration

### 3. Mean Waiting Time

- **Research purpose**: measure efficiency cost from stopping or near-stopping
- **Corresponding RQ**: RQ1, RQ2, RQ3, RQ4
- **Formula**: average number of time steps with `speed_after_action < stop_speed` per vehicle, or the project's summary implementation
- **Source fields**: `speed_after_action`, `vehicle_id`
- **Unit**: steps
- **Aggregation**: mean across vehicles, then mean across seeds
- **Missing-data handling**: if a run lacks vehicle rows, mark as unavailable
- **Interpretation**: lower is better
- **Limitations**: counts stop-like states, not full queueing theory delay

### 4. Mean Speed

- **Research purpose**: measure overall motion efficiency
- **Corresponding RQ**: RQ1, RQ2, RQ3, RQ4
- **Formula**: average `speed_after_action`
- **Source fields**: `speed_after_action`
- **Unit**: m/s
- **Aggregation**: mean across rows or vehicles
- **Missing-data handling**: rows with missing speed are ignored
- **Interpretation**: higher is usually better, but only within safe comparisons
- **Limitations**: high speed alone is not sufficient evidence of good control

### 5. Episode Duration

- **Research purpose**: measure how long a run lasts
- **Corresponding RQ**: RQ1, RQ2, RQ3, RQ4
- **Formula**: `max(simulation_time_seconds) - min(simulation_time_seconds)` or final step times simulation step length
- **Source fields**: `simulation_time_seconds`, `simulation_step`
- **Unit**: seconds
- **Aggregation**: mean across runs
- **Missing-data handling**: derive from step records if metadata is absent
- **Interpretation**: shorter can indicate better flow, but only if completion remains acceptable
- **Limitations**: depends on episode stopping rule

### 6. Collision Count

- **Research purpose**: safety outcome
- **Corresponding RQ**: RQ3, RQ4
- **Formula**: count of records or metadata entries indicating collision
- **Source fields**: `collision`, `run_metadata.collision_count`
- **Unit**: events
- **Aggregation**: sum across runs
- **Missing-data handling**: use metadata if present, otherwise row flags
- **Interpretation**: lower is better
- **Limitations**: zero collisions does not by itself prove robust safety

### 7. Minimum TTC / TTC Threshold Violations

- **Research purpose**: quantify safety margin
- **Corresponding RQ**: RQ3, RQ4
- **Formula**: minimum of `time_to_intersection`, or count of pairs below the threshold
- **Source fields**: `time_to_intersection`, `conflict_detected`
- **Unit**: seconds or count
- **Aggregation**: minimum per run, then mean of minima; threshold violation count summed
- **Missing-data handling**: if `time_to_intersection` is missing, mark as unavailable
- **Interpretation**: lower TTC is riskier; more threshold violations indicate greater safety pressure
- **Limitations**: TTC is a proxy, not a direct collision prediction

## Secondary Metrics

### 1. Parser Success Rate

- **Purpose**: measure whether the raw provider text can be parsed
- **RQ**: RQ1, RQ5
- **Formula**: `number of successful parses / number of LLM requests`
- **Source fields**: `json_parse_success`, `llm_called`
- **Unit**: ratio
- **Interpretation**: higher is better
- **Limitation**: a successful parse can still contain a poor decision

### 2. Fallback Rate

- **Purpose**: measure how often the pipeline had to fall back
- **RQ**: RQ1, RQ5
- **Formula**: `number of rows or runs with fallback_used = true / total rows or runs`
- **Source fields**: `fallback_used`
- **Unit**: ratio
- **Interpretation**: lower is better

### 3. LLM Request Success Rate

- **Purpose**: measure connectivity reliability
- **RQ**: RQ1
- **Formula**: `successful live requests / total live requests`
- **Source fields**: `llm_called`, `fallback_used`, `json_parse_success`
- **Unit**: ratio
- **Interpretation**: higher is better
- **Limitation**: a successful request does not guarantee a good decision

### 4. Decision Latency

- **Purpose**: measure response time of the LLM provider path
- **RQ**: RQ1, RQ5
- **Formula**: average `llm_response_time_ms`
- **Source fields**: `llm_response_time_ms`
- **Unit**: milliseconds
- **Interpretation**: lower is better
- **Limitation**: only meaningful for live or real-mode requests

### 5. Safety Override Count and Rate

- **Purpose**: measure how often safety changes the action
- **RQ**: RQ3, RQ5
- **Formula**: count or rate of `safety_override = true`
- **Source fields**: `safety_override`
- **Unit**: count and ratio
- **Interpretation**: lower is safer only if collision count is also low; otherwise the trade-off must be discussed

### 6. Postprocessor Intervention Count and Rate

- **Purpose**: measure cooperative adjustments
- **RQ**: RQ2, RQ5
- **Formula**: count or rate of `postprocess_applied = true`
- **Source fields**: `postprocess_applied`, `postprocess_reason`
- **Unit**: count and ratio
- **Interpretation**: shows when cooperative logic actively changes a decision

## Decision-Flow Metrics

### 1. Raw Action Distribution

- **Formula**: count of `llm_raw_decision` values
- **Source fields**: `llm_raw_decision`

### 2. Validated Action Distribution

- **Formula**: count of `validated_llm_decision` values
- **Source fields**: `validated_llm_decision`

### 3. Postprocessed Action Distribution

- **Formula**: count of `postprocessed_decision` values
- **Source fields**: `postprocessed_decision`

### 4. Final Action Distribution

- **Formula**: count of `final_decision` values
- **Source fields**: `final_decision`

### 5. Raw-to-Final Agreement Rate

- **Formula**: `count(final_decision == validated_llm_decision) / count(rows with valid raw decisions)`
- **Source fields**: `llm_raw_decision`, `validated_llm_decision`, `final_decision`

### 6. Validated-to-Postprocessed Change Rate

- **Formula**: `count(postprocessed_decision != validated_llm_decision) / count(rows)`
- **Source fields**: `validated_llm_decision`, `postprocessed_decision`, `postprocess_applied`

### 7. Postprocessed-to-Final Change Rate

- **Formula**: `count(final_decision != postprocessed_decision) / count(rows entering safety stage)`
- **Source fields**: `postprocessed_decision`, `final_decision`, `safety_override`

### 8. LLM Direct Influence Rate

- **Formula**: `count(final_decision == validated_llm_decision) / count(rows with valid parsed raw decisions)`
- **Source fields**: `validated_llm_decision`, `final_decision`, `json_parse_success`

### 9. Deterministic Intervention Rate

- **Formula**: `count(final_decision changed by interface rule, postprocessor, or safety) / total rows`
- **Source fields**: `outside_control_zone_rule_applied`, `postprocess_applied`, `safety_override`

## NOT_CURRENTLY_AVAILABLE Handling

No primary metric is fundamentally blocked by the current logging schema. If a particular downstream table cannot compute a metric because a run is incomplete or a field is missing, tag the cell as `NOT_CURRENTLY_AVAILABLE` and state the missing source field or the incomplete run.

## Interpretation Rules

1. Do not compare runs with different scenario definitions as if they were identical.
2. Do not claim better safety from zero collisions alone.
3. Do not treat smoke results as formal experiment results.
4. Do not treat the single live revalidation as a full-scale statistical evaluation.
