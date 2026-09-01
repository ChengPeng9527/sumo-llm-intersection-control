# Phase 3 Waiting-Distribution Post-Run Evidence Audit

## Scope

This is a read-only audit of the independently executed Phase 3 fixed-state individual-waiting distribution probe. It does not modify the preregistration, raw outputs, classification criteria, frozen Phase 1/2 evidence, or other Phase 3 evidence. No Gemini request and no SUMO run was made during this audit.

## Evidence integrity

The evidence root `results/phase3_waiting_distribution_probe/` contains a passed connectivity record, completed `run_metadata.json`, and exactly 15 raw decision records. The CSV contains exactly 15 unique request IDs, matching the registered three conditions times five replicates:

- Provider success: 15/15.
- Parser success: 15/15.
- Fallback: 0/15.
- Legal selected candidate: 15/15.
- Invalid: 0/15.
- `request_attempt_count`: 1 for every record; no replacement/retry record is present.
- Sanitised `llm_raw_output`: retained in every raw record.
- `prompt_hash`: non-empty in every record; one prompt hash per condition and three distinct hashes overall.
- `candidate_set_hash`: one identical value across all 15 records.
- `input_state_hash`: one value per condition and three distinct values overall.
- `generation_config`: one identical object across all records: Gemini / `gemini-3.6-flash`.

The connectivity gate is separately retained and passed with HTTP 200. `run_metadata.json` records `COMPLETED`, 15 experimental logical requests, five replicates per condition, and `NO_LOGICAL_REQUEST_REPLACEMENT`.

All conditions retained S2 aggregate waiting of 20 s: `BALANCED` = 10 + 10, `MODERATELY_SKEWED` = 7 + 13, and `HIGHLY_SKEWED` = 2 + 18. Candidate IDs/order and candidate-set hash were unchanged. The three input-state and prompt hashes differ exactly by registered condition, consistent with the intended waiting-state change.

### Provenance limitation

The raw records retain condition-specific input-state hashes rather than a complete per-request local-state payload. Consequently, the output evidence independently confirms stable candidate set/order, generation configuration, and condition-specific prompt/state identity, while exact equality of every non-target local-state field is supported by the registered runner implementation and its fake-provider tests rather than by a separately persisted full state snapshot. No unexpected variation is evidenced in the retained records.

## Primary results

| Condition | Individual waiting (s) | Maximum waiting (s) | R4 | S2 | OTHER_LEGAL | INVALID | Valid total |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BALANCED` | 10, 10 | 10 | 0 | 5 | 0 | 0 | 5 |
| `MODERATELY_SKEWED` | 7, 13 | 13 | 2 | 3 | 0 | 0 | 5 |
| `HIGHLY_SKEWED` | 2, 18 | 18 | 0 | 5 | 0 | 0 | 5 |

Replicate-level sequence:

| Request sequence | Selections |
| --- | --- |
| `BALANCED_R1`--`BALANCED_R5` | S2, S2, S2, S2, S2 |
| `MODERATELY_SKEWED_R1`--`MODERATELY_SKEWED_R5` | S2, S2, R4, R4, S2 |
| `HIGHLY_SKEWED_R1`--`HIGHLY_SKEWED_R5` | S2, S2, S2, S2, S2 |

## Preregistered classification

**`NO_OBSERVED_DISTRIBUTION_EFFECT`**.

Every condition meets the at-least-4/5-valid requirement. However, the endpoint distributions are identical: `BALANCED` and `HIGHLY_SKEWED` each selected S2 in 5/5 requests and R4 in 0/5. No valid selection class differs by at least three selections between the two endpoints. The mixed 2/5 R4 result at `MODERATELY_SKEWED` is therefore retained as descriptive variation, but cannot satisfy the preregistered ordered endpoint criterion and must not be retrospectively relabelled as distribution sensitivity.

With aggregate waiting fixed at 20 s, this sample does not show a preregistered, ordered change in Gemini candidate-selection distribution as within-group waiting distribution changes.

## Integration with aggregate-waiting evidence

The completed aggregate-waiting study found R4 in W08 5/5 and S2 in W19, W20, and W24 5/5. This is repeatable evidence that Gemini selection responded to the aggregate-waiting manipulation in the fixed state.

The present fixed-aggregate study neither establishes that aggregate waiting alone is the model's mechanism nor supports a separate ordered distribution effect. The correct combined interpretation is **mixed / cannot distinguish mechanism**: aggregate waiting is the strongest experimentally established behavioural manipulation, while the `MODERATELY_SKEWED` mixed sequence leaves descriptive uncertainty that is not an ordered within-distribution effect under the preregistered rule.

## Maximum-waiting confound and next waiting decision

Maximum waiting was necessarily coupled to the within-group distribution: 10 s, 13 s, and 18 s for the three conditions. If an ordered selection change had occurred, the experiment could not distinguish distribution from maximum-waiting information. Here, no preregistered ordered change occurred. Therefore **`NO_FURTHER_WAITING_TEST_NEEDED`** is recommended: a maximum-waiting disentanglement experiment would address a mechanism not currently supported by a stable distribution effect and would add API exposure without resolving the principal R4/S2 turn-composition confound.

## Scientific claim boundary

| Claim | Status | Reason |
| --- | --- | --- |
| Gemini selection responds repeatably to aggregate waiting manipulation in this fixed state. | SUPPORTED | W08 was R4 5/5; W19/W20/W24 were S2 5/5 in the completed aggregate-waiting study. |
| Gemini selection changes when aggregate waiting is fixed but within-group waiting distribution changes. | NOT_SUPPORTED | The registered endpoint test is unchanged (S2 5/5 at both endpoints); moderate mixed results are insufficient. |
| Gemini specifically uses maximum waiting as its decision rule. | NOT_SUPPORTED | Maximum waiting is coupled to distribution and no ordered distribution result was observed. |
| Gemini specifically uses individual waiting inequality. | NOT_SUPPORTED | The manipulation did not produce the preregistered ordered endpoint effect. |
| Gemini optimises fairness. | NOT_SUPPORTED | Candidate selection evidence does not identify an objective or reasoning mechanism. |
| Gemini is superior to the deterministic comparator. | NOT_SUPPORTED | This probe measures legal choice distribution, not comparative effectiveness. |
| Planner-choice differences improve closed-loop traffic. | STILL_UNKNOWN | No valid Phase 3C natural-emergence gate or counterfactual branch outcome evidence exists. |

## Recommended next factor and counterfactual timing

The highest-priority next behavioural factor is **matched turn composition**. It is directly represented in the candidate movement summaries and differs between the historical R4 all-`RIGHT` and S2 opposite-`STRAIGHT` selections. A future offline study should first construct and preregister a symmetric legal template holding group size, aggregate and individual waiting distribution, ETA, candidate richness, and route-direction balance constant while varying only turn composition.

Counterfactual timing is **`AFTER_NEXT_FACTOR`**. The next matched turn-composition probe addresses the central remaining R4/S2 confound at lower provenance and implementation risk than controller-state snapshot/restore. No counterfactual, provider request, or SUMO run is authorized by this audit.
