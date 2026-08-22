# Experimental Design v1

## 1. Design Goal

The formal experiment evaluates the frozen dissertation method under a controlled SUMO scenario. The goal is to compare controller variants using the same network, prompt family, request configuration, and logging schema.

## 2. Experimental Factors

The formal v2 matrix varies three factors:

- controller: `rule_based`, `raw_llm`, `hybrid`, `hybrid_safety`
- vehicle count: `4`, `8`
- seed: `1`, `2`, `3`

This yields:

- `4` controllers x `2` vehicle counts x `3` seeds = `24` planned runs

## 3. Fixed Conditions

The following elements are held constant:

- canonical prompt: `P1_BASELINE`
- scenario density: `low`
- live provider: Groq
- base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- request config: `256` max completion tokens, `low` reasoning effort, `30.0` s timeout, `0` retries
- SUMO network and route definitions
- decision space: `PROCEED / WAIT / FREE`

## 4. Execution Provenance

The formal experiment is tied to the freeze commit and tag:

- freeze commit: `7b363fa8add58ac83775eb26dd6ff0b68bea022e`
- freeze tag: `v0.9.1-formal-experiment-freeze`

The fresh formal v2 sweep was executed on branch:

- `phase-18-decision-pipeline-separation`

## 5. Outcome Measures

The dissertation can report the following outcome families:

- completion rate
- throughput
- mean waiting time
- mean speed
- episode duration
- collision count
- parser success rate
- provider success rate
- fallback rate
- request latency
- safety override count and rate
- postprocessor intervention count and rate
- decision-flow agreement / change rates

These measures are defined in `docs/research/evaluation_specification_v1.md` and are computable from the current logging schema.

## 6. Result Interpretation Plan

### RQ1

Compare rule-based control against raw LLM control.

### RQ2

Compare raw LLM against hybrid control.

### RQ3

Compare hybrid against hybrid_safety.

### RQ4

Assess 4V to 8V behavior under the frozen low-density scenario.

### RQ5

Use the trace fields to quantify how much of the final decision comes from validation, cooperative post-processing, and safety verification.

## 7. Validity Controls

The formal v2 design is strong enough for a dissertation first draft because it includes:

- counterbalanced controller order by seed,
- multiple seeds,
- two vehicle scales,
- full trace logging,
- frozen prompt and request settings,
- separate artifact storage for each run.

## 8. Validity Threats

The dissertation must still state the following threats clearly:

- provider reliability is fallback-heavy,
- completion rate is saturated at 100%, so waiting time and intervention metrics matter more than completion,
- no 16-vehicle formal v2 evidence is available,
- safety overrides are zero, so a safety-efficiency trade-off cannot be claimed from this dataset,
- sequential execution can still confound controller comparisons if not discussed carefully.

## 9. Why This Design Is Suitable for a First Draft

The design is already frozen, the runs are complete, and the dataset is reproducible from repository artifacts. That is enough to write a proper dissertation first draft without modifying the method.
