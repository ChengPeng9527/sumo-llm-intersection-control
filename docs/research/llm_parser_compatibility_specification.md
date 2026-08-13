# LLM Parser Compatibility Specification

## 1. Purpose

This document defines the only allowed compatibility standard for future parser compatibility work in the canonical dissertation repository.

Scope:

- parser input compatibility
- output-shape classification
- ambiguity handling
- fallback rules

Out of scope:

- prompt redesign
- method redesign
- controller strategy changes
- new decision semantics
- new vehicle actions

## 2. Evidence Basis

This specification is derived from:

- `docs/research/llm_parser_failure_audit.md`
- `docs/research/current_research_status.md`
- `results/diagnostics/llm_parser_diagnostic/`
- `src/llm/response_parser.py`
- `src/llm/prompt_builder.py`
- `src/controllers/decision_pipeline.py`

Observed evidence summary:

- canonical pilot completed with 4 controllers and fallback-dominated LLM paths
- live diagnostic confirmed Groq returned JSON-formatted responses
- live diagnostic confirmed one parser compatibility gap:
  - `TOP_LEVEL_JSON_LIST_WAS_COLLAPSED_TO_OBJECT`

## 3. Canonical Decision Space

The only legal semantic decisions are:

- `PROCEED`
- `WAIT`
- `FREE`

Rules:

- case-insensitive input is allowed
- leading and trailing whitespace is ignored
- no new action tokens are allowed
- no expansion of the decision set is allowed

Any extracted action outside this set must be rejected and treated as fallback.

## 4. Canonical Output Shapes

The following output shapes are recognized by this specification.

### 4.1 Pure action

Examples:

- `PROCEED`
- `WAIT`
- `FREE`

Status:

- `SUPPORTED`

Reason:

- no structural extraction is needed beyond trimming and case normalization

### 4.2 Action embedded in short prose

Examples:

- `Decision: PROCEED`
- `Final decision: WAIT`
- `The vehicle should PROCEED.`

Status:

- `SUPPORTED_AFTER_EXTRACTION`

Reason:

- the action must be extracted from surrounding text before normalization

### 4.3 Markdown wrapped action or JSON

Examples:

- `**PROCEED**`
- ```json
  {"action":"PROCEED"}
  ```

Status:

- `SUPPORTED_AFTER_EXTRACTION`

Reason:

- formatting must be stripped before extracting the action

### 4.4 Top-level JSON object

Examples:

- `{"action":"PROCEED"}`
- `{"decision":"WAIT"}`
- `{"decisions":{"car0":"PROCEED"}}`

Status:

- `SUPPORTED_AFTER_EXTRACTION`

Reason:

- JSON must be parsed first, then the action slot must be resolved

### 4.5 Top-level JSON list

Examples:

```json
[
  {
    "vehicle_id": "car0",
    "action": "PROCEED"
  }
]
```

Status:

- `SUPPORTED_AFTER_EXTRACTION`

Reason:

- list items must be reduced to a unique current-vehicle decision

### 4.6 Vehicle-id dict

Examples:

```json
{
  "car0": "PROCEED",
  "car1": "WAIT"
}
```

Status:

- `SUPPORTED_AFTER_EXTRACTION`

Reason:

- each current vehicle id can be mapped directly to one action

### 4.7 Reasoning plus final decision

Examples:

- `Reasoning ... Final decision: PROCEED`
- `Reasoning ... therefore WAIT`

Status:

- `SUPPORTED_AFTER_EXTRACTION`

Reason:

- reasoning text is allowed only if one unique final action can still be extracted

### 4.8 Provider error

Examples:

- HTTP error payload
- timeout payload
- authentication error payload

Status:

- `MUST_FALLBACK`

Reason:

- no usable decision can be trusted from a provider error payload

### 4.9 Empty response

Examples:

- empty string
- whitespace only

Status:

- `MUST_FALLBACK`

Reason:

- no decision is present

### 4.10 Malformed JSON

Examples:

- truncated JSON
- invalid JSON syntax

Status:

- `MUST_FALLBACK`

Reason:

- structural parsing failed

## 5. Compatibility Matrix

| Output shape | Status | Notes |
| --- | --- | --- |
| Pure action | `SUPPORTED` | Direct action token after trimming and casing |
| Action in prose | `SUPPORTED_AFTER_EXTRACTION` | Requires extraction from surrounding text |
| Markdown wrapped action | `SUPPORTED_AFTER_EXTRACTION` | Requires markup removal |
| Top-level JSON object | `SUPPORTED_AFTER_EXTRACTION` | Requires JSON parsing and field resolution |
| Top-level JSON list | `SUPPORTED_AFTER_EXTRACTION` | Requires list-to-decision reduction |
| Vehicle-id dict | `SUPPORTED_AFTER_EXTRACTION` | Requires mapping current vehicle ids to actions |
| Reasoning plus final decision | `SUPPORTED_AFTER_EXTRACTION` | Reasoning is ignored; final decision is used |
| Provider error | `MUST_FALLBACK` | No decision extraction is allowed |
| Empty response | `MUST_FALLBACK` | No decision is present |
| Malformed JSON | `MUST_FALLBACK` | Structural parsing failed |
| Multiple conflicting actions | `MUST_FALLBACK` | Ambiguous, do not guess |
| Missing decision slot | `MUST_FALLBACK` | Ambiguous, do not guess |

## 6. Ambiguity Rules

Fallback is mandatory when any of the following happens:

1. Two or more different valid actions are present for the same current vehicle.
2. The response contains both `PROCEED` and `WAIT` as candidate final outcomes and no unique final action can be proven.
3. The response contains a list or object but no unique decision slot can be resolved.
4. The response omits the required decision field for the current vehicle.
5. The response contains only reasoning and no unique final action.
6. The response mentions unknown vehicles and the current vehicle mapping cannot be constructed unambiguously.
7. The response is semantically inconsistent with itself.

Non-ambiguity rule:

- the parser must never guess a missing action
- the parser must never invent a decision from reasoning alone
- if one unique current-vehicle decision cannot be proven, fallback is required

## 7. Vehicle Matching Rules

For multi-vehicle responses:

- only current controlled vehicle ids may be accepted
- unknown vehicle ids must not be guessed or remapped
- each current vehicle must map to one and only one legal action
- if one current vehicle is unresolved, the response is not fully compatible

## 8. Field Rules

Canonical action field:

- `action`

Compatibility alias:

- `decision`

Rules:

- `action` is preferred
- `decision` may be accepted as a legacy alias only if it maps unambiguously to one current vehicle action
- a response that has neither `action` nor `decision` is not compatible

## 9. Practical Acceptance Policy

Accept immediately:

- pure action
- clearly extractable final action
- JSON or markdown that collapses to one legal action per current vehicle without ambiguity

Fallback immediately:

- provider error
- empty response
- malformed JSON
- multiple conflicting actions
- missing action slot
- any response that would require guessing

## 10. Relationship To Current Evidence

The live diagnostic evidence shows:

- Groq can return valid JSON responses
- some responses are top-level JSON lists
- the current compatibility gap is real and independently evidenced

Therefore:

- the future parser compatibility patch must support top-level JSON list reduction
- the future parser compatibility patch must not broaden the decision space
- the future parser compatibility patch must preserve fallback for ambiguity

## 11. Non-Goals

This specification does not:

- change the prompt
- change the LLM model
- change the controller strategy
- change the cooperative postprocessor
- change the safety logic
- introduce any new action semantics

