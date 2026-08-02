# Phase 6 Report

## Objective

Build deterministic scenario generation from the experiment matrix so runs are reproducible.

## Files Changed

- `src/experiments/scenario_generator.py`
- `config/experiment_matrix.yaml`
- `tests/test_scenario_generation.py`

## Validation

- Added a dedicated experiment-matrix loader.
- Generated scenario manifests now record route sequence information.
- Added a determinism test for the route sequence sampler.

## Notes

- Scenario output is written under `simulation/generated_routes/`.
- The generator is seeded, so repeated runs with the same inputs stay stable.

## Acceptance Status

PASS

