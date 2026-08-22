# Fallback vs Rule-Based Semantics Audit

## Scope
This audit compares the deterministic rule-based controller with the deterministic fallback policy used by the LLM pipeline. It is limited to implementation semantics and trace implications. No dissertation prose or experimental outputs are modified here.

## Key Finding
The fallback policy is not equivalent to the rule-based baseline. It is materially more permissive and uses a different priority heuristic.

## Evidence in Repository

### Rule-based baseline
- File: `src/controllers/baseline_controller.py`
- Priority selection:
  - chooses the vehicle with the minimum `distance_to_center` among vehicles inside the control zone
- Decision policy:
  - vehicles outside the control zone: `FREE`
  - priority vehicle: `PROCEED`
  - all other controlled vehicles: `WAIT`

### Deterministic fallback policy
- File: `src/llm/fallback_policy.py`
- Priority selection:
  - chooses the vehicle with the minimum `time_to_intersection` among controlled vehicles
- Decision policy:
  - vehicles outside the control zone: `FREE`
  - priority vehicle: `PROCEED`
  - vehicles with a route compatible with the priority route: `PROCEED`
  - all remaining controlled vehicles: `WAIT`

### Cooperative post-processing
- File: `src/llm/postprocessor.py`
- The cooperative stage uses the same compatibility logic as the fallback policy and promotes compatible waiting vehicles to `PROCEED`.
- The interface rule still forces vehicles outside the control zone to `FREE`.

### Safety verifier
- File: `src/safety/safety_verifier.py`
- The safety verifier only downgrades unsafe or conflicting decisions.
- It does not create a new traffic advantage beyond the permissive fallback/cooperative logic already present upstream.

## Semantic Difference
The fallback policy:
- uses `time_to_intersection` instead of `distance_to_center`
- allows compatible-route vehicles to proceed

The rule-based baseline:
- uses `distance_to_center`
- blocks all non-priority controlled vehicles with `WAIT`

This means the fallback policy can achieve better throughput or lower waiting time even without any live provider contribution.

## Implication for Attribution
Any traffic advantage observed in the full LLM-assisted pipeline can be partly or largely explained by the deterministic fallback path alone. The rule-based baseline is a stricter controller and is not the correct semantic comparator for "LLM success" attribution.

## Confidence
High. The implementation differences are explicit in the source code and consistent across the pipeline.

