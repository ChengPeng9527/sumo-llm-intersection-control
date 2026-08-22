# LLM Fallback Discriminative State Audit

## 1. Research Question

Why did the genuine live Gemini Raw LLM 4V seed1 pilot produce exactly the same traffic behaviour as the fallback-only 4V seed1 run?

The audit checks whether the answer is primarily:

- prompt and fallback semantics are effectively equivalent,
- the current scenario does not expose enough discriminative states,
- provider/parser reliability or downstream processing altered the evidence,
- or some combination of these factors.

## 2. Fallback Semantics

The fallback path is a deterministic local controller. Its behaviour is driven by:

- whether a vehicle is inside the control zone,
- the nearest / priority vehicle selection rule,
- route-group compatibility,
- and TTC-style safety filtering.

At a high level, the fallback logic behaves as follows:

- vehicles outside the control zone are assigned `FREE`,
- the priority vehicle is selected from the controlled set using minimum distance / time-to-intersection,
- vehicles in the active compatible group are assigned `PROCEED`,
- incompatible vehicles are assigned `WAIT`,
- a safety filter can override non-priority decisions to `WAIT`.

This means the fallback is already a structured decision rule over the same traffic state features that the LLM sees.

## 3. Gemini Prompt Semantics

The canonical structured prompt is not open-ended natural language. It explicitly includes:

- route conflict information,
- policy hints,
- traffic state,
- and a restricted output contract with only `PROCEED`, `WAIT`, and `FREE`.

The prompt builder and decision pipeline expose the same key ingredients that the fallback uses:

- `route_conflicts`,
- `priority_vehicle_id`,
- `priority_route_id`,
- `controlled_vehicle_count`,
- `compatible_routes_with_priority`.

This means the Gemini prompt is not asking the model to invent a new policy from scratch. It is being asked to emit a structured decision inside a narrow semantic box that already encodes the local rule structure.

## 4. Prompt-Fallback Semantic Overlap

The overlap is substantial.

Both systems use:

- control-zone gating,
- a priority vehicle notion,
- route compatibility / conflict logic,
- and a restricted action set.

The main difference is implementation style:

- the fallback computes the action directly,
- Gemini receives a prompt that already encodes the same policy cues and then returns the same action space.

This is a strong reason to expect convergence even when the model is live and successful.

## 5. Existing-State Dataset Sources

This audit used the following existing artifacts:

- `results/raw/GEMINI_RAW_LLM_4V_S1_PILOT_v4_seed1_gemini5_real/step_records.csv`
- `results/raw/FB_ONLY_v4_seed1_mock/step_records.csv`
- `results/raw/FE01_RULE_BASED_v4_seed1/step_records.csv`
- associated `events.jsonl` and run metadata in the same result folders

These are the relevant state sources because they record the aligned decision rows used for the Gemini vs fallback comparison.

## 6. State Difficulty Definition

For the purpose of this audit, a state is more discriminative if it provides a realistic chance for Gemini and fallback to choose different actions.

Useful indicators of discriminative difficulty are:

- simultaneously controlled vehicles,
- mixed route compatibility,
- conflicting route groups,
- and non-trivial WAIT/PROCEED trade-offs.

A state is weakly discriminative if:

- the vehicle is outside the control zone,
- only one obvious safe action exists,
- or the prompt already exposes a policy structure that mirrors the fallback rule.

## 7. Selected States

The aligned Gemini and fallback-only 4V seed1 trace contained:

- 132 comparable decision rows,
- 82 controlled-zone rows,
- 50 outside-control-zone rows,
- 44 controlled steps,
- 34 steps with 2 or more simultaneously controlled vehicles,
- maximum of 3 simultaneously controlled vehicles in one step.

Representative aligned states observed in the trace:

- outside control zone: both systems returned `FREE`,
- inside control zone with a clear compatible action: both systems returned `PROCEED`,
- inside control zone with a non-compatible / safety-constrained action: both systems returned `WAIT`.

The trace therefore contains some multi-vehicle situations, but not enough observable cross-policy divergence to separate Gemini from fallback.

## 8. Provider and Parser Reliability

The genuine Gemini live pilot was technically stable:

- logical provider requests: 53
- provider success: 53 / 53
- parser success: 53 / 53
- fallback count: 0
- provenance complete

The fallback-only run also produced stable deterministic outputs.

Therefore the identical traffic behaviour is not explained by provider failure, parser failure, or incomplete provenance in this pilot.

## 9. Agreement Rates

Decision-level comparison between Gemini and fallback-only:

- comparable rows: 132
- raw agreement rate: 132 / 132 = 100%
- final agreement rate: 132 / 132 = 100%
- raw disagreement count: 0
- downstream-erased disagreement count: 0

This is the strongest evidence in the audit.

## 10. Agreement Matrix

### Gemini Raw vs Fallback-Only

| Gemini raw | Fallback-only | Count |
|---|---:|---:|
| FREE | FREE | 50 |
| PROCEED | PROCEED | 70 |
| WAIT | WAIT | 12 |

Agreement rate: 100%

### Gemini Final vs Fallback-Only

| Gemini final | Fallback-only | Count |
|---|---:|---:|
| FREE | FREE | 50 |
| PROCEED | PROCEED | 70 |
| WAIT | WAIT | 12 |

Agreement rate: 100%

## 11. Disagreement Examples

No disagreement examples exist in the aligned 4V seed1 decision set.

This matters because it rules out the most obvious alternative explanation:

- Gemini did not differ from fallback and then get “corrected” downstream,
- the raw Gemini output itself already matched the fallback decision stream on every comparable row.

## 12. Interpretation

The evidence supports multiple simultaneous explanations:

### A. Prompt and fallback are semantically very close

This is strongly supported.

The prompt exposes the same structural features that the fallback uses, so the model is nudged toward the same decision surface.

### B. The scenario offers limited visible discriminative power

Also supported.

Although the run contains 82 controlled-zone rows and 34 multi-vehicle steps, there were no observed route conflicts in the selected seed, and the trace still produced identical decisions throughout.

### C. Provider/parser reliability is not the cause

Not supported as an explanation.

The live Gemini run was reliable enough that the identical output cannot be blamed on provider failure, parser failure, or fallback activation.

The most defensible reading is that the current experimental design collapses Gemini and fallback onto nearly the same effective decision policy for this seed.

## 13. Implication for Experimental Design

The current 4V seed1 setup is not sufficiently discriminative for attributing traffic performance differences to Gemini decision-making.

The design implication is:

- a larger range of route-conflict states is needed,
- or a scenario with more competing WAIT / PROCEED opportunities,
- or a task formulation where the prompt does not already encode the fallback policy so closely.

Without that, live Gemini can be perfectly reliable and still fail to show unique behavioural contribution.

## 14. Recommended Next Step

Use this conclusion as a design audit, not as a code fix.

The next useful step is to identify or construct a more discriminative scenario / state set, then re-check whether Gemini and fallback remain identical when:

- route conflicts are actually exercised,
- competing controlled vehicles produce different plausible actions,
- and the prompt no longer mirrors the fallback rule so tightly.

## 15. Final Verdict

`MULTIPLE_CAUSES_IDENTIFIED`

Primary evidence:

- prompt and fallback semantics are highly overlapping,
- the seed does not expose enough observable discriminative states,
- and the raw Gemini output still matched fallback exactly on every comparable row.
