# Live Raw LLM Pilot Report

## Scope
- Controller: `raw_llm`
- Scenario: `formal_low_v4_seed1`
- Seed: `1`
- Vehicle count: `4`
- Provider: `Groq`
- Model: `openai/gpt-oss-20b`

## Outcome
- Final verdict: `FORMAL_CONTEXT_SMOKE_PASSED`
- Provider requests attempted: `true`
- Provider requests succeeded: `true`
- Parser success: `true`
- Residual SUMO processes: `0`
- TraCI cleanup: `passed`

## Key Evidence
- Request count: 148
- Provider success count: 39
- Provider failure count: 109
- Parser success count: 39
- Fallback count: 109
- Completion rate: 1.0
- Collision count: 0

## Interpretation
- The raw LLM path remained live and usable.
- Fallback usage was dominant in this pilot, so the result still supports the dissertation's attribution to fallback-dominant behavior rather than provider robustness.
- The pilot did not introduce a new evidence boundary or rerun the dissertation's formal experiments.

## Artifacts
- [Summary](../../results/diagnostics/raw_llm_reliable_pilot_v1/raw_llm_reliable_pilot_summary.json)
- [Trace](../../results/diagnostics/raw_llm_reliable_pilot_v1/raw_llm_reliable_pilot_trace.jsonl)
