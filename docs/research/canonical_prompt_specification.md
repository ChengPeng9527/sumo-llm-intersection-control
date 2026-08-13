# Canonical Prompt Specification

## 1. Prompt ID

`P1_BASELINE`

## 2. Full Frozen Prompt

The selected canonical prompt is the prompt currently produced by `build_structured_prompt(...)` after prompt development and selection.

Frozen template:

```text
You are a centralized autonomous intersection decision module.
Follow the canonical output contract exactly.

Output contract:
Return exactly one JSON object with this shape:
{
  "decisions": {
    "<vehicle_id>": "PROCEED|WAIT|FREE"
  }
}
Rules:
- Use the exact vehicle_id values from Traffic state. Do not invent, rename, duplicate, or omit ids.
- Include exactly one decision for every vehicle in Traffic state.
- Vehicles outside the control zone must be FREE.
- Vehicles inside the control zone must use only PROCEED, WAIT, or FREE.
- No markdown, prose, comments, or reasoning.

Route conflict matrix:
{route_conflicts}

Policy hints:
{policy_hints}

Traffic state:
{traffic_state}
```

## 3. Input Fields

The canonical prompt accepts three live inputs:

- `route_conflicts`
- `policy_hints`
- `traffic_state`

### 3.1 Route conflict matrix

The route-conflict input is produced from the repository's frozen route-compatibility definition.

### 3.2 Policy hints

The policy hints are derived from the live traffic state and may include:

- priority vehicle id
- priority route id
- controlled vehicle count
- compatible routes with the priority flow

### 3.3 Traffic state

The traffic-state payload includes the current vehicle snapshot used by the live controllers.

## 4. Output Contract

The model must return JSON only.

Canonical shape:

```json
{
  "decisions": {
    "<vehicle_id>": "PROCEED | WAIT | FREE"
  }
}
```

Rules:

- Use exact `vehicle_id` values from `traffic_state`.
- Do not invent, rename, duplicate, or omit vehicle ids.
- Include exactly one decision for every vehicle in `traffic_state`.
- Vehicles outside the control zone must be `FREE`.
- Vehicles inside the control zone must use only `PROCEED`, `WAIT`, or `FREE`.
- No markdown, prose, comments, or reasoning.

## 5. Decision Space

The canonical prompt supports only the frozen dissertation decision space:

- `PROCEED`
- `WAIT`
- `FREE`

## 6. LLM Responsibility

The LLM is responsible only for:

- high-level cooperative decision recommendation

The LLM is not responsible for:

- low-level control
- trajectory generation
- collision checking
- deterministic safety verification
- SUMO commands
- rule-engine execution
- postprocessor execution

## 7. Explicit Exclusions

The canonical prompt does not ask the model to reproduce or anticipate:

- rule-based controller answers
- cooperative postprocessor outputs
- deterministic safety-verifier outputs
- other controllers' final decisions
- hidden implementation details

## 8. Development Evidence

Prompt development was performed with:

- `3` candidate prompts
- `3` development seeds: `101`, `202`, `303`
- `4` vehicles
- counterbalanced prompt order across the 3 seeds
- `9` valid development runs

Observed selection evidence:

- `P1_BASELINE`: `198` live requests, `2` successful requests, `196` fallback decisions, `1.0101%` provider success, `1.0101%` parser success
- `P2_STRUCTURED`: `198` live requests, `0` successful requests, `198` fallback decisions, `0%` provider success, `0%` parser success
- `P3_COOPERATIVE_OBJECTIVE`: `198` live requests, `0` successful requests, `198` fallback decisions, `0%` provider success, `0%` parser success

## 9. Selection Rationale

`P1_BASELINE` was selected because:

1. It was the only candidate with non-zero live-provider success.
2. It was the only candidate with non-zero parser success.
3. All three candidates had the same completion rate in the development dataset.
4. All three candidates had the same mean waiting time in the development dataset.
5. `P1_BASELINE` is the simplest reliable prompt, which is preferred when reliability is otherwise equal or close.

`P2_STRUCTURED` and `P3_COOPERATIVE_OBJECTIVE` were rejected because they collapsed to fallback-only behavior in the development batch.

## 10. Known Limitations

- Provider reliability in the development batch was modest overall.
- The prompt-selection batch is engineering evidence, not the formal experiment.
- The canonical prompt should remain frozen for all future LLM-bearing formal experiments.

## 11. Freeze Statement

From this point onward, the formal experiment must use this canonical prompt unchanged.

If the prompt changes, all LLM-bearing formal experiment runs must be rerun.

## 12. Freeze Confirmation

The canonical prompt is frozen for formal experiment use.

## 13. Final Revalidation Confirmation

The canonical prompt was revalidated under the frozen max_completion_tokens = 256 request budget.

The final counterbalanced prompt-selection batch remained consistent with the original freeze decision:

- selected prompt: P1_BASELINE
- final verdict: CANONICAL_PROMPT_SELECTED_READY_TO_FREEZE

This revalidation did not change the prompt semantics, decision space, controller strategy, or safety logic.
