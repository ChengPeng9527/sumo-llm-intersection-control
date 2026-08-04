# Phase 18 Report

## Objective

Separate the decision pipeline into three explicitly traceable stages:

1. Raw LLM decision
2. Cooperative post-processing
3. Deterministic safety filtering

## Files Changed

- `src/controllers/decision_pipeline.py`
- `src/controllers/decision_rules.py`
- `src/controllers/raw_llm_controller.py`
- `src/controllers/hybrid_llm_controller.py`
- `src/controllers/hybrid_llm_safety_controller.py`
- `src/llm/postprocessor.py`
- `src/llm/response_parser.py`
- `src/common/logging_schema.py`
- `src/common/metrics.py`
- `common.py`
- `baseline_controller.py`
- `cooperative_controller.py`
- `src/experiments/experiment_runner.py`
- `src/experiments/scenario_generator.py`
- `requirements.txt`
- `requirements-test.txt`
- `pytest.ini`
- `scripts/phase18_sumo_smoke.py`
- `tests/test_decision_pipeline.py`
- `tests/test_llm_postprocessor.py`
- `tests/fakes.py`
- `tests/conftest.py`
- `tests/__init__.py`
- `docs/phases/phase_18/environment.txt`

## Validation

- Syntax-only validation passed via `py_compile` on the Phase 18 controller, pipeline, helper, configuration, and test files.
- Full `pytest` execution passed with `C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe -m pytest`.
- `pytest` collected 30 tests and all 30 passed.
- Standalone SUMO smoke validation passed with `C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe scripts\phase18_sumo_smoke.py`.
- SUMO runtime used headless `D:\Sumo\bin\sumo.exe` 1.27.0 with `traci` and `sumolib` from `D:\Sumo\tools`.
- Smoke summary was written to `results\phase18_smoke\phase18_sumo_smoke\smoke_summary.json`.
- Smoke outcomes:
  - `raw`: 184 rows, 4 vehicles observed, `postprocess_rows = 0`, `safety_override_rows = 0`
  - `hybrid`: 149 rows, 4 vehicles observed, `postprocess_rows = 42`, `safety_override_rows = 0`
  - `hybrid_safety`: 150 rows, 4 vehicles observed, `postprocess_rows = 0`, `safety_override_rows = 0`

## Notes

- The raw, hybrid, and hybrid+safety paths are now separated in code and in logs.
- Raw LLM records now keep the raw response, the validated action, the optional cooperative stage, and the optional safety stage distinct.
- A lightweight YAML fallback was added so the test suite can run without `PyYAML`.
- Cooperative logic was preserved with pure helper functions for regression tests.
- The phase now has a working minimal pytest environment and a standalone SUMO smoke path.
- Live Groq validation was checked for feasibility, but `GROQ_API_KEY` was missing in the shell environment, so the live Groq smoke path is blocked by credentials and was not executed.

## Acceptance Status

INTEGRATION_VALIDATED_LIVE_GROQ_BLOCKED_CREDENTIALS
