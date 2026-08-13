# Controller Live Provider Gate Audit

## 1. Observed Contradiction

The provider probe succeeded, but the controller revalidation batch recorded 330 rows with:

- `provider_request_attempted = false`
- `provider_request_success = false`
- `fallback = true`
- `decision_source = DETERMINISTIC_INTERFACE_RULE`
- `final_decision = FREE`

This means the controller batch did not reach the live provider call path, even though the provider itself is reachable.

## 2. Gate Map

| Gate name | Condition | True branch | False branch | Provider call reached | Current evidence |
| --- | --- | --- | --- | --- | --- |
| `stage_mode == baseline` | baseline controller path | deterministic baseline decisions | non-baseline path enters LLM branch | No | Not the observed batch |
| `llm_mode == real` | live provider enabled | attempt live client construction | skip live provider path | No for failed rows | `llm_mode = real` in step records |
| `credential_available` | `GROQ_API_KEY` supplied to controller path | construct live client | `MISSING_CREDENTIAL` skip reason | No | Not observable from old traces |
| `live_client_constructed` | OpenAI client successfully created | enter `run_live_llm_request(...)` | `CLIENT_NOT_AVAILABLE` skip reason | No | Old trace shows zero provider attempts |
| `provider_call_function_entered` | wrapper around `client.chat.completions.create(...)` entered | request kwargs built and request attempted | `provider_request_skipped = true` | Yes only when true | Old trace shows false for all 330 rows |
| `apply_interface_rule(...)` | vehicle outside control zone | final decision forced to `FREE` | retain postprocessed decision | No | Explains `decision_source`, not provider skip |

## 3. `llm_called` Semantics

`llm_called = true` currently means the controller entered the LLM branch, not that the provider request was actually attempted.

Separate fields are now recorded for:

- `llm_branch_entered`
- `provider_request_attempted`

This avoids conflating branch entry with a live network call.

## 4. Provider-Call Eligibility Conditions

From the current controller code, a live provider call requires:

- `llm_mode == "real"`
- a non-empty credential supplied to the controller path
- a constructed OpenAI client
- entry into `run_live_llm_request(...)`

The deterministic interface rule does **not** preempt the provider call. It is applied later in the decision pipeline to vehicles outside the control zone.

## 5. Runtime Flag Audit

The controller path now records:

- `llm_branch_entered`
- `live_provider_gate_entered`
- `live_provider_enabled`
- `credential_available`
- `live_client_constructed`
- `provider_call_function_entered`
- `provider_request_kwargs_built`
- `provider_request_attempted`
- `provider_request_skipped`
- `provider_skip_reason`
- `fallback_trigger_reason`
- `decision_source`

These fields allow a later live run to distinguish live-provider failure from controller fallback.

## 6. Client Construction Audit

The controller path records whether the OpenAI client was constructed.

Recorded fields:

- `live_client_constructed`
- `provider_name`
- `model_name`

The exact short-circuit reason is now explicitly classified when the live client is not constructed.

## 7. Exact Short-Circuit Reason

The prior batch cannot prove the exact sub-reason because the old trace lacked explicit gate fields.

The current code now classifies the short-circuit reason as one of:

- `LIVE_MODE_DISABLED`
- `MISSING_CREDENTIAL`
- `CLIENT_NOT_AVAILABLE`
- `INTERFACE_RULE_SHORT_CIRCUIT`
- `NO_LLM_ELIGIBLE_VEHICLES`
- `PRECONDITION_FAILED`
- `UNKNOWN`

## 8. Evidence Impact

Current conclusion:

- the canonical prompt revalidation batch is invalid for prompt-quality comparison
- the provider probe is still valid evidence of provider reachability
- the controller batch needs a fresh live-provider gate revalidation before prompt comparison is trusted again

## 9. Minimal Fix Boundary

The minimal fix boundary is diagnostics only.

Do not change:

- prompt text
- model
- parser semantics
- controller strategy
- postprocessor
- safety rules
- fallback policy
- scenario
- decision space
- frozen request configuration

## 10. Required Local Smoke

A small local smoke path is still required after diagnostics are in place.

The smoke should prove only that the controller path reaches:

- `client.chat.completions.create(...)`

Do not expand this into a formal experiment.
