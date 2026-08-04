# Phase 14 Report

## Objective

Validate a real Groq-backed LLM smoke test and add decision-caching support so real LLM experiments remain practical.

## Files Changed

- `llm_controller.py`
- `test_free_llm.py`
- `.env.example`
- `docs/current_project_status.md`

## Validation

- `test_free_llm.py` returned `{"status":"success"}` against Groq.
- `llm_controller.py` completed a real Groq-backed 8-vehicle smoke test.
- The smoke test used `LLM_DECISION_INTERVAL=20` to reuse model decisions across steps and avoid API-call overload.

## Notes

- The 60-step smoke test produced `Vehicles observed: 8`, `Departed: 8`, and `Arrived: 0`, which is expected because the time window was intentionally shortened.
- Full 240-step real-LLM runs will need the same caching strategy and may still require a longer timeout for practical use.

## Acceptance Status

PASS

