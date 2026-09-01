# Targeted Safety-Verifier Validation

## Scope

This is a deterministic unit-level validation of
`src/safety/safety_verifier.py`. It does not run SUMO, call a provider, change
the verifier, or amend frozen Phase 1 or Phase 2 evidence. It is not part of
the frozen `release_evidence/manifest.json` package.

## Results

| Case | Input condition | Expected behaviour | Observed behaviour | Status |
| --- | --- | --- | --- | --- |
| 1. Conflicting pair | `N_S` and `E_W` both `PROCEED`, close TTI | Earliest TTI proceeds; other is `WAIT` | Matched; both flagged `route_conflict` | PASS |
| 2. Outside-zone proceed | Outside vehicle proposes `PROCEED` | Downgrade to `FREE` | `FREE`, no conflict | PASS |
| 3. Compatible pair | Opposite straight `N_S` and `S_N` both `PROCEED` | Preserve both proposals | Both remained `PROCEED`, no conflict | PASS |
| 4. Time-separated conflict | Conflicting routes with TTI 1.0 and 10.0 | Preserve both under the current TTI threshold rule | Both remained `PROCEED`, no conflict | PASS |
| 5. Three-way conflict | Three close-TTI conflicting `PROCEED` proposals | Preserve earliest TTI and override the other two | Earliest remained `PROCEED`; other two became `WAIT` | PASS |
| 6. Inside-zone `FREE` | Inside vehicle proposes `FREE` | Downgrade to `WAIT` | `WAIT`, no conflict | PASS |
| 7. Outside-zone `FREE` | Outside vehicle proposes `FREE` | Preserve `FREE` | `FREE`, no conflict | PASS |
| 8. Missing action | Inside vehicle has no raw decision | Apply default `WAIT` | `WAIT`, no conflict | PASS |
| 9. Unknown route string | Valid and unknown-route vehicles both `PROCEED` | Current route contract treats unknown route as conflicting | Valid earliest vehicle proceeded; unknown route became `WAIT` and both were `route_conflict` | PASS |
| 10. Malformed state | Required `inside_control_zone` field omitted | Raise the current contract error | `KeyError('inside_control_zone')` | PASS |

## Interpretation

The state-level verifier preserves compatible and TTI-separated proposals,
overrides non-priority close-TTI route conflicts, and applies its documented
zone/default transformations. A malformed state is not normalised: the current
contract raises `KeyError`. An unknown route string is conservatively treated as
a route conflict rather than rejected as an input exception.

## Scope Limitation

Passing these ten deterministic unit cases does **not** establish general,
real-world, trajectory-level, perception-aware, communication-aware, or
deployment safety. They do not demonstrate collision avoidance under SUMO or
real traffic, nor quantify the empirical contribution of the final verifier.
