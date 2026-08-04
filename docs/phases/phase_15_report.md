# Phase 15 Report

## Objective

Extend the simulation window for 8-vehicle and 16-vehicle trials so vehicles can fully clear the intersection instead of being cut off at the road mouth.

## Files Changed

- `src/experiments/scenario_generator.py`
- `tests/test_scenario_generation.py`
- `docs/current_project_status.md`

## Validation

- Unit tests passed: 11/11.
- A 16-vehicle baseline run completed with `Arrived: 16` and `Completion rate: 100%`.

## Notes

- The previous window length was too short for denser scenarios.
- The new duration rule scales the simulation horizon with vehicle count:
  - 8 vehicles -> 400 seconds
  - 16 vehicles -> 720 seconds

## Acceptance Status

PASS

