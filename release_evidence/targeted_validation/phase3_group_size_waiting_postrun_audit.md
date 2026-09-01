# Phase 3 Group Size x Waiting Post-Run Scientific Audit

## Scope

This is a read-only scientific audit of the independently executed targeted
probe under `results/phase3_group_size_waiting_probe/`. It does not alter the
preregistration, raw records, classification rules, or frozen Phase 1/2/3
evidence. No provider request, replacement request, retry, or SUMO run was
made during this audit.

Candidate IDs below are abbreviated to their final vehicle-number suffixes.
The full canonical IDs remain in the CSV and raw JSON records.

## Evidence integrity

- `run_metadata.json` records `COMPLETED`, four preregistered cells, three
  replicates per cell, exactly 12 experimental logical requests, and
  `NO_LOGICAL_REQUEST_REPLACEMENT`.
- The CSV contains exactly 12 rows and 12 unique request IDs. The raw
  namespace contains exactly one JSON record for each request ID.
- Provider success: 9/12; parser success: 9/12; fallback: 3/12; legal
  selection: 9/12; valid: 9/12; invalid: 3/12.
- Every request records `request_attempt_count = 1`; no replacement or retry
  evidence is present.
- Sanitised raw model output is retained for every successful response. The
  three provider failures have no model output, as expected.
- Prompt hash, input-state hash, candidate-set hash, and presentation hash are
  non-empty in all 12 rows. There is one prompt/input-state hash per cell.
- Candidate-set and presentation hashes are constant across LOW/HIGH within
  each group-size context: one pair for G1 (13 candidates) and one pair for G2
  (18 candidates).
- Two exact generation-configuration serialisations are retained because the
  legal response-schema enum differs between the 13- and 18-candidate sets.
  Their common provider, model, timeout, response MIME type, and unspecified
  sampling parameters are consistent.
- The separately retained connectivity gate passed with HTTP 200. It is not
  counted among the 12 experimental logical requests.

No evidence-integrity mismatch was found.

## Invalid requests

| Request | Provider success | Parser success | Fallback | Failure | Latency | Raw output | Interpretation |
|---|---|---|---|---|---:|---|---|
| `G1_HIGH_R3` | No | No | Yes | `TIMEOUT`; parser reason `PROVIDER_FAILURE` | 60,211.70 ms | None | Provider timeout before a model selection was received. |
| `G2_LOW_R3` | No | No | Yes | `TIMEOUT`; parser reason `PROVIDER_FAILURE` | 60,156.87 ms | None | Provider timeout before a model selection was received. |
| `G2_HIGH_R1` | No | No | Yes | `SERVER_ERROR`; parser reason `PROVIDER_FAILURE` | 28,156.17 ms | None | Provider-side/server error; no candidate was parsed. |

All three records are correctly retained as `INVALID`. They are not illegal
Gemini selections and must not be counted as agreement, disagreement, or a
selection class. No retry is permitted.

## Replicate-level selections

Deterministic rank is reconstructed with the unchanged comparator ordering.
The deterministic target is rank 1 in every cell. Selected candidate waiting
is aggregate waiting in seconds.

| Request | Contrast | Waiting | Validity | Selected candidate | Class | Size | Waiting | Deterministic rank |
|---|---:|---|---|---|---|---:|---:|---:|
| `G1_LOW_R1` | +1 | LOW (8 s) | VALID | `6|7` | OTHER_LEGAL | 2 | 14 | 2 |
| `G1_LOW_R2` | +1 | LOW (8 s) | VALID | `6|7` | OTHER_LEGAL | 2 | 14 | 2 |
| `G1_LOW_R3` | +1 | LOW (8 s) | VALID | `6|7` | OTHER_LEGAL | 2 | 14 | 2 |
| `G1_HIGH_R1` | +1 | HIGH (20 s) | VALID | `4|5` | S2_HIGH_WAIT | 2 | 20 | 2 |
| `G1_HIGH_R2` | +1 | HIGH (20 s) | VALID | `4|5` | S2_HIGH_WAIT | 2 | 20 | 2 |
| `G1_HIGH_R3` | +1 | HIGH (20 s) | INVALID | None | INVALID | - | - | - |
| `G2_LOW_R1` | +2 | LOW (8 s) | VALID | `6|7` | OTHER_LEGAL | 2 | 14 | 3 |
| `G2_LOW_R2` | +2 | LOW (8 s) | VALID | `6|7` | OTHER_LEGAL | 2 | 14 | 3 |
| `G2_LOW_R3` | +2 | LOW (8 s) | INVALID | None | INVALID | - | - | - |
| `G2_HIGH_R1` | +2 | HIGH (20 s) | INVALID | None | INVALID | - | - | - |
| `G2_HIGH_R2` | +2 | HIGH (20 s) | VALID | `4|5` | S2_HIGH_WAIT | 2 | 20 | 3 |
| `G2_HIGH_R3` | +2 | HIGH (20 s) | VALID | `4|5` | S2_HIGH_WAIT | 2 | 20 | 3 |

The OTHER_LEGAL candidate `6|7` is the two-vehicle all-LEFT group. The
registered larger target (R3 in G1 and R4 in G2) was never selected.

## Cell-level results

| Cell | Larger group | S2 | Other legal | Invalid | Valid total | Valid-only distribution |
|---|---:|---:|---:|---:|---:|---|
| `G1_LOW` (+1, 8 s) | 0/3 | 0/3 | 3/3 | 0/3 | 3 | Other 3/3 (100%) |
| `G1_HIGH` (+1, 20 s) | 0/3 | 2/3 | 0/3 | 1/3 | 2 | S2 2/2 (100%) |
| `G2_LOW` (+2, 8 s) | 0/3 | 0/3 | 2/3 | 1/3 | 2 | Other 2/2 (100%) |
| `G2_HIGH` (+2, 20 s) | 0/3 | 2/3 | 0/3 | 1/3 | 2 | S2 2/2 (100%) |

Invalid requests remain in the registered denominator. Valid-only
proportions are descriptive and do not replace the 3-request cell totals.

## Preregistered classification

**`NO_CLEAR_SIZE_WAITING_TRADEOFF`.**

Every cell has at least two valid decisions, so the result is not
`INCONCLUSIVE`. The preregistered waiting response requires, in at least one
group-size context, both an increase of at least two S2 selections and a
decrease of at least two larger-group selections from LOW to HIGH. S2 does
increase by two in both G1 and G2, but larger-group selections remain zero in
every cell; the required larger-group decrease does not occur. The registered
size response also does not occur because increasing the advantage from +1 to
+2 produces no material increase in larger-group selection and no material
decrease in S2 selection at either waiting level.

### Direct answers

- **+1 LOW to HIGH:** valid selections change from OTHER_LEGAL `6|7` to S2,
  but not from the registered larger target to S2. Therefore the descriptive
  selection shift is present while the preregistered waiting response is not.
- **+2 LOW to HIGH:** the same OTHER_LEGAL-to-S2 pattern is observed, but the
  preregistered larger-to-S2 response is not.
- **Cross-context repeatability:** the descriptive LOW/HIGH selection pattern
  repeats across both candidate-size contexts among valid responses.
- **Group-size effect:** no registered group-size response is observed. The
  larger target is selected 0 times at both advantages.

The preregistered confounds remain material: G1/G2 differ in candidate
richness (13/18), local vehicle count, directional balance, candidate
identity, and absolute position. No pure group-size causal interpretation is
permitted.

## Invalidity impact

**`ROBUST` for the preregistered classification, with reduced descriptive
precision.** All cells satisfy the minimum two-valid-decision rule. Moreover,
no possible selection from any one missing request can create the registered
two-count decrease in larger-group choice: G1_LOW has zero larger selections
across all three completed requests, while G2_LOW has at most one unknown
request. The missing outcomes likewise cannot create the registered material
size response. Thus the frozen classification remains
`NO_CLEAR_SIZE_WAITING_TRADEOFF` without replacement requests.

This robustness applies only to the classification rule. Three provider
failures out of 12 attempts and `n=2` valid observations in three cells weaken
the precision and generalisability of descriptive proportions.

## Q2 evidence synthesis

| Factor | Retained evidence | Conclusion |
|---|---|---|
| Aggregate waiting | W08 R4 5/5; W19/W20/W24 S2 15/15 | Repeatable waiting sensitivity in the original fixed candidate state. |
| Individual waiting distribution | `NO_OBSERVED_DISTRIBUTION_EFFECT` | No preregistered ordered endpoint effect with aggregate waiting fixed. |
| Matched turn composition | `NO_OBSERVED_TURN_COMPOSITION_EFFECT` | No registered target preference; an OTHER_LEGAL competitor was selected. |
| Group size x waiting | This probe: LOW valid selections all `6|7`; HIGH valid selections all S2; larger target 0 selections | Descriptive LOW/HIGH response repeats across two confounded candidate-size contexts, but no preregistered group-size x waiting trade-off is observed. |

The strongest bounded Q2 conclusion is:

> Across both preregistered candidate-size contexts, valid Gemini selections
> changed descriptively from the same legal all-left pair under low S2 waiting
> to the S2 opposite-straight pair under high S2 waiting. Because the larger
> target was never selected and the contexts differ in candidate richness and
> directional balance, this result does not establish a group-size by waiting
> trade-off or a causal group-size effect.

The stronger statement that Gemini exhibits a reproducible group-size/waiting
trade-off across multiple candidate-size contexts is **not supported**.

## Q3 gate

**`Q3_EXTENSION_NOT_SUPPORTED`.** The frozen Q3 rule allows extension only
after `SIZE_WAITING_TRADEOFF_OBSERVED` or a strong partial result containing
the registered waiting response and a directionally consistent size response.
This study is `NO_CLEAR_SIZE_WAITING_TRADEOFF`; therefore no representative
larger-group-dominant, transition, or waiting-dominant states may be selected
from this matrix for Q3.

The existing completed historical same-state counterfactual remains the
appropriate downstream evidence. This probe does not reopen or invalidate
its `R4_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES` result.

## Claim boundaries

| Claim | Status | Reason |
|---|---|---|
| Aggregate waiting influences controlled Gemini selection. | **SUPPORTED, bounded** | Prior 20-request repeatability and this probe's unanimous valid LOW/HIGH class change support behavioural sensitivity in tested fixed states; this is not an internal-mechanism claim. |
| Waiting-related response repeats across candidate-size contexts. | **PARTIALLY_SUPPORTED** | The valid descriptive OTHER-to-S2 pattern repeats in G1/G2, but three requests are invalid and the registered larger-to-S2 response does not occur. |
| Group-size advantage itself causally changes Gemini selection. | **NOT_SUPPORTED** | No size response is observed, and G1/G2 retain preregistered context confounds. |
| Gemini implements an efficiency/waiting utility trade-off. | **NOT_SUPPORTED** | Candidate-choice distributions do not reveal an internal utility or optimisation objective. |
| Gemini improves traffic. | **NOT_SUPPORTED** | This is an offline choice probe with no traffic outcomes. |
| Gemini can outperform R4 in selected high-wait states. | **STILL_UNKNOWN** | No Q3 branch was run; the existing historical branches favoured R4 only in their tested states. |
| Previous same-state R4 advantage generalises to all states. | **NOT_SUPPORTED** | Three historical interventions cannot support universal generalisation. |

## Research decision

**`STOP_Q2_AND_USE_EXISTING_COUNTERFACTUAL`.** The probe adds a useful bounded
observation that LOW/HIGH selection changes can appear in two confounded
candidate-size contexts, but it does not identify the preregistered
group-size/waiting trade-off. Additional feature scanning or replacement
requests would be outcome-driven and are not justified. The completed
same-state historical counterfactual should remain the downstream evidence
for the dissertation.
