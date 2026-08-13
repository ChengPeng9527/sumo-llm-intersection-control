# Four-Vehicle Completion Budget Validation

## Purpose

This note records whether the 4-vehicle canonical LLM response failure is caused by an insufficient completion budget / output truncation.

It is a diagnostic evidence note only. It does not change the prompt, parser contract, controller semantics, safety rules, or decision space.

## Repository State

- Repository: `D:\Sumo\sumo_train`
- Branch: `phase-18-decision-pipeline-separation`
- HEAD: `3bd76ac0f252cfdf897eadde40dda6b2bd9532e4`
- Frozen request config before this validation:
  - provider = `Groq`
  - model = `openai/gpt-oss-20b`
  - max_completion_tokens = `128`
  - reasoning_effort = `low`
  - timeout = `30.0`
  - max_retries = `0`

## Validation Design

Two small live audits were run on the same canonical 4-vehicle interface contract:

- `128` completion tokens, 3 provider-success samples
- `256` completion tokens, 3 provider-success samples

Both audits used the same:

- prompt builder
- model
- reasoning effort
- parser
- vehicle-count setup
- route/state generation logic

## Evidence Summary

### 128-token audit

Evidence path:

- `results/diagnostics/four_vehicle_completion_budget_validation_v1/four_vehicle_completion_budget_validation_summary.json`
- `results/diagnostics/four_vehicle_completion_budget_validation_v1/four_vehicle_completion_budget_validation_trace.jsonl`

Observed results:

- provider successes: `3/3`
- parser successes: `0/3`
- finish_reason distribution: `length = 3`
- completion_tokens distribution: `128 = 3`
- reasoning_tokens observed: `76`, `107`, `122`
- truncated response count: `3`
- canonical schema compliance count: `0`

Interpretation:

- all provider-success samples were truncated at the configured completion budget
- the returned text was visibly cut mid-JSON in at least some samples
- the parser failed because the JSON was incomplete, not because the schema contract changed

### 256-token audit

Evidence path:

- `results/diagnostics/four_vehicle_completion_budget_validation_v1_256/four_vehicle_completion_budget_validation_summary.json`
- `results/diagnostics/four_vehicle_completion_budget_validation_v1_256/four_vehicle_completion_budget_validation_trace.jsonl`

Observed results:

- provider successes: `3/3`
- parser successes: `3/3`
- finish_reason distribution: `stop = 3`
- completion_tokens distribution: `76`, `105`, `110`
- reasoning_tokens observed: `21`, `48`, `53`
- truncated response count: `0`
- canonical schema compliance count: `3`

Interpretation:

- increasing the completion budget to 256 removed the truncation failure in this small live sample
- the canonical 4-vehicle JSON contract was returned in full

## Root Cause Assessment

**Exact root cause:** `COMPLETION_BUDGET_TOO_LOW`

### Why this is supported

- the 128-token run returned `finish_reason = length` in all live samples
- completion tokens saturated at exactly `128`
- the response body was visibly truncated mid-JSON
- the 256-token run returned `finish_reason = stop` and full canonical JSON in all live samples
- parser success improved from `0/3` to `3/3` without changing prompt, parser, controller semantics, or safety rules

### Confidence

**Confidence level:** High

This is strong evidence that the 4-vehicle failure was caused by an insufficient completion budget, not by a prompt-contract regression.

## Budget Conclusion

- `128` is demonstrably insufficient for the current 4-vehicle canonical contract
- `256` was tested and was sufficient in this validation set
- **minimum defensible completion budget:** `256`

This conclusion is limited to the current canonical prompt/model/configuration and the observed 4-vehicle live samples.

## Change Scope

- Prompt changed: No
- Parser changed: No
- Method changed: No
- Controller semantics changed: No

## Notes for Supervisor Communication

The safest evidence-based statement is:

> The 4-vehicle failure is caused by output truncation under the current 128-token completion budget. When the budget is raised to 256 tokens, the same canonical 4-vehicle contract completes successfully in the live Groq path.

