# Phase 3 Turn-Composition Post-Run Evidence Audit

## Scope

This is a read-only audit of the independently executed matched turn-composition fixed-state probe. It does not alter preregistration, raw outputs, frozen Phase 1/2/3 evidence, or classification criteria. No provider request and no SUMO run was made during this audit.

## Evidence integrity and controlled structure

The independent namespace contains a passed connectivity record, completed `run_metadata.json`, and exactly 10 raw decision records. The matrix contains two registered presentation-order conditions with five unique IDs each.

- Provider success: 10/10; parser success: 10/10; fallback: 0/10.
- Legal selected candidate: 10/10; invalid: 0/10.
- `request_attempt_count`: 1 in every record; no replacement/retry record exists.
- Sanitised raw model output and non-empty prompt hash are retained for every record.
- One order-insensitive `candidate_set_hash`, one `input_state_hash`, one generation configuration, two `candidate_presentation_hash` values, and two prompt hashes are retained, exactly as preregistered.
- Target structures remain legal and matched: `RIGHT_2` and `STRAIGHT_2` each have group size 2, individual waiting values 0 and 2 s, aggregate waiting 2 s, maximum waiting 2 s, and the matched minimum ETA. Candidate richness remains 11 legal groups in both conditions.

The deliberately retained confounds are vehicle IDs, route IDs, incoming/outgoing edges, and the associated real route identity. These are unavoidable when using real legal RIGHT and STRAIGHT candidates rather than relabelling movements synthetically.

## Replicate-level result

The selected candidate was identical in all 10 requests: the legal three-vehicle all-`RIGHT` candidate `..._2_3|..._2_1|..._2_2`, classified as `OTHER_LEGAL` because it is neither registered two-vehicle target.

| Request sequence | Target positions (RIGHT, STRAIGHT) | Selected class | Selected candidate position |
| --- | --- | --- | ---: |
| `RIGHT_TARGET_FIRST_R1`--`R5` | 8, 10 | OTHER_LEGAL, OTHER_LEGAL, OTHER_LEGAL, OTHER_LEGAL, OTHER_LEGAL | 11 |
| `STRAIGHT_TARGET_FIRST_R1`--`R5` | 10, 8 | OTHER_LEGAL, OTHER_LEGAL, OTHER_LEGAL, OTHER_LEGAL, OTHER_LEGAL | 11 |

Neither first-presented target nor second-presented target was selected: 0/10 each.

## Distribution and preregistered classification

| Condition | RIGHT_2 | STRAIGHT_2 | OTHER_LEGAL | INVALID |
| --- | ---: | ---: | ---: | ---: |
| `RIGHT_TARGET_FIRST` | 0/5 | 0/5 | 5/5 | 0/5 |
| `STRAIGHT_TARGET_FIRST` | 0/5 | 0/5 | 5/5 | 0/5 |

**`NO_OBSERVED_TURN_COMPOSITION_EFFECT`** under the preregistered rule. Both conditions have at least 4/5 valid requests, but neither target class reached 6/10; the response distribution instead consists entirely of `OTHER_LEGAL` selections.

## Order-bias analysis

**`ORDER_EFFECT_NOT_OBSERVED` for the swapped target positions.** The right/straight target positions were reversed between conditions, but the selected candidate stayed identical and remained at position 11. This rules out a target-first versus target-second explanation for this observed selection. It does not establish that Gemini is insensitive to every possible prompt-order change outside the registered two-target swap.

## Integration with current behavioural evidence

| Factor | Evidence | Result | Confidence and limitation |
| --- | --- | --- | --- |
| Aggregate waiting | Phase 3B, 20 valid requests | W08 R4 5/5; W19/W20/W24 S2 5/5 | Repeatable fixed-state behavioural association; not an internal threshold or performance result. |
| Individual waiting distribution | 15 valid requests at aggregate 20 s | `NO_OBSERVED_DISTRIBUTION_EFFECT` | Moderate condition was mixed, but endpoints were identical; maximum waiting remained coupled to distribution. |
| Matched turn composition | This 10-valid-request probe | `NO_OBSERVED_TURN_COMPOSITION_EFFECT` | Neither matched target was selected because a legal three-vehicle competitor dominated all requests. |
| Presentation order | This 10-valid-request probe | `ORDER_EFFECT_NOT_OBSERVED` for target swap | Targets changed positions 8/10 to 10/8, while the same position-11 non-target was selected. |

## Scientific claim boundary

| Claim | Status | Basis |
| --- | --- | --- |
| Gemini selection responds repeatably to aggregate waiting. | SUPPORTED | Completed Phase 3B distribution across W08--W24. |
| Within-group waiting distribution independently changes selection. | NOT_SUPPORTED | No preregistered ordered endpoint change. |
| Matched RIGHT vs STRAIGHT candidate structure is associated with different Gemini selection behaviour. | NOT_SUPPORTED | Neither two-vehicle target was selected. |
| Movement label alone causally determines selection. | NOT_SUPPORTED | Targets retain route/edge/identity confounds and were not selected. |
| Candidate presentation order affects selection. | NOT_SUPPORTED for the registered target swap | The selection did not follow either swapped target position. |
| Gemini prefers STRAIGHT generally. | NOT_SUPPORTED | No straight target was selected here; no generalisation is valid. |
| Gemini is superior to the deterministic comparator. | NOT_SUPPORTED | This is not an effectiveness comparison. |
| Candidate-choice differences improve closed-loop traffic. | STILL_UNKNOWN | No same-state counterfactual traffic outcome is available. |

## Recommendation and counterfactual timing

**`PROCEED_COUNTERFACTUAL`** is the recommended next research step, but only as a separately authorised design/implementation audit before any execution. The current behavioural programme already establishes one repeatable aggregate-waiting selection difference and has ruled out a stable within-group distribution effect under the tested rule. The turn probe did not identify a target preference because of a larger legal competitor; removing that competitor now would be outcome-driven candidate-context tuning rather than a clean continuation.

The next bounded question should be the existing counterfactual question: from one identical pre-decision state, what downstream outcome follows from forcing the observed legal S2 choice versus the deterministic legal R4 choice? It requires independently verified snapshot equivalence, controller-state restoration, and branch provenance. No counterfactual run is authorized by this audit.
