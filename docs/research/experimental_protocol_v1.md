# Experimental Protocol v1

## Protocol Goal

Define a controlled, reproducible evaluation plan for comparing rule-based control, raw LLM control, cooperative post-processing, and deterministic safety verification in SUMO.

## Core Comparison Logic

The protocol is organized around five experiment families:

- Experiment A: Rule-based vs Raw LLM
- Experiment B: Raw LLM vs Hybrid
- Experiment C: Hybrid vs Hybrid + Safety
- Experiment D: Scalability / Traffic Complexity
- Experiment E: Decision Flow Analysis

## Experiment A: Rule-based vs Raw LLM

**Purpose**

Check whether raw LLM decisions can substitute for a deterministic rule controller at the same scenario scale.

**Research question**

RQ1

**Hypothesis**

Raw LLM output is usable, but not reliably better than the rule controller without validation.

**Controller modes**

- baseline
- raw LLM

**Scenarios**

- low density, 4 vehicles
- low density, 8 vehicles
- low density, 16 vehicles

**Independent variables**

- controller mode
- vehicle count

**Dependent variables**

- completion rate
- throughput
- mean waiting time
- mean speed
- collision count

**Controlled variables**

- network
- route set
- seed
- simulation step length
- prompt version
- stopping rules

**Seeds**

- 1 to 5 for formal experiments

**Repetitions**

- minimum viable: 3
- recommended: 5
- extended: 10

**Stopping conditions**

- all vehicles arrive,
- simulation reaches configured duration,
- collision occurs,
- simulation deadlock is detected.

**Output files**

- `step_records.csv`
- `run_metadata.json`
- `events.jsonl`
- aggregated summary files

**Acceptance criteria**

- raw LLM must produce parsable actions for the majority of controlled decisions,
- baseline comparison must be executable on the same scenario definition.

**Expected tables**

- controller comparison table
- raw action distribution table

**Expected figures**

- completion and waiting-time comparison chart

## Experiment B: Raw LLM vs Hybrid

**Purpose**

Measure whether cooperative post-processing improves raw LLM behavior.

**Research question**

RQ2

**Hypothesis**

Cooperative post-processing will reduce conservative waiting for compatible flows and improve traceable decision quality.

**Controller modes**

- raw LLM
- hybrid

**Scenarios**

- low density, 4 vehicles
- low density, 8 vehicles
- low density, 16 vehicles

**Independent variables**

- postprocessing enabled or disabled
- vehicle count

**Dependent variables**

- postprocessor intervention rate
- mean waiting time
- completion rate
- raw-to-final agreement rate
- LLM direct influence rate

**Acceptance criteria**

- postprocessor must produce measurable decision changes on at least some compatible cases,
- raw / validated / postprocessed / final fields must remain distinct in logs.

## Experiment C: Hybrid vs Hybrid + Safety

**Purpose**

Measure the effect of deterministic safety verification on the hybrid pipeline.

**Research question**

RQ3

**Hypothesis**

Safety verification will reduce unsafe final actions, but may increase waiting or override frequency.

**Controller modes**

- hybrid
- hybrid + safety

**Dependent variables**

- safety override count
- safety override rate
- collision count
- TTC conflict event count
- mean waiting time
- completion rate

**Acceptance criteria**

- safety layer must only reduce or preserve risky behavior, not create more permissive unsafe actions.

## Experiment D: Scalability / Traffic Complexity

**Purpose**

Evaluate behavior under increasing vehicle count or traffic intensity.

**Research question**

RQ4

**Hypothesis**

Higher traffic load will increase waiting, interventions, and decision disagreement.

**Controller modes**

- baseline
- cooperative
- raw LLM
- hybrid
- hybrid + safety

**Scenario levels**

- 4 vehicles
- 8 vehicles
- 16 vehicles

**Recommended scope**

Keep density fixed while varying vehicle count first. Do not expand both vehicle count and traffic intensity in the same step unless the smaller matrix is already complete.

**Dependent variables**

- throughput
- completion rate
- waiting time
- safety overrides
- intervention rates

## Experiment E: Decision Flow Analysis

**Purpose**

Quantify how decisions change across the pipeline.

**Research question**

RQ5

**Hypothesis**

The final decision will differ from the raw LLM decision in a measurable fraction of cases because validation, cooperative post-processing, and safety may each intervene.

**Required comparisons**

- raw vs validated
- validated vs postprocessed
- postprocessed vs final
- raw vs final

**Dependent variables**

- raw action distribution
- validated action distribution
- postprocessed action distribution
- final action distribution
- raw-to-final agreement rate
- validated-to-postprocessed change rate
- postprocessed-to-final change rate
- deterministic intervention rate

## Minimum Viable Experiment Plan

1. One seed.
2. 4-vehicle scenario.
3. Baseline, raw LLM, hybrid, hybrid + safety.
4. One live provider path if available.
5. One complete aggregation pass.

## Recommended Experiment Plan

1. Five seeds.
2. 4, 8, and 16 vehicles.
3. All five controller modes.
4. One formal comparison table per research question.
5. One flow-analysis table for the decision pipeline.

## Optional Extended Experiment Plan

1. Add multiple traffic densities.
2. Add repeated live-provider checks.
3. Add more sensitivity analysis for TTC thresholds.
4. Add extra baselines only if they answer a specific research question.

## Failure Handling

If a run fails:

1. Stop the run.
2. Record the failure location.
3. Do not rewrite the prompt or strategy unless a confirmed bug requires it.
4. Re-run only after the failure cause is classified.

## Formal Experiment Status

Formal experiments are still pending. The repository currently contains engineering evidence, smoke validation, and one live revalidation, but not a full dissertation-scale experimental sweep.
