# Gemini vs Fallback Decision-Level Audit

## Scope
This audit compares the genuine-live Gemini Raw LLM 4V seed1 pilot against the fallback-only 4V seed1 pilot at the decision-row level.

Alignment key:
- `simulation_step`
- `vehicle_id`

Only comparable controlled-vehicle decision rows are analyzed.

## Evidence Sources
- [Gemini step records](/D:/Sumo/sumo_train/results/raw/GEMINI_RAW_LLM_4V_S1_PILOT_v4_seed1_gemini5_real/step_records.csv)
- [Fallback-only step records](/D:/Sumo/sumo_train/results/raw/FB_ONLY_v4_seed1_mock/step_records.csv)

## Comparable Decision Events
- Aligned rows: 132
- Gemini-controlled rows (`inside_control_zone = True`): 82
- Deterministic interface rows (`inside_control_zone = False`): 50
- Controlled simulation steps: 44
- Steps with 2+ simultaneously controlled vehicles: 34
- Maximum simultaneously controlled vehicles in one step: 3
- Route conflicts observed: 0

## Decision Pipeline Trace
For Gemini-controlled rows, the full path is visible in the trace:
- `llm_raw_decision`
- `validated_llm_decision`
- `postprocessed_decision`
- `final_decision`
- `decision_source`

For this pilot, the trace shows:
- `llm_raw_decision` = `validated_llm_decision` = `postprocessed_decision` = `final_decision`
- `decision_source` is `LLM_RAW` on 82 rows and `DETERMINISTIC_INTERFACE_RULE` on 50 rows

## Agreement Metrics
- Gemini raw vs fallback-only raw agreement rate: 1.000
- Gemini final vs fallback-only final agreement rate: 1.000
- Raw disagreement count: 0
- Final disagreement count: 0
- Disagreements erased downstream: 0

## Action Agreement Matrix
### Raw decision matrix: Gemini raw vs fallback-only
| Gemini raw \ Fallback | FREE | PROCEED | WAIT |
|---|---:|---:|---:|
| FREE | 50 | 0 | 0 |
| PROCEED | 0 | 70 | 0 |
| WAIT | 0 | 0 | 12 |

### Final decision matrix: Gemini final vs fallback-only
| Gemini final \ Fallback | FREE | PROCEED | WAIT |
|---|---:|---:|---:|
| FREE | 50 | 0 | 0 |
| PROCEED | 0 | 70 | 0 |
| WAIT | 0 | 0 | 12 |

## Representative Disagreement Examples
- None observed.
- There are no rows where Gemini raw decision differs from fallback-only raw decision after alignment on `simulation_step + vehicle_id`.
- There are no rows where Gemini final decision differs from fallback-only final decision.

## Scenario Discriminative Opportunities
This 4V seed1 scenario was not trivial:
- 82 controlled decision rows occurred across 44 steps
- 34 steps had 2 or more simultaneously controlled vehicles
- One step had 3 simultaneously controlled vehicles
- The final action set was not degenerate: `PROCEED` 70, `WAIT` 12, `FREE` 50

However, despite those opportunities, the trace still shows zero Gemini-vs-fallback disagreement at either the raw or final decision level.

## Attribution Interpretation
The evidence supports the simplest reading:
- Gemini raw behavior intrinsically matches the fallback-only policy on every aligned controlled event in this seed.
- Downstream deterministic logic does not appear to erase LLM-specific differences, because no raw differences are present to erase.
- The final traffic equivalence is therefore explained by identical row-level decisions, not by a downstream transformation of divergent Gemini outputs.

## Verdict
LLM_BEHAVIOUR_INTRINSICALLY_MATCHES_FALLBACK
