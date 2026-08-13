# Four Vehicle Output Truncation Root Cause Analysis

## Scope

This note analyzes the micro-validation failure mode observed for the canonical multi-vehicle prompt/parser contract under the frozen dissertation request configuration.

It does **not** redesign the prompt, parser, controller architecture, decision space, safety layer, or formal experiment design.

## Repository Context

- Repository: `D:/Sumo/sumo_train`
- Branch: `phase-18-decision-pipeline-separation`
- Head: `3bd76ac0f252cfdf897eadde40dda6b2bd9532e4`

## Frozen Request Configuration

- Provider: `Groq`
- Base URL: `https://api.groq.com/openai/v1`
- Model: `openai/gpt-oss-20b`
- `max_completion_tokens = 128`
- `reasoning_effort = low`
- `timeout = 30.0`
- `max_retries = 0`

## Evidence Reviewed

- `results/diagnostics/canonical_multi_vehicle_contract_micro_validation_v1/micro_validation_summary.json`
- `results/diagnostics/canonical_multi_vehicle_contract_micro_validation_v1/micro_validation_trace.jsonl`
- `results/diagnostics/canonical_multi_vehicle_contract_micro_validation_v1/micro_validation_report.md`

No additional provider-side usage metadata artifact was persisted in the current evidence directory, so this report does **not** claim a directly observed `finish_reason`, `completion_tokens`, or `reasoning_tokens` value.

## What Is Already Confirmed

The canonical multi-vehicle output schema is:

```json
{
  "decisions": {
    "<vehicle_id>": "PROCEED|WAIT|FREE"
  }
}
```

The current parser and prompt builder already enforce:

- exact reuse of `traffic_state` vehicle ids
- full coverage of all controlled vehicles
- fallback on missing, duplicate, unknown, or ambiguous vehicles
- legacy compatibility for prior diagnostic shapes

## Micro-Validation Results

### 2 vehicles

- Provider success: `2 / 2`
- Parser success: `2 / 2`
- Canonical schema compliance: `2 / 2`
- Full vehicle coverage: `2 / 2`
- Correct vehicle-id reuse: `2 / 2`

### 3 vehicles

- Provider success: `2 / 2`
- Parser success: `2 / 2`
- Canonical schema compliance: `2 / 2`
- Full vehicle coverage: `2 / 2`
- Correct vehicle-id reuse: `2 / 2`

### 4 vehicles

- Provider success: `4 / 4`
- Parser success: `2 / 4`
- Canonical schema compliance: `2 / 4`
- Full vehicle coverage: `2 / 4`
- Fallback given provider success: `2 / 4`

## Key Failure Evidence

Two 4-vehicle failures are especially diagnostic:

1. A response redacted to only:

   ```text
   {"decisions":{"dbg_v
   ```

   - response length: `20`
   - parser success: `false`

2. Another 4-vehicle failure was truncated mid-object:

   - response redacted tail ended in `... "micro_v4_s505_3"`
   - raw response length: `107`
   - parser success: `false`

These failures are consistent with an incomplete JSON object rather than a schema mismatch that the parser should accept.

## Comparison Table

| request | vehicles | provider success | parser success | raw response length | canonical compliance |
| --- | ---: | ---: | ---: | ---: | ---: |
| sample 1 | 2 | yes | yes | 68 | yes |
| sample 2 | 2 | yes | yes | 68 | yes |
| sample 3 | 3 | yes | yes | 96 | yes |
| sample 4 | 3 | yes | yes | 94 | yes |
| sample 5 | 4 | yes | yes | 118 | yes |
| sample 6 | 4 | yes | no | 107 | no |
| sample 7 | 4 | yes | no | 22 | no |
| sample 8 | 4 | yes | yes | 121 | yes |

## Root Cause Assessment

### Best-supported conclusion

The strongest current explanation is:

**`COMPLETION_BUDGET_TOO_LOW`**

Why this is the best-supported explanation:

- all failures are provider-success cases
- the parser is not failing on a structurally valid canonical object
- failed outputs are truncated mid-JSON
- the 4-vehicle failures are shorter than the successful 4-vehicle outputs
- the prompt now asks for a full per-vehicle mapping, which raises completion demand compared with the earlier single-action style outputs

### Evidence that is still missing

The current evidence set does **not** include:

- `finish_reason`
- `completion_tokens`
- `reasoning_tokens`
- visible/output token split
- prompt token count per request

Because of that, the report cannot claim a formally proven `finish_reason = length`.

## Conservative Verdict

The current evidence supports this provisional classification:

**`COMPLETION_BUDGET_TOO_LOW`**

However, because usage metadata is absent, the strictest evidence-based wording is:

**output truncation is the most likely root cause, but the exact token-budget mechanism is not directly proven in the present evidence set.**

## Implication

This is **not** evidence that the prompt/parser contract is fundamentally broken.

The evidence instead suggests:

- the canonical contract is valid for 2- and 3-vehicle requests in this micro-validation set
- 4-vehicle requests can still overrun the current completion budget or otherwise produce truncated JSON
- a separate provider metadata audit is required if the project wants formal proof of `finish_reason = length`

## Evidence Path

- `D:/Sumo/sumo_train/results/diagnostics/canonical_multi_vehicle_contract_micro_validation_v1/micro_validation_summary.json`
- `D:/Sumo/sumo_train/results/diagnostics/canonical_multi_vehicle_contract_micro_validation_v1/micro_validation_trace.jsonl`
- `D:/Sumo/sumo_train/results/diagnostics/canonical_multi_vehicle_contract_micro_validation_v1/micro_validation_report.md`

