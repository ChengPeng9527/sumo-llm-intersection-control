# Phase 18 Report

## Objective

Separate the decision pipeline into three explicitly traceable stages:

1. Raw LLM decision
2. Cooperative post-processing
3. Deterministic safety filtering

## Files Changed

- `src/controllers/decision_pipeline.py`
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
- `requirements.txt`
- `tests/test_decision_pipeline.py`
- `tests/test_llm_postprocessor.py`
- `docs/phases/phase_18/environment.txt`

## Validation

- Syntax-only validation passed via `py_compile` on all Phase 18 controller, pipeline, and test files.
- Full `pytest` execution was not possible in the current shell because the only discoverable Python runtime does not provide `pytest` or `pyyaml`.
- Full analysis execution was not possible in the current shell because the discoverable runtime also lacks `matplotlib`.

## Notes

- The raw, hybrid, and hybrid+safety paths are now separated in code and in logs.
- Raw LLM records now keep the raw response, the validated action, the optional cooperative stage, and the optional safety stage distinct.
- Cooperative and baseline controllers were updated to populate the new traceable fields without changing their core behavior.
- The environment is currently `BLOCKED_ENVIRONMENT` for runtime test verification.

## Acceptance Status

BLOCKED_ENVIRONMENT
