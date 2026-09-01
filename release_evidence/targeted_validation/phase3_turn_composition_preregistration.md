# Phase 3 Matched Turn-Composition Probe Preregistration

## Question and boundary

**Primary RQ:** With candidate group size and waiting-related attributes matched, does turn composition alter Gemini's legal candidate-group selection in a controlled fixed state?

This is behavioural characterisation, not a traffic-performance experiment. It does not modify or reinterpret frozen Phase 1, Phase 2, Phase3B1-R2, Phase 3B, or waiting-distribution evidence. It cannot establish that Gemini generally prefers straight traffic, understands efficiency, optimises throughput, or is superior to the comparator.

## Identifiability and historical anchor

The anchor is a real frozen legal state: S3-12V seed 2, decision epoch 2, simulation time 12 s. It contains 11 legal candidates, including a two-vehicle all-`RIGHT` candidate (`..._2_3|..._2_1`) and a two-vehicle opposite-`STRAIGHT` candidate (`..._2_5|..._2_4`). Both had group size 2, aggregate waiting 2 s, and maximum waiting 2 s. They are opposite-approach pairs and therefore preserve directional balance as far as the frozen topology allows.

The original target pair differed in local speed, distance, and minimum ETA. The registered static fixture pairwise copies `waiting_time`, speed, distance, ETA, and control-zone status from the real RIGHT target members to the corresponding STRAIGHT target members. This gives the two target candidates identical group size, individual/aggregate/maximum waiting, and minimum ETA. It retains their real vehicle IDs, incoming/outgoing edges, movement labels, route semantics, and legal frozen candidate membership. Candidate legality is inherited from the frozen candidate set; no illegal group is manufactured.

Classification: **`TURN_COMPOSITION_IDENTIFIABLE_WITH_CONFOUNDS`**. The remaining unavoidable prompt-visible confounds are route IDs, vehicle IDs, and incoming/outgoing edge identity. They cannot be removed without changing the actual legal route/turn semantics. Any outcome may therefore characterise selection among matched RIGHT-versus-STRAIGHT legal candidates, not an isolated semantic effect of the word `RIGHT` or `STRAIGHT` alone.

## Registered matrix and position control

Both legal target candidates are present in every request. The only condition manipulation is their presentation position in the candidate-group list; the state and order-insensitive candidate set remain fixed.

| Condition | Target candidate presentation order | Independent logical requests |
| --- | --- | ---: |
| `RIGHT_TARGET_FIRST` | RIGHT target precedes STRAIGHT target | 5 |
| `STRAIGHT_TARGET_FIRST` | STRAIGHT target precedes RIGHT target | 5 |

The maximum is 10 experimental logical requests. IDs are `RIGHT_TARGET_FIRST_R1` through `STRAIGHT_TARGET_FIRST_R5`. Every request is issued once. Invalid results remain recorded and are never replaced. One bounded connectivity gate may precede the matrix; if it fails, all ten entries are `NOT_RUN`.

## Controlled attributes

Across order conditions: source template, normalized local state, group-size, target individual/aggregate/maximum waiting, target minimum ETA, candidate count/richness, legal candidate set, provider/model, prompt structure, parser, comparator, safety/legal filtering, and generation configuration are held fixed. The stable order-insensitive `candidate_set_hash` and `input_state_hash` must match across conditions; `candidate_presentation_hash` and prompt hash must differ because presentation order is intentionally counterbalanced.

## Validity, outcome, and preregistered classification

A request is `VALID` only with provider success, parser success, no fallback, and a legal selected candidate. Valid selections are `RIGHT_2`, `STRAIGHT_2`, or `OTHER_LEGAL`; all others are `INVALID`.

- `TURN_COMPOSITION_EFFECT_OBSERVED`: each order condition has at least 4/5 valid requests; one target class is selected at least 8/10 overall and at least 3/5 under each presentation order.
- `PARTIAL_TURN_COMPOSITION_EFFECT`: each condition has at least 4/5 valid requests; a target class is selected at least 6/10 overall but does not meet the cross-order persistence rule.
- `NO_OBSERVED_TURN_COMPOSITION_EFFECT`: each condition has at least 4/5 valid requests and neither target class reaches 6/10 overall, or apparent target choice reverses completely with presentation order.
- `INCONCLUSIVE`: either condition has fewer than 4/5 valid requests, or the connectivity gate fails.

All classification is descriptive. Candidate order is explicitly counterbalanced because it is prompt-visible; no result can be attributed to turn composition if a complete order reversal occurs.

## Provenance

Use only `results/phase3_turn_composition_probe/` and new `phase3_turn_composition_*` evidence files. Each raw record retains IDs, condition, selected candidate/class, legality, provider/parser/fallback fields, latency, sanitized raw output, timestamp, non-empty actual-prompt hash, input-state hash, stable candidate-set hash, presentation-order hash, generation configuration, and one-request attempt count.
