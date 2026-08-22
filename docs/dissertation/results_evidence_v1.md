# Results Evidence v1

This note collects the exact evidence that can be written into the dissertation results chapter without overstating the data.

## 1. Formal v2 dataset completeness

- Repository: `D:\Sumo\sumo_train`
- Formal experiment ID: `dissertation_formal_v2`
- Planned runs: `24`
- Completed runs: `24`
- Valid runs: `24`
- Missing runs: `0`
- Duplicate runs: `0`
- Technical reruns: `0`
- Collision count: `0` across all runs

Evidence:

- `D:\Sumo\sumo_train\docs\research\formal_experiment_v2_execution_report.md`
- `D:\Sumo\sumo_train\results\formal_experiment\dissertation_formal_v2\formal_experiment_summary.json`
- `D:\Sumo\sumo_train\results\formal_experiment\dissertation_formal_v2\run_manifest.json`

## 2. Aggregate provider reliability

Across all formal v2 live LLM-bearing rows:

- provider attempts: `2664`
- provider successes: `109`
- provider failures: `2555`
- parser successes: `109`
- fallback count: `2555`
- finish reason distribution: `stop = 109`
- truncations: `0`
- mean latency: `423.52 ms`
- median latency: `389.13 ms`

Interpretation:

- the formal v2 live provider path worked, but most attempted live calls fell back
- the dissertation should treat this as a validity threat and not as a simple model-performance win

Evidence:

- `D:\Sumo\sumo_train\docs\research\formal_experiment_v2_execution_report.md`

## 3. Controller-level traffic outcome summary

### Rule-based

- 4V: completion `100%`, collisions `0`, mean waiting time `82` steps, mean speed `2.31 m/s`
- 8V: completion `100%`, collisions `0`, mean waiting time `82` steps, mean speed `2.31 m/s`

### Raw LLM

- 4V: completion `100%`, collisions `0`, provider attempts `444`, provider successes `26`, parser successes `26`, fallbacks `418`, mean waiting time `15` steps, mean speed `6.80 m/s`, mean latency `456.37 ms`
- 8V: completion `100%`, collisions `0`, provider attempts `444`, provider successes `3`, parser successes `3`, fallbacks `441`, mean waiting time `15` steps, mean speed `6.80 m/s`, mean latency `766.23 ms`

### Hybrid

- 4V: completion `100%`, collisions `0`, provider attempts `444`, provider successes `22`, parser successes `22`, fallbacks `422`, mean waiting time `15` steps, mean speed `6.80 m/s`, mean latency `451.61 ms`
- 8V: completion `100%`, collisions `0`, provider attempts `444`, provider successes `18`, parser successes `18`, fallbacks `426`, mean waiting time `15` steps, mean speed `6.80 m/s`, mean latency `447.77 ms`

### Hybrid + Safety

- 4V: completion `100%`, collisions `0`, provider attempts `444`, provider successes `22`, parser successes `22`, fallbacks `422`, mean waiting time `15` steps, mean speed `6.80 m/s`, mean latency `356.22 ms`
- 8V: completion `100%`, collisions `0`, provider attempts `444`, provider successes `18`, parser successes `18`, fallbacks `426`, mean waiting time `15` steps, mean speed `6.80 m/s`, mean latency `342.59 ms`

Evidence:

- `D:\Sumo\sumo_train\docs\research\formal_experiment_v2_execution_report.md`
- `D:\Sumo\sumo_train\results\formal_experiment\dissertation_formal_v2\runs\**\step_records.csv`

## 4. Decision-flow evidence

Formal v2 step records show that final decisions were mostly determined by deterministic layers and fallback handling rather than direct live LLM output.

Observed formal v2 counts across step records:

- `DETERMINISTIC_INTERFACE_RULE`: `3522`
- `FALLBACK`: `1722`
- `LLM_RAW`: `23`
- `COOPERATIVE_POSTPROCESSOR`: `1`
- safety overrides: `0`

Interpretation:

- the dissertation should frame the system as a pipeline, not as an unconstrained LLM controller
- direct LLM influence exists, but it is mediated by validation, interface rules, and fallback handling

Evidence:

- `D:\Sumo\sumo_train\results\formal_experiment\dissertation_formal_v2\runs\**\step_records.csv`
- `D:\Sumo\sumo_train\src\common\metrics.py`

## 5. What the results do not support

The current formal v2 evidence does not support the following claims:

- "LLM is universally better than rule-based control"
- "Safety verification improved performance"
- "The system proves general scalability to 16 vehicles"
- "Low collision count alone proves safety"
- "Raw LLM performance can be separated from fallback-dominated pipeline behavior"

These statements would require either more evidence or a narrower formulation.

## 6. Safe dissertation wording

A defensible summary sentence is:

> The formal v2 dataset shows a fully completed and collision-free 24-run matrix, but the live LLM-bearing controllers are heavily mediated by fallback behavior, so the dissertation must interpret performance as pipeline behavior rather than pure model performance.
