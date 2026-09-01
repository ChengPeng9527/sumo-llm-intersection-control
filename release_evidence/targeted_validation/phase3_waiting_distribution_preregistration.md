# Phase 3 Individual Waiting Distribution Probe Preregistration

## Question and evidence boundary

**Primary RQ:** With aggregate candidate waiting held constant, does changing the within-candidate distribution of individual vehicle waiting times alter Gemini's legal candidate selection?

This is a separately labelled fixed-state supplementary experiment. It reuses the frozen Phase 3B S3-12V decision-state template and formal Phase 2 candidate-selection path. It does not reinterpret or modify frozen Phase 1, Phase 2, Phase3B1-R2, or Phase 3B evidence. It does not test direct `WAIT` actions, fairness, superiority, internal thresholds, or closed-loop traffic performance.

## Manipulability check

The actual candidate-selection prompt contains per-vehicle local `waiting_time`, `vehicle_id`, `incoming_edge`, `outgoing_edge`, `movement`, speed, distance, ETA, and control-zone status. Each candidate feature explicitly includes `group_size`, `aggregate_waiting_time`, `maximum_waiting_time`, and minimum ETA. Therefore the registered manipulation is identifiable: the two S2 vehicles' individual waiting values differ while their aggregate candidate waiting remains fixed.

## Registered fixed template

The template is the retained S3-12V seed-1 disagreement state used by Phase 3B. `R4` is the legal four-vehicle all-`RIGHT` comparator rank-1 group. `S2` is the legal two-vehicle opposite-`STRAIGHT` rank-3 group. The template must retain exactly 18 legal candidate groups.

Across all conditions, the following are held constant: source state except the two S2 `waiting_time` values, aggregate S2 waiting, R4 state and attributes, candidate set, candidate IDs/order, group sizes, routes/directions/turns, ETA-related values, prompt construction, parser, comparator, legal filtering, provider/model, and generation configuration.

## Registered matrix

The fixed S2 aggregate waiting is **20 s**, selected because it was a stable S2 condition in the completed Phase 3B repeatability study. The three distributions provide the minimum three-level design needed to distinguish equality, a historically plausible moderate maximum (13 s), and a clearly larger imbalance while keeping the same total:

| Condition | S2 individual waiting values (s) | S2 aggregate (s) | Independent logical requests |
| --- | --- | ---: | ---: |
| `BALANCED` | 10, 10 | 20 | 5 |
| `MODERATELY_SKEWED` | 7, 13 | 20 | 5 |
| `HIGHLY_SKEWED` | 2, 18 | 20 | 5 |

The maximum is 15 experimental logical requests. IDs are `BALANCED_R1` through `HIGHLY_SKEWED_R5`. Each request is issued once; invalid requests are retained and never replaced. A single bounded connectivity gate is allowed before the 15-request matrix and is recorded separately. If it fails, all experimental requests are `NOT_RUN`.

## Validity and primary outcome

A request is `VALID` only when `provider_request_success=true`, `parser_success=true`, `fallback_used=false`, and the selected candidate is legal. Valid selections are classified as `R4`, `S2`, or `OTHER_LEGAL`; all other outcomes are `INVALID`.

Primary outcome: the distribution of `R4`, `S2`, `OTHER_LEGAL`, and `INVALID` across the three registered conditions.

The preregistered descriptive classification is:

- `DISTRIBUTION_SENSITIVE`: every condition has at least 4/5 valid requests; one valid selection class changes by at least 3 selections between `BALANCED` and `HIGHLY_SKEWED`; and the `MODERATELY_SKEWED` count for that class lies between the endpoint counts (inclusive).
- `PARTIAL_DISTRIBUTION_SENSITIVITY`: every condition has at least 4/5 valid requests and endpoint distributions differ by at least 3 selections, but the moderate condition is not ordered as above.
- `NO_OBSERVED_DISTRIBUTION_EFFECT`: every condition has at least 4/5 valid requests and no selection-class endpoint count differs by 3 or more.
- `INCONCLUSIVE`: any condition has fewer than 4/5 valid requests, or the pre-run connectivity gate fails.

These are descriptive decision rules, not population inference or an assertion of an internal model threshold.

## Provenance and outputs

The independent evidence root is `results/phase3_waiting_distribution_probe/`. It must never overwrite Phase 3B1, Phase 3B1-R2, Phase 3B repeatability, Phase 1, or Phase 2 outputs.

For every request, persist condition, replicate, individual/aggregate waiting values, candidate IDs, stable candidate-set hash, changing input-state hash, selected candidate, selection class, legality, provider/parser/fallback fields, latency, sanitised raw output, timestamp, non-empty SHA-256 prompt hash calculated from the actual sent prompt, provider attempt count, and generation configuration.

## Claim boundary

If a change is observed, the permitted statement is: **Gemini candidate selection was sensitive to the controlled within-group waiting distribution in this fixed decision state.** It does not establish that Gemini understands fairness, prioritises the most-starved vehicle, optimises fairness, uses maximum waiting as its mechanism, or has human-like reasoning.
