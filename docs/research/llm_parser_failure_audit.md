# LLM Parser Failure Audit

## Status Note

This document records the earlier fallback-dominated pilot evidence that existed before the parser compatibility fix was live revalidated.

The current canonical state is now documented separately in:

- `docs/research/parser_compatibility_patch_report.md`
- `docs/research/llm_parser_diagnostic_report.md`
- `docs/research/pilot_experiment_report.md`

## 1. Executive Summary

Current canonical repository:

- Repository root: `D:\Sumo\sumo_train`
- Branch: `phase-18-decision-pipeline-separation`
- HEAD: `3bd76ac0f252cfdf897eadde40dda6b2bd9532e4`

Current evidence shows that the canonical 4-controller pilot completed end-to-end, but all live LLM-bearing controllers relied on fallback for every live request:

- `raw_llm`: `53/53` live requests failed, `0/53` parser success
- `hybrid`: `53/53` live requests failed, `0/53` parser success
- `hybrid_safety`: `53/53` live requests failed, `0/53` parser success

The pilot still completed because deterministic fallback and interface rules preserved control flow, not because live Groq outputs were successfully parsed.

Most important conclusion:

- The repository does **not** preserve enough raw provider payloads or exception details in the pilot artifacts to prove the exact low-level root cause.
- Therefore the safest evidence-based verdict is: `PILOT_LOGGING_INSUFFICIENT_FOR_ROOT_CAUSE`.

This means the current pilot is **not** suitable for claiming that Groq-generated decisions were successfully parsed in the canonical 4-controller pilot.

## 2. Parser Contract

`src/llm/response_parser.py` defines the current parser behavior.

### Accepted input shapes

The parser accepts only JSON-like content after optional extraction:

- fenced JSON blocks, e.g. ```json ... ```
- bare JSON objects, e.g. `{...}`
- bare JSON arrays, e.g. `[...]`

### Accepted action values

After JSON parsing, actions are normalized against:

- `PROCEED`
- `WAIT`
- `FREE`

### Supported decision payload structures

The parser can handle either:

- a dictionary keyed by vehicle id, e.g. `{"car0": "PROCEED"}`
- a list of decision objects, e.g. `[{ "vehicle_id": "car0", "decision": "PROCEED" }]`

### Normalization rules

- strings are stripped and uppercased
- anything outside the valid action set becomes `WAIT`
- non-string values become `WAIT`
- malformed JSON returns `ok = false` and defaults all vehicles to `WAIT`

### Important limitation

The parser does **not** accept general prose, markdown commentary, or arbitrary natural-language answers unless they contain extractable JSON in one of the supported shapes above.

## 3. Pilot Response Evidence

### Verified pilot outputs

The pilot output root is:

`D:\Sumo\sumo_train\results\pilot\dissertation_pilot_v1`

Current artifacts present:

- `pilot_config.json`
- `pilot_summary.json`
- `pilot_summary.csv`
- `decision_flow_summary.csv`
- `request_cost_summary.json`
- `runtime_summary.json`
- `pilot_verification.json`
- controller subdirectories for `rule_based`, `raw_llm`, `hybrid`, `hybrid_safety`

### Current pilot outcome

| Controller | Scheduled | Departed | Arrived | Completion rate | Collision count | Live requests | Successful requests | Failed requests | Parser success | Fallback |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rule-based | 4 | 4 | 4 | 1.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Raw LLM | 4 | 4 | 4 | 1.0 | 0 | 53 | 0 | 53 | 0 | 53 |
| Hybrid | 4 | 4 | 4 | 1.0 | 0 | 53 | 0 | 53 | 0 | 53 |
| Hybrid + Safety | 4 | 4 | 4 | 1.0 | 0 | 53 | 0 | 53 | 0 | 53 |

### Decision flow summary

For each LLM-bearing controller:

- total step records: `132`
- `json_parse_success = 0`
- `fallback_used = 132`
- `llm_called = 132`
- decision source distribution:
  - `DETERMINISTIC_INTERFACE_RULE = 50`
  - `FALLBACK = 82`

### Current pilot logging gap

The saved pilot artifacts do **not** include the raw provider payload text or the exception type/message for each failed live request.

That means the repository can prove:

- live requests were attempted
- live requests failed
- fallback was used
- final simulation still completed

But it cannot prove from saved evidence:

- whether the provider returned prose, JSON, markdown, or an empty body
- whether the failure was HTTP/transport, timeout, provider exception, response extraction, or parser mismatch

### Current shell note

The canonical repository still has a validated `pytest` result of `30 passed` in the project evidence trail, but a direct rerun in this session hit environment write-permission issues in:

- `simulation/generated_routes/...`
- `.pytest_cache/...`

That rerun failure is an environment limitation of this session, not evidence of a repository logic regression.

## 4. Response Format Distribution

### What can be counted from saved artifacts

From the current pilot artifacts, the only directly measurable distribution is:

- live request attempts: `53` per LLM controller
- parser successes: `0`
- fallback rows: `132`
- deterministic interface-rule rows: `50`

### What cannot be counted from saved artifacts

There is no saved raw provider text for the current pilot, so these categories cannot be measured from current artifacts:

- pure expected action
- sentence
- reasoning + action
- markdown
- JSON
- XML / tags
- empty response
- provider error payload
- unexpected action
- other

### Consequence

Because raw provider content is not preserved, the repository cannot currently answer whether the model:

- produced a semantically valid action that the parser rejected, or
- failed earlier in the provider request path.

## 5. Exact Failure Mechanism

### What the code implies

In `src/controllers/decision_pipeline.py`, the live path does this:

1. build prompt
2. call `client.chat.completions.create(...)`
3. parse `response.choices[0].message.content`
4. on any exception, fall back to deterministic mock decisions

The important evidence from the saved pilot rows is:

- `llm_called = True`
- `successful_request_count = 0`
- `failed_request_count = 53`
- `fallback_used = True`

That combination means the controller entered the **exception/fallback branch**, not the successful parse branch.

### What this rules out

This pilot does **not** currently prove:

- `PARSER_TOO_STRICT_NON_BEHAVIOURAL_FIX_POSSIBLE`
- `MODEL_OUTPUT_NONCOMPLIANT_METHOD_REVIEW_REQUIRED`
- `PROVIDER_RESPONSE_EXTRACTION_BUG`

Those remain plausible, but not provable from current saved evidence.

### What is most defensible

The most defensible conclusion is:

- the live request path failed before a successful parser-confirmed decision could be recorded
- the repository does not retain enough failure detail to isolate the exact low-level cause

Therefore the exact failure mechanism remains:

`PILOT_LOGGING_INSUFFICIENT_FOR_ROOT_CAUSE`

## 6. Historical Successful Comparison

Historical successful live revalidation evidence exists in:

`results/phase18_live_revalidation/live_summary.json`

### Historical live revalidation facts

- provider: `Groq`
- base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- request count: `1`
- parser success: `true`
- raw response non-empty: `true`
- raw response length: `113`
- raw decision: `MISSING`
- validated decision: `WAIT`
- postprocessed decision: `PROCEED`
- final decision: `PROCEED`
- decision source: `COOPERATIVE_POSTPROCESSOR`
- fallback used: `false`
- safety override: `false`
- logging success: `true`
- trace success: `true`

### Current pilot vs historical live revalidation

Key differences:

1. Historical live revalidation preserved a measurable raw-response summary.
2. Current pilot does not preserve raw provider text or exception detail.
3. Historical live revalidation had `parser_success = true`.
4. Current pilot has `parser_success = 0/53` for all live LLM controllers.

### Interpretation

Historical evidence proves that the live provider path can succeed in principle.

Current pilot evidence proves that the full four-controller pilot can still complete via fallback.

But current evidence does **not** prove that the live provider outputs for this pilot were parser-compatible, because the raw response payloads were not preserved.

## 7. Fallback Dependence

### raw_llm

- live requests: `53`
- parser successes: `0`
- fallback rows: `132`
- final completion rate: `1.0`
- collision count: `0`

### hybrid

- live requests: `53`
- parser successes: `0`
- fallback rows: `132`
- final completion rate: `1.0`
- collision count: `0`

### hybrid_safety

- live requests: `53`
- parser successes: `0`
- fallback rows: `132`
- final completion rate: `1.0`
- collision count: `0`

### Main source of final decisions

In this pilot, the final control flow was dominated by:

- deterministic interface rule for vehicles outside the control zone
- fallback decisions for live-request failure rows
- not by successfully parsed live Groq decisions

### What the completion rate means

`completion_rate = 1.0` only means the simulation completed and all four vehicles arrived.

It does **not** mean the live LLM layer succeeded.

## 8. Research Impact

### Supported

- The experimental chain can execute end-to-end without crashing.
- The four-controller pilot can complete and produce consistent artifacts.
- The repository can log completion, arrival, collision, and decision-source statistics.

### Partially supported

- Groq was configured as the provider for the live pilot.
- Live requests were attempted for all three LLM-bearing controllers.

### Not supported by current pilot evidence

- “Groq output was successfully parsed for this pilot”
- “Current pilot demonstrates valid live LLM decision quality”
- “Hybrid improves performance based on live LLM decisions”
- “Safety improves performance based on live LLM decisions”
- “Formal performance conclusions can be drawn from the current pilot”

### Conservative dissertation interpretation

This pilot is best treated as:

- an execution-readiness and logging-robustness check
- not as evidence of successful live LLM parsing quality
- not as a formal performance comparison

## 9. Live Diagnostic Follow-Up

A minimal live Groq diagnostic runner was added at:

`scripts/run_llm_parser_diagnostic.py`

It reuses the current prompt builder, provider client, response parser, and raw controller validation path without starting SUMO.

### Evidence path

`results/diagnostics/llm_parser_diagnostic/`

### Live diagnostic result

- provider: `Groq`
- base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- request count: `3`
- provider request success count: `3`
- parser success count: `3`
- fallback count: `0`
- unique response format categories: `JSON`
- unique parser failure reasons:
  - `TOP_LEVEL_JSON_LIST_WAS_COLLAPSED_TO_OBJECT`

### Observed live response patterns

The saved diagnostic trace shows two distinct Groq JSON shapes:

1. A top-level JSON list containing a single decision object.
2. A top-level JSON object keyed directly by vehicle id.

For the list-shaped responses, the current parser extracted the inner JSON object and then treated it as a vehicle-id keyed dictionary. That produced:

- `llm_raw_decision = MISSING`
- `validated_llm_decision = WAIT`
- `decision_source = FALLBACK`

even though the response contained a semantically valid action.

### Parser-side root cause

The parser-side root cause is now evidenced as:

**`TOP_LEVEL_JSON_LIST_WAS_COLLAPSED_TO_OBJECT`**

This is a parser compatibility gap, not a prompt change or model change.

### Pilot-side limitation remains

The canonical 4-controller pilot artifacts still do not contain raw provider payloads or exception traces for the 53 failed live requests.

So the pilot artifacts alone still cannot prove whether the canonical pilot failures were caused by:

- provider request exceptions,
- top-level list response shapes,
- or a mixture of both.

The best evidence-based interpretation is therefore:

- parser-side root cause: confirmed
- canonical pilot root cause: still mixed and partially unobserved

## 10. Minimal Fix Options

No behavioral change is justified by current evidence.

Only non-behavioural fixes are justified:

1. Preserve raw provider payload text for each live request.
2. Preserve exception type and exception message for each failed request.
3. Record whether the failure happened at:
   - provider call
   - response extraction
   - JSON parse
   - semantic validation
4. Add a minimal parser/extraction regression test matrix using saved raw samples once they are available.

### Why this is the minimal fix

The current evidence gap is observability, not controller logic.

The repository already has:

- prompt builder
- parser
- decision pipeline
- postprocessor
- safety verifier
- pilot orchestration

What it lacks for root-cause proof is the raw failure evidence.

## 11. Required Tests

Before any new pilot revalidation, the repository should have tests that cover:

- fenced JSON
- bare JSON object
- bare JSON array
- dictionary keyed by vehicle id
- list of `{vehicle_id, decision}` objects
- extra prose outside JSON
- lowercase actions
- whitespace around actions
- invalid / empty response
- provider-exception path

Current parser unit tests already cover:

- fenced JSON success
- bad JSON fallback

But they do **not** yet cover the full failure-observability problem exposed by the pilot artifacts.

## 12. Required Pilot Revalidation

If the repository is updated to preserve raw provider payloads and exception detail, the next required revalidation is:

- one fixed 4-vehicle canonical pilot
- same frozen branch and method
- same controllers
- same scenario
- same provider/model settings
- no prompt or strategy changes

The purpose of that rerun would be:

- to classify the actual failure mode from saved evidence
- not to optimize the method
- not to enter formal experiment mode

## 13. Final Verdict

**MIXED_FAILURE_MODES**

Reason:

- canonical pilot artifacts prove fallback-dominated execution and request failure on the 53 live requests
- the live diagnostic runner proves the current parser has a compatibility gap on top-level JSON list responses
- the repository still does not preserve the raw provider payloads and exception details needed to prove the canonical pilot's 0/53 live parser failure was caused by a single unique factor
- therefore the canonical pilot evidence is best interpreted as a mixture of provider-request failure and parser-compatibility failure modes, with the parser-side issue now confirmed independently
