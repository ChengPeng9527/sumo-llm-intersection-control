# Fallback-Only Ablation Report

## Purpose
This report records a minimal ablation run that exercises the deterministic fallback policy directly, without any provider call, cooperative post-processing, or safety verifier.

## Implementation
- Controller file: `fallback_only_controller.py`
- Runner file: `scripts/run_fallback_only_ablation_v1.py`
- Output root: `results/diagnostics/fallback_only_ablation_v1/`

## Design
The fallback-only controller:
- uses the same deterministic fallback policy as the pipeline's mock path
- does not call the provider
- does not apply cooperative post-processing
- does not invoke the safety verifier

## Runs Executed
- 4V seed 1
- 4V seed 2
- 4V seed 3
- 8V seed 1
- 8V seed 2
- 8V seed 3

## Observed Results

### 4V
- Seed 1:
  - completion rate: 100%
  - average waiting time per vehicle: 11.00 steps
  - average speed: 7.58 m/s
  - collisions: 0
- Seed 2:
  - average waiting time per vehicle: 10.00 steps
  - average speed: 7.79 m/s
  - collisions: 0
- Seed 3:
  - average waiting time per vehicle: 11.00 steps
  - average speed: 7.59 m/s
  - collisions: 0

### 8V
- Seed 1:
  - average waiting time per vehicle: 12.88 steps
  - average speed: 6.88 m/s
  - collisions: 0
- Seed 2:
  - average waiting time per vehicle: 17.88 steps
  - average speed: 6.26 m/s
  - collisions: 0
- Seed 3:
  - average waiting time per vehicle: 15.12 steps
  - average speed: 6.65 m/s
  - collisions: 0

## Interpretation
The fallback-only controller performs very strongly without any live provider involvement:
- it is dramatically better than the rule-based baseline
- it is competitive with the recorded raw LLM aggregate on waiting time

This supports the conclusion that the dissertation's traffic advantage is primarily driven by the deterministic fallback policy rather than successful provider decisions.

## Confidence
High for the ablation itself, because the controller path is explicit and the run output is deterministic for the recorded seeds.

