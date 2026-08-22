# Phase 2 Route Semantics Report

## Scope

This step implemented the minimum foundation for mixed vehicle route intentions without introducing candidate groups, a deterministic cooperative comparator, or a new LLM contract.

## Existing Network Capability

The SUMO network already supports all three movement classes at the central junction:

- LEFT
- STRAIGHT
- RIGHT

This is supported by the actual `connection` entries in `net.net.xml` for the four approaches `N`, `E`, `S`, and `W`.

## Route Catalog Before / After

### Before

The repository route catalog only exposed the four straight routes:

- `N_S`
- `S_N`
- `E_W`
- `W_E`

### After

The route catalog now supports all 12 legal local movement routes:

- `N_S`
- `N_W`
- `N_E`
- `E_N`
- `E_W`
- `E_S`
- `S_E`
- `S_N`
- `S_W`
- `W_S`
- `W_E`
- `W_N`

## Edge Pair -> Movement Mapping

The deterministic mapping is derived from the actual network topology and the `dir` attribute in `net.net.xml`.

- `N -> -S` => `STRAIGHT`
- `N -> -W` => `RIGHT`
- `N -> -E` => `LEFT`
- `E -> -W` => `STRAIGHT`
- `E -> -N` => `RIGHT`
- `E -> -S` => `LEFT`
- `S -> -N` => `STRAIGHT`
- `S -> -E` => `RIGHT`
- `S -> -W` => `LEFT`
- `W -> -E` => `STRAIGHT`
- `W -> -S` => `RIGHT`
- `W -> -N` => `LEFT`

## Privacy-Minimised Local Intention Definition

Traffic state now exposes the following local, non-route-history fields:

- `route_id`
- `incoming_edge`
- `outgoing_edge`
- `movement`

The implementation does not expose:

- full navigation route
- origin/destination history
- downstream route history
- any additional path information beyond the immediate intersection movement

Backward compatibility with Phase 1 fields is preserved.

## Files Changed

Source:

- `src/safety/route_semantics.py`
- `src/experiments/scenario_generator.py`
- `src/common/metrics.py`
- `src/common/state.py`
- `src/common/logging_schema.py`
- `common.py`
- `src/controllers/decision_pipeline.py`
- `config/experiment_matrix.yaml`
- `routes.xml`

Tests:

- `tests/test_route_semantics.py`
- `tests/test_metrics.py`
- `tests/test_common_credentials.py`

## Tests

Unit tests:

- `111 passed`

Focused checks added for:

- deterministic movement mapping
- explicit failure on invalid route / edge pairs
- route catalog coverage for all 12 legal routes
- scenario generation against a mixed-turn density
- record persistence of `incoming_edge`, `outgoing_edge`, and `movement`

## SUMO Smoke Result

A minimal smoke scenario was executed with three vehicles and deterministic route coverage for:

- `LEFT`
- `STRAIGHT`
- `RIGHT`

Observed result:

- SUMO completed successfully
- no invalid-route error occurred
- no invalid-lane error occurred
- no unexpected teleport was observed in the run output
- result and provenance records retained `route_id`, `incoming_edge`, `outgoing_edge`, and `movement`

Smoke run identifier:

- `PHASE2_ROUTE_SEMANTICS_SMOKE_v3_seed8_mock`

## Phase 1 Regression Status

Phase 1 behavior remained intact:

- existing 4-vehicle straight-only scenarios still work
- existing controller entrypoints still work
- `PROCEED / WAIT / FREE` remains unchanged
- parser, provider, fallback, cooperative postprocessor, and safety verifier were not redesigned
- unit tests passed after the change set

## Limitations

- The conflict matrix is still Phase 1 scoped.
- Safe candidate passage groups are not implemented yet.
- The deterministic cooperative comparator is not implemented yet.
- The LLM response contract was not changed yet.
- The new mixed-turn density is a foundation for later Phase 2 work, not the final experimental design.

## Deferred To The Next Step

The next implementation step should add:

- deterministic candidate-group generation
- a deterministic cooperative comparator
- compatibility-aware postprocessing over mixed-turn groups
- then, only after that, any LLM-facing candidate selection logic
