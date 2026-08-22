# Minimal Discriminative Experiment Design

## 1. Why 4V Seed1 Was Not Discriminative Enough

The canonical Gemini prompt already encodes much of the deterministic fallback structure:

- control-zone gating,
- route conflict information,
- policy hints including priority vehicle and compatible routes,
- and a restricted output vocabulary of `PROCEED`, `WAIT`, and `FREE`.

Relevant evidence:

- [prompt builder](D:\Sumo\sumo_train\src\llm\prompt_builder.py)
- [decision pipeline](D:\Sumo\sumo_train\src\controllers\decision_pipeline.py)
- [fallback controller](D:\Sumo\sumo_train\llm_ready_controller.py)
- [fallback controller](D:\Sumo\sumo_train\modular_controller.py)
- [route conflict matrix](D:\Sumo\sumo_train\config\route_conflicts.yaml)
- [existing discriminative-state audit](D:\Sumo\sumo_train\docs\research\llm_fallback_discriminative_state_audit.md)

The 4V seed1 trace does contain mixed route-group states, but Gemini still matched fallback exactly on every comparable row. So the issue is not simply that no complex states existed. The stronger explanation is that the prompt and fallback semantics occupy nearly the same decision surface.

## 2. What Counts as a Genuinely Discriminative State

A state is high-discriminative only if all of the following hold:

- at least 2 vehicles are simultaneously inside the control zone,
- at least one route conflict exists,
- `FREE` is not already determined by outside-control-zone gating,
- more than one action assignment is plausibly defensible,
- the fallback priority rule must actually resolve competing actions.

In practice, that means a good probe state should force a real choice between `PROCEED` and `WAIT`, not just a trivial `FREE` assignment.

## 3. Existing Trace Search Result

The current canonical 4V seed1 live trace already provides 11 such mixed route-group steps:

- steps 14 through 24,
- 39 comparable vehicle-row decisions in total,
- 2 or 3 controlled vehicles per state,
- mixed `N_S` / `W_E` route groups, plus an `S_N` entrant at step 24,
- one near-tie case around step 19 where two `W_E` vehicles have very similar time-to-intersection.

These are enough to form a minimal observed probe set without inventing new SUMO traffic.

## 4. Offline Probe Result

The selected existing states were replayed as an offline comparison between the live Gemini decisions and the fallback-only trace.

Summary:

- selected states: 11
- selected vehicle-row comparisons: 39
- Gemini raw vs fallback agreement: 39 / 39 = 100%
- Gemini final vs fallback agreement: 39 / 39 = 100%
- provider success on selected rows: 39 / 39 = 100%
- parser success on selected rows: 39 / 39 = 100%

Representative state pattern:

- `N_S` vehicle inside the control zone received `WAIT`.
- `W_E` vehicle inside the control zone received `PROCEED`.
- outside-control-zone vehicles received `FREE`.

That pattern is repeated identically in both systems.

## 5. Agreement Matrix

| Gemini raw | Fallback | Count |
|---|---:|---:|
| FREE | FREE | 12 |
| PROCEED | PROCEED | 15 |
| WAIT | WAIT | 12 |

This is a perfect diagonal on the selected high-discriminative probe set.

## 6. Interpretation

The evidence supports the following interpretation:

- the prompt and fallback are semantically very close,
- the observed 4V seed1 states are not enough to force different decisions,
- Gemini does not show a distinct behavioural policy on the available high-discriminative states,
- and there is no evidence that downstream correction is hiding a divergence.

The model looks like it is executing a natural-language encoding of the deterministic heuristic rather than independently discovering an alternative policy.

## 7. Is a New SUMO Experiment Scientifically Justified?

Not yet.

Because the selected high-discriminative states already yield 100% agreement, a larger formal matrix would mostly re-measure the same policy surface. That would add runtime but very little identification power.

A new SUMO experiment becomes justified only if one of the following changes:

- the prompt is made less isomorphic to the fallback heuristic,
- the scenario is extended to create more competing WAIT / PROCEED options,
- or a deliberately adversarial conflict configuration is introduced.

## 8. Smallest Useful Experiment, If One Must Be Run Later

If a follow-up is eventually needed, the smallest useful design is a 3-state probe rather than a full matrix:

1. two-vehicle cross-axis conflict with one clear priority vehicle,
2. three-vehicle mixed conflict with one compatible pair and one incompatible vehicle,
3. near-tie priority state where two controlled vehicles have almost identical time-to-intersection.

But under the current evidence, even this is optional rather than mandatory.

## 9. Final Verdict

`LLM_EFFECTIVELY_REPRODUCES_FALLBACK_POLICY`

This is supported by:

- 11 observed mixed route-group states in the canonical 4V seed1 trace,
- 39 / 39 agreement on the selected high-discriminative probe rows,
- and the strong semantic overlap between the prompt and fallback logic.
