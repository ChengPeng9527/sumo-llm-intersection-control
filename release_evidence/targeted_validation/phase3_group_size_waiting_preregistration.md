# Phase 3 Group Size x Aggregate Waiting Preregistration

## Status and evidence boundary

This is a targeted post-hoc supplementary validation study. It does not alter
the frozen Phase 1/2 experiments or the completed Phase 3 evidence. The study
must use the formal Phase 2 candidate-selection prompt, parser, provider
adapter, deterministic comparator reference, and candidate legality
representation without modification. No SUMO run is part of this protocol.

This preregistration must exist before the first future connectivity or
experimental provider request. Invalid requests are retained without
replacement, condition-level retry, or adaptive redesign.

## Research question

With other candidate attributes controlled as far as technically possible,
how does the interaction between candidate group-size advantage and aggregate
waiting pressure relate to Gemini's legal candidate selection?

The study does not ask whether Gemini optimises throughput, whether Gemini is
superior, whether a condition can make Gemini outperform the comparator, or
whether Gemini uses an exact internal threshold.

## Identifiability audit

**Classification: `GROUP_SIZE_IDENTIFIABLE_WITH_CONFOUNDS`.**

The frozen S3-12V candidate lattice contains legal two-, three-, and
four-vehicle candidates, so a legal group-size contrast can be constructed
without relabelling a route or inventing an illegal movement. Strong isolation
is not possible. If the full 18-candidate state is retained, R3 and R4 are
simultaneously available and group-size advantage is not a manipulated
condition. To create a genuine `+1` condition, one right-turn vehicle must be
absent and every candidate containing it must consequently be absent. That
changes candidate richness and directional balance. Those changes are
intrinsic retained confounds, not effects to be hidden by deleting an
unfavourable competitor.

No important competitor is selectively removed within a condition. The `+1`
condition is the complete legal subset induced by one absent vehicle; the
`+2` condition is the complete frozen legal set. Candidate legality semantics
are unchanged.

## Historical anchor and minimal transformation

The anchor is frozen Phase 2 S3-12V seed 2, decision epoch 3, simulation time
23 s. It contains 18 legal candidates. The deterministic comparator selected
the rank-1 four-vehicle all-RIGHT candidate R4 (`10|11|8|9`); Gemini selected
the rank-3 two-vehicle opposite-STRAIGHT candidate S2 (`4|5`). The same legal
set contains R3 (`11|8|9`). All target vehicles have unavailable ETA in this
anchor and are stopped; route semantics and legality are retained.

The only registered transformations are:

1. set the available right-turn target vehicles' waiting values to zero in
   every cell, so R3 and R4 each have aggregate and maximum waiting zero;
2. set the two S2 vehicles to equal waiting values that sum to the registered
   aggregate-waiting level; and
3. for group-size advantage `+1`, remove vehicle 10 and all legal candidates
   containing it, leaving the complete 13-candidate induced subset with R3 as
   the larger target. For `+2`, retain the complete 18-candidate anchor with
   R4 as the larger target.

All common vehicles retain speed, distance, edge, lane/movement semantics,
and ETA. The two LEFT vehicles retain their anchor state.

### Main confounds

- Candidate richness is 13 at `+1` and 18 at `+2`.
- The `+1` state has seven locally represented vehicles while `+2` has eight.
- R3 lacks the S-approach right-turn vehicle present in the directionally
  balanced R4 group.
- Candidate identities and absolute presentation positions cannot be equal
  across different candidate lattices.

These confounds prohibit a claim that group size alone caused any observed
selection change. The probe can only identify a reproducible behavioural
association across the registered compound conditions.

## Fixed minimal matrix

Group-size advantage is defined as:

`size(larger all-RIGHT target) - size(smaller opposite-STRAIGHT target)`.

| Condition | Larger target | Smaller target | Advantage | S2 aggregate waiting | S2 individual waiting | Candidate count |
|---|---|---|---:|---:|---|---:|
| `G1_LOW` | R3, size 3 | S2, size 2 | +1 | 8 s | 4 + 4 s | 13 |
| `G1_HIGH` | R3, size 3 | S2, size 2 | +1 | 20 s | 10 + 10 s | 13 |
| `G2_LOW` | R4, size 4 | S2, size 2 | +2 | 8 s | 4 + 4 s | 18 |
| `G2_HIGH` | R4, size 4 | S2, size 2 | +2 | 20 s | 10 + 10 s | 18 |

There are exactly three independent Gemini requests per cell, for at most 12
experimental logical requests. The low/high levels reuse the completed
aggregate-waiting evidence and do not search the 8--19 s interval for a
threshold.

## Presentation-order control

Within each group-size lattice, all non-target candidates retain their frozen
relative order. S2 is placed penultimate and the registered larger target is
placed last. This rule is identical in all four cells. Candidate IDs/order,
target positions, order-sensitive presentation hash, and order-insensitive
candidate-set hash are retained for every request. Absolute positions and
candidate count still differ between the two group-size levels and remain a
recorded confound.

## Validity and outputs

A decision is valid only if provider request succeeds, parsing succeeds,
fallback is false, and the selected candidate belongs to the cell's legal
candidate set. Every cell reports counts for:

- `LARGER_GROUP` (R3 in `+1`, R4 in `+2`);
- `SMALLER_HIGH_WAIT` (S2);
- `OTHER_LEGAL`; and
- `INVALID`.

The runner also retains group sizes, contrast, aggregate and individual
waiting, turn composition, ETA, candidate richness and ordered IDs, selected
candidate and legality, provider/parser/fallback provenance, latency,
sanitised raw output, timestamp, non-empty prompt hash, input-state hash,
candidate-set hash, presentation hash, and generation configuration.

## Frozen classification rules

Each cell must contain at least two valid decisions; otherwise the result is
`INCONCLUSIVE`. For valid cells define a material count change as at least two
of the three registered requests.

- A **waiting response** exists when, for at least one group-size level,
  `SMALLER_HIGH_WAIT` increases by at least two from LOW to HIGH and
  `LARGER_GROUP` decreases by at least two. Direction must not reverse at the
  other group-size level.
- A **size response** exists when, for at least one waiting regime,
  `LARGER_GROUP` increases by at least two from advantage `+1` to `+2` or
  `SMALLER_HIGH_WAIT` decreases by at least two. Direction must not reverse in
  the other waiting regime.

The final categories are:

- `SIZE_WAITING_TRADEOFF_OBSERVED`: every cell meets validity requirements,
  both waiting and size responses exist, and neither directional consistency
  check reverses.
- `PARTIAL_SIZE_WAITING_TRADEOFF`: every cell meets validity requirements and
  exactly one of the waiting or size responses exists, or both appear but a
  non-material directional reversal prevents the full category.
- `NO_CLEAR_SIZE_WAITING_TRADEOFF`: every cell meets validity requirements but
  neither registered response exists.
- `INCONCLUSIVE`: at least one cell has fewer than two valid decisions.

Counts and proportions are descriptive. With `n=3` per cell, no inferential,
population, causal-mechanism, internal-utility, fairness, superiority, or
traffic-performance claim is permitted.

## Connectivity and execution policy

The future manual runner may make at most one connectivity request. If it
fails, all 12 experimental requests remain `NOT_RUN`. If it passes, each
registered request is attempted exactly once. No request is replaced or
retried. The provider/model remain Gemini / `gemini-3.6-flash` through the
existing formal Phase 2 path.

## Q3 follow-up rule

If the result is `SIZE_WAITING_TRADEOFF_OBSERVED`, or a strong
`PARTIAL_SIZE_WAITING_TRADEOFF` with the registered waiting response and a
directionally consistent but sub-material size response, a separately
preregistered Q3 study may choose states by experimental role only:

1. a registered larger-group-dominant state;
2. a registered transition/trade-off state; and
3. a registered waiting-dominant state.

Selection must be based on the preregistered condition pattern, never on which
state makes Gemini look better. If the result is
`NO_CLEAR_SIZE_WAITING_TRADEOFF` or `INCONCLUSIVE`, this two-factor hypothesis
must not motivate a Q3 counterfactual extension.
