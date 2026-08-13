# Formal Prompt Audit

## Status Note

This audit documented the prompt state before the final prompt-development batch completed.

The current canonical prompt selection supersedes the earlier audit conclusion:

- selected canonical prompt: `P1_BASELINE`
- canonical prompt specification: `docs/research/canonical_prompt_specification.md`
- canonical prompt selection report: `docs/research/canonical_prompt_selection_report.md`

## 1. Objective

Assess whether the current formal-experiment prompt is already suitable as a frozen prompt for the dissertation formal experiment.

This audit does **not** modify the prompt, prompt builder, parser, model, controller, safety logic, or postprocessor.

## 2. Canonical Prompt Reconstruction

### Prompt builder location

- `src/llm/prompt_builder.py`

### Real formal prompt used by the live controllers

The formal prompt is built by `build_structured_prompt(...)` and sent as the user message to the live provider.

Its effective instruction set is:

- the model is a centralized autonomous intersection decision module
- use the structured vehicle state and route conflict matrix
- safety comes first, but avoid unnecessary waiting
- vehicles outside the control zone must be `FREE`
- for vehicles inside the control zone, prefer `PROCEED` when routes are compatible with the priority vehicle
- multiple compatible vehicles may `PROCEED` together
- use `WAIT` only for genuine route conflicts or to yield to a conflicting priority flow
- minimize unnecessary waiting while keeping the intersection safe
- return JSON only

### Dynamic prompt inputs

The prompt is assembled from three live inputs:

- `route_conflicts` from `validate_conflict_matrix()`
- `policy_hints` from the current traffic state
- `traffic_state` from the live SUMO vehicle snapshot

### Policy-hint fields included

The `policy_hints` object contains:

- `priority_vehicle_id`
- `priority_route_id`
- `controlled_vehicle_count`
- `compatible_routes_with_priority`

### Traffic-state fields included

The live vehicle-state payload includes:

- `vehicle_id`
- `route_id`
- `speed`
- `distance_to_intersection`
- `time_to_intersection`
- `inside_control_zone`

## 3. Prompt Inputs

### Information sufficiency

The prompt provides the model with the information needed for high-level cooperative intersection control:

- current vehicle identity
- current route
- current speed
- current distance to intersection
- current estimated time to intersection
- current control-zone membership
- route compatibility information
- priority-vehicle hint

### Sufficiency judgment

**Sufficient**

Reason:

- the model can infer which vehicles are eligible to act
- the model can reason about priority flow and compatible flow
- the model can decide between `PROCEED`, `WAIT`, and `FREE`

### What is intentionally not included

The prompt does **not** include:

- raw controller outputs from other controllers
- final safety verdicts
- hidden internal postprocessor results
- natural-language justification prompts
- chain-of-thought instructions

That omission is desirable for a frozen formal experiment prompt.

## 4. Prompt Outputs

### Required decision contract

The formal prompt is aligned with the repository's decision space:

- `PROCEED`
- `WAIT`
- `FREE`

### Output shape

The prompt requires:

- JSON-only output

### Compatibility judgment

**Compatible**

Reason:

- the parser accepts JSON-based outputs and supported extracted shapes
- the live diagnostic already showed successful parsing of real Groq JSON and markdown-wrapped JSON responses

## 5. Information Leakage

### Leakage check

The prompt does **not** directly leak:

- rule-based controller answers
- cooperative postprocessor outputs
- safety verifier outputs
- final decisions from other controllers
- private API material

### What it does expose

The prompt deliberately exposes:

- a priority vehicle hint
- compatible-route hints
- the control-zone status of each vehicle
- the route conflict matrix

These are not accidental leaks; they are part of the research method.

### Leakage judgment

**No disallowed leakage detected**

### Caution

The prompt does contain a throughput-biased instruction set:

- "do not overuse WAIT"
- "minimize unnecessary waiting"

This is an instruction bias, not a hidden leakage of another controller's answer.

## 6. Controller Fairness

### Same prompt across controllers

The raw, hybrid, and hybrid+safety controllers all call the same structured prompt builder in the shared decision pipeline.

Therefore the prompt content is the same for all live LLM-bearing controllers, aside from the live vehicle-state snapshot and the corresponding policy hints.

### Fairness judgment

**Fair**

Reason:

- prompt logic is shared
- controller-specific differences occur after the prompt, in later pipeline stages
- no controller-specific prompt rewrite is present in the repository

### Difference classification

- Method differences:
  - validation stage
  - cooperative postprocessing
  - safety verification
- Engineering differences:
  - stage mode selection
  - logging scope
  - controller wrappers

## 7. Parser Compatibility

### Prompt-parser alignment

The prompt asks for JSON-only output and the parser supports real-world JSON-based Groq responses.

The live parser diagnostic demonstrated that the current parser can successfully handle:

- JSON
- markdown-wrapped JSON

### Compatibility judgment

**Aligned**

### Important note

The prompt does not lock the model into a single rigid JSON schema, but the parser is already compatible with the accepted output forms observed in live use.

## 8. Prompt Complexity

### Complexity judgment

**Moderate**

### Reasons

The prompt is not overly long, but it does include:

- a general role statement
- high-level cooperative guidance
- safety guidance
- a priority-flow hint
- a route-conflict matrix
- a per-vehicle traffic-state payload

### Complexity risks

- repeated information between policy hints and the vehicle snapshot
- throughput-biased instruction language
- slightly higher token cost than a minimal prompt

### Complexity benefit

The prompt remains understandable and structured, which is preferable for a frozen formal experiment prompt.

## 9. Prompt Responsibilities

### What the prompt should do

The prompt is responsible for asking the LLM to make a high-level cooperative traffic decision.

### What the prompt should not do

The prompt is **not** responsible for:

- safety enforcement
- collision checking
- trajectory planning
- rule-engine execution
- postprocessing logic

### Responsibility separation judgment

**Clear**

Reason:

- the prompt asks for high-level decision support
- the actual safety and rule enforcement are implemented later in the pipeline

## 10. Threats To Validity

### Identified threats

- prompt bias toward throughput
- instruction bias toward `PROCEED` / reduced `WAIT`
- formatting bias from JSON-only instruction
- controller bias if later pipeline stages differ
- leakage risk from policy hints if overinterpreted as ground truth

### Impact on formal experiment

These threats are real, but they do not make the prompt unusable.

They should be reported as validity threats, not treated as reasons to redesign the method at this stage.

## 11. Prompt Freeze Recommendation

### Recommendation

**Freeze the current prompt for the formal experiment.**

### Why

- it matches the frozen research design
- it is shared across raw / hybrid / safety controller paths
- it is already aligned with the parser
- it supplies the necessary control context without exposing hidden controller outputs
- it is sufficiently specific for cooperative decision-making

### What should happen next

Use the current prompt as the canonical prompt for formal experiment execution.

Do not change it unless a genuine bug is discovered that makes the prompt invalid for parsing or execution.

## 12. Research Impact

### If the prompt is kept unchanged

- the research method remains stable
- the formal experiment can proceed with a frozen prompt
- any differences across controllers can be attributed to later pipeline stages rather than prompt drift

### If the prompt were changed

- the dissertation method would become less stable
- the formal comparison would lose traceability
- the results would need re-justification

## 13. Final Verdict

**PROMPT_FIT_FOR_FORMAL_EXPERIMENT**

## 14. Evidence Path

- `src/llm/prompt_builder.py`
- `src/controllers/decision_pipeline.py`
- `src/controllers/raw_llm_controller.py`
- `src/controllers/hybrid_llm_controller.py`
- `src/controllers/hybrid_llm_safety_controller.py`
- `results/diagnostics/llm_parser_diagnostic/`
