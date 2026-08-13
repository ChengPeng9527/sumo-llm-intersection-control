# Formal Experiment Execution Design v2

## 1. Objective

Design a fair, reproducible formal experiment protocol for comparing:

- Rule-based
- Raw LLM
- Hybrid
- Hybrid + Safety

under live provider uncertainty such as time/order bias, transient provider failures, and rate limiting.

This design keeps the dissertation method frozen and only changes execution control, logging, and statistical planning.

## 2. Experimental Unit

### Definition

One experimental run is defined as:

`run = one controller × one vehicle scale × one seed × one frozen scenario × one execution attempt`

### Required run metadata

Each run must record:

- `run_id`
- `controller`
- `vehicle_count`
- `seed`
- `execution_order`
- `batch_id`
- `timestamp`
- `provider`
- `model`
- `scenario_hash`
- `config_hash`
- `results_path`

### Run validity principle

The run unit is execution-oriented, not controller-internal.
The run is only comparable if all frozen method settings match.

## 3. Formal Matrix

### Minimum formal matrix

- 4 controllers
- 2 vehicle scales: 4 vehicles, 8 vehicles
- 3 seeds

Total planned valid runs:

- `4 × 2 × 3 = 24`

### Excluded from this round

- 16 vehicles
- 5 seeds

Those may be considered later only if the minimum matrix shows a clear trend.

### Matrix structure

| Vehicle scale | Seed 1 | Seed 2 | Seed 3 |
| --- | --- | --- | --- |
| 4 vehicles | 4 controllers | 4 controllers | 4 controllers |
| 8 vehicles | 4 controllers | 4 controllers | 4 controllers |

Each cell represents one run per controller, so the total remains 24 valid runs.

## 4. Counterbalanced Order

### Why counterbalancing is required

The canonical pilot showed a strong order/time bias:

- `raw_llm` obtained an early success window, then became failure-dominant
- `hybrid` and `hybrid_safety` were disadvantaged by later execution

Therefore, fixed order such as:

`Rule -> Raw -> Hybrid -> HybridSafety`

is not acceptable for formal comparison.

### Order strategy

Use counterbalanced execution batches so that each LLM-bearing controller appears in early, middle, and late positions across the formal matrix.

### Example balanced batch templates

The following are examples, not mandatory copies:

- Batch A: `Rule -> Raw -> Hybrid -> HybridSafety`
- Batch B: `Hybrid -> HybridSafety -> Rule -> Raw`
- Batch C: `HybridSafety -> Rule -> Raw -> Hybrid`

These templates ensure that no single controller is always exposed to the same provider-time position.

### Required property

Across the 3 seeds, each controller should appear at least once in:

- an early slot
- a middle slot
- a late slot

## 5. Independent Run Sessions

Each controller run must be an independent execution unit.

### Required separation

- independent SUMO start
- independent TraCI close
- independent result writing
- independent provider request counters
- independent failure logs
- no shared controller runtime state

### Cooldown recommendation

Insert a short cooldown between controller runs to reduce shared provider/session contamination.

Recommended range:

- `20-30 seconds`

This is an execution-control recommendation only, not a method change.

## 6. Provider Reliability Controls

Formal experiments must log per-request reliability evidence.

### Required request-level fields

- request index
- controller
- run_id
- timestamp
- provider success
- HTTP status
- exception type
- redacted error body
- latency
- retry count
- parser success
- fallback reason

### Forbidden in logs

- API key
- Authorization
- secret material

### Reliability interpretation

Provider reliability is a robustness covariate and a threats-to-validity factor.
It is not a primary performance metric.

## 7. Retry Policy

### Allowed retries

Allow exactly one technical retry for:

- timeout
- transient 5xx
- connection reset
- rate limit when a `Retry-After` header is present

### Disallowed retries

Do not retry for:

- malformed semantic response
- ambiguous action
- parser ambiguity
- invalid decision
- deterministic fallback conditions

### Retry limit

- maximum retries: `1`

### Required retry logging

Record:

- `first_attempt`
- `retry_attempt`
- `final_result`

No unlimited retry loops are allowed.

## 8. Run Validity

### Valid run classes

#### VALID_RUN

The experiment completed and the schema is complete.

#### VALID_RUN_WITH_PROVIDER_FAILURES

The experiment completed, but some live calls failed and were handled by the frozen fallback policy.

This run class may be used for robustness analysis, but it must be reported separately from pure provider-success comparisons.

#### INVALID_TECHNICAL_RUN

Examples:

- SUMO crash
- log corruption
- wrong scenario
- wrong seed
- wrong config
- missing trace

These runs must be excluded from statistics.

#### FAILED_RUN

A run that stops before a valid completion because of a technical failure.

These runs must not be mixed into result tables.

## 9. Fairness Rules

For the same `vehicle_count + seed`, the following must match:

- same scenario
- same route
- same departure schedule
- same SUMO config
- same vehicle parameters
- same termination condition
- same Prompt
- same model
- same decision interval
- same metrics

Additionally, record:

- execution order
- provider success rate

### Fairness objective

Prevent controller identity from being confounded with provider time/order.

The formal experiment should not repeat the pilot condition where the later controller naturally inherits a worse provider window.

## 10. Metrics

### Primary metrics

- completion rate
- throughput
- mean waiting time
- mean speed
- episode duration
- collision count

### Secondary metrics

- parser success
- fallback rate
- latency
- safety override
- postprocessor intervention

### Research metrics

- raw-to-final agreement
- decision flow
- decision source distribution

## 11. Provider Exposure Metrics

Treat provider reliability as a covariate and robustness indicator.

### Required exposure metrics

- Provider Success Rate
- Provider Failure Rate
- Fallback Due To Provider Rate
- Mean Provider Latency
- Retry Rate

### Thesis placement

These metrics belong in:

- Threats to Validity
- Robustness analysis

They are not primary performance outcomes.

## 12. Statistical Strategy

Because the matrix uses only 3 seeds in the minimum formal round, analysis should be descriptive first.

### Required descriptive statistics

- mean
- standard deviation
- median
- 95% confidence interval

### Reporting rule

Do not claim significance prematurely.

If the minimum matrix shows a strong trend, then consider:

- expanding to 5 seeds
- optionally extending to 16 vehicles

No significance claim should be made before that decision gate.

## 13. Stop Rules

Pause remaining runs if any of the following occur:

- 3 consecutive provider failures
- 3 consecutive rate-limit events
- repeated authentication failure
- model unavailable
- schema corruption
- SUMO lifecycle failure

### Rationale

Do not allow one provider outage or one lifecycle bug to contaminate the entire batch.

### Suggested batch-level stop threshold

- conservative threshold: `3`

## 14. Threats to Validity

### Main threats

1. Time/order bias between controllers
2. Provider reliability variation across the run
3. Single-scenario dependence
4. Single-seed dependence within the pilot evidence
5. Failure logging incompleteness for per-request diagnosis
6. Sequential controller execution confounding controller identity with provider state
7. Robustness runs being misread as comparative performance evidence

### Interpretation rule

If provider failure varies strongly over time, controller comparison must be framed as a robustness-aware comparison, not a pure efficiency ranking.

## 15. Decision Gate

After completing the minimum 24-run matrix, classify the state as one of:

- `MINIMUM_FORMAL_MATRIX_SUFFICIENT`
- `MORE_SEEDS_REQUIRED`
- `16_VEHICLE_EXTENSION_RECOMMENDED`
- `PROVIDER_RELIABILITY_TOO_LOW_FOR_VALID_COMPARISON`

### Decision rule

Do not auto-expand the matrix.

Only expand if the minimum matrix and its reliability profile justify it.

## 16. Execution Manifest

Each formal run manifest row should include:

- `run_id`
- `batch_id`
- `order_position`
- `controller`
- `vehicle_count`
- `seed`
- `status`
- `provider_success_rate`
- `fallback_rate`
- `scenario_hash`
- `config_hash`
- `results_path`

## 17. Provider Bias Control Strategy

To reduce systematic provider bias:

1. Randomize or counterbalance controller order.
2. Run each controller in an independent session.
3. Insert a short cooldown between controller runs.
4. Keep each batch small enough that provider degradation is easier to detect.
5. Log request-level reliability evidence.
6. Compare controllers only after stratifying by seed and vehicle scale.

### Example balanced execution order

One acceptable 3-batch template is:

- Seed 1 batch: `Rule -> Raw -> Hybrid -> HybridSafety`
- Seed 2 batch: `Hybrid -> HybridSafety -> Rule -> Raw`
- Seed 3 batch: `HybridSafety -> Rule -> Raw -> Hybrid`

This is an example pattern only. It should be adapted if implementation constraints require a different balanced sequence.

## 18. Implementation Gap Audit

Current repository has the main method and logging framework, but v2 execution still needs execution-only support in the following areas:

- counterbalanced scheduler
- per-run resume support
- request error logging at request level
- cooldown handling between controller runs
- manifest writer
- randomized / counterbalanced ordering
- retry logging
- batch-level reliability summary

These are execution-control additions, not method changes.

## 19. Final Recommendation

- Keep the method frozen.
- Execute the formal matrix only after execution-control gaps are addressed.
- Start with the minimum 24-run matrix.
- Use counterbalanced order and independent sessions.
- Treat provider reliability as a validity threat and robustness covariate.
- Do not expand to 16 vehicles until the minimum matrix has been reviewed.

