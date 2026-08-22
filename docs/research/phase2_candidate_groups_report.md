# Phase 2 Step 3 Candidate Groups Report

## What changed

- Added deterministic mixed-turn conflict reasoning in `src/safety/route_conflict.py`.
- Added safe candidate passage-group generation in `src/safety/candidate_groups.py`.
- Added focused tests for conflict rules and candidate groups.
- Kept `docs/dissertation/` untouched.

## Conflict representation

- Route semantics continue to be resolved through the Step 2 route-semantic layer.
- The Step 3 conflict model stays route-based, not vehicle-ID-based.
- Compatibility now distinguishes:
  - opposite straight movements
  - right-turn movements across distinct approaches
  - opposite left-turn movements
- Everything else is treated as conflicting.

## Candidate generation rule

- Only vehicles inside the control zone are considered relevant.
- Only vehicles with resolvable mixed-turn route semantics participate.
- Candidate groups are built deterministically from sorted vehicle state.
- Every candidate group is checked pairwise.
- Single-vehicle candidates are included when relevant vehicles exist.
- Multi-vehicle candidates are only emitted when all internal pairs are conflict-free.

## Files changed

- `src/safety/route_conflict.py`
- `src/safety/candidate_groups.py`
- `tests/test_route_conflicts.py`
- `tests/test_candidate_groups.py`

## Tests executed

- Manual harness executed 32 assertions across:
  - `tests.test_route_conflicts`
  - `tests.test_candidate_groups`
  - `tests.test_safety_verifier`
  - `tests.test_llm_postprocessor`
  - `tests.test_decision_pipeline`
- Result: 32 passed, 0 failed.

## Mechanism demonstration

- Demonstration state included mixed RIGHT, STRAIGHT, and LEFT intentions.
- Example compatible pairs:
  - `N_W` with `E_N`
  - `N_S` with `S_N`
- Example conflicting pairs:
  - `N_E` with `N_W`
  - `N_E` with `N_S`
- Generated candidate groups:
  - singletons for each relevant vehicle
  - `['veh_1', 'veh_2']`
  - `['veh_3', 'veh_4']`

## Known limitations

- This step does not choose the best candidate group.
- The LLM planner/selector is still deferred.
- The deterministic safety verifier remains final authority.

## Deferred improvements

- Candidate selection and ranking
- Deterministic cooperative comparator
- Fairness analysis
- LLM prompt integration for candidate groups
