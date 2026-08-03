# Phase 13 Report

## Objective

Fix the scenario wiring so 8-vehicle and 16-vehicle experiments actually use their generated route files and scenario-specific simulation duration.

## Files Changed

- `src/experiments/scenario_generator.py`
- `src/experiments/experiment_runner.py`
- `baseline_controller.py`
- `cooperative_controller.py`
- `llm_controller.py`
- `tests/test_scenario_generation.py`
- `docs/current_project_status.md`

## Validation

- Unit tests passed: 10/10.
- Dry-run confirmed the 8-vehicle and 16-vehicle LLM scenarios are scheduled.
- Real baseline runs confirmed `Vehicles observed` was 8 and 16 respectively.
- The generated scenario config now points to the per-run `routes.xml` and `simulation.sumocfg`.

## Notes

- The 16-vehicle run still may not fully arrive within the current 240-step window, which is an experiment-design limit rather than a wiring bug.
- If you want full completion for every vehicle, increase `SIMULATION_STEPS` further for the dense runs.

## Acceptance Status

PASS

