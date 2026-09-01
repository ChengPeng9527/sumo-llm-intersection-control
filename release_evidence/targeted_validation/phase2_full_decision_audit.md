# Phase 2 Full Decision Audit

## Scope and source boundary

This targeted analysis is read-only with respect to frozen Phase 2 evidence. It audits the 18 Gemini-controlled `decision_records.jsonl` files below `results/phase2_formal/`; the derived CSV is a new targeted-validation artefact, not a replacement for frozen evidence. No SUMO run, provider request, or controller/prompt/parser change was made.

## Audit result

- Logical Gemini decision epochs: **93**
- Agreement / disagreement: **89 / 4**
- Provider request attempted and successful: **93 / 93**
- Parser successful: **93 / 93**
- Fallback: **0 / 93**
- Gemini selected candidate legal: **93 / 93**
- Deterministic selected candidate legal: **93 / 93**
- Duplicate `(run_id, decision_epoch)` keys: **0**
- Provider/model: **Gemini / gemini-3.6-flash** for all 93 records.

The independently recomputed counts match the frozen complete-matrix summary (93 requests, 93 provider successes, 93 parser successes, zero fallbacks, 89 agreements, four disagreements). No frozen-evidence consistency issue was found.

## Provenance consistency

Every record retains `llm_raw_output`; each is parseable JSON and its `selected_candidate_id` equals the persisted `llm_candidate_id`. Each record also retains candidate set/features, deterministic and Gemini candidate IDs, provider/parser/fallback fields, latency, request timestamps, prompt hash, and canonical prompt reconstruction data. Thus the retained chain is: provider response text -> parser candidate ID -> persisted Gemini selection -> legal candidate set.

`HISTORICAL_RAW_RESPONSE_NOT_RETAINED` is **not applicable**: sanitized raw response text is retained for all 93 records. The audit found no record-level marker of `mock`, `cache`, `synthetic`, hard-coded substitution, or fallback mislabelled as a Gemini success. This is a provenance observation from the retained records, not an independent proof about external provider infrastructure.

## Coverage

| Scenario | Scale | Seed | Gemini decision epochs |
|---|---:|---:|---:|
| S1_BALANCED_MIXED_TURN_V8 | 8 | 1 | 7 |
| S1_BALANCED_MIXED_TURN_V8 | 8 | 2 | 7 |
| S1_BALANCED_MIXED_TURN_V8 | 8 | 3 | 7 |
| S2_SIMULTANEOUS_CONFLICT_V8 | 8 | 1 | 5 |
| S2_SIMULTANEOUS_CONFLICT_V8 | 8 | 2 | 5 |
| S2_SIMULTANEOUS_CONFLICT_V8 | 8 | 3 | 5 |
| S3_COOPERATIVE_OPPORTUNITY_V12 | 12 | 1 | 5 |
| S3_COOPERATIVE_OPPORTUNITY_V12 | 12 | 2 | 5 |
| S3_COOPERATIVE_OPPORTUNITY_V12 | 12 | 3 | 5 |
| S3_COOPERATIVE_OPPORTUNITY_V8 | 8 | 1 | 4 |
| S3_COOPERATIVE_OPPORTUNITY_V8 | 8 | 2 | 4 |
| S3_COOPERATIVE_OPPORTUNITY_V8 | 8 | 3 | 4 |
| S4_FAIRNESS_PRESSURE_V16 | 16 | 1 | 6 |
| S4_FAIRNESS_PRESSURE_V16 | 16 | 2 | 6 |
| S4_FAIRNESS_PRESSURE_V16 | 16 | 3 | 6 |
| S4_FAIRNESS_PRESSURE_V8 | 8 | 1 | 4 |
| S4_FAIRNESS_PRESSURE_V8 | 8 | 2 | 4 |
| S4_FAIRNESS_PRESSURE_V8 | 8 | 3 | 4 |

## Agreement versus disagreement (descriptive)

Means are descriptive; ranges are shown in parentheses. ETA spread uses only finite retained local ETA values, so it is not comparable where most ETA values are non-finite/unrecorded.

| Feature | Agreement (n=89) | Disagreement (n=4) |
|---|---:|---:|
| Legal candidate count | 5.84 (1--28) | 16.00 (10--18) |
| Maximum group size | 1.93 (1--4) | 3.50 (2--4) |
| Group-size range | 0.93 (0--3) | 2.50 (1--3) |
| Number of maximal groups | 1.31 (1--3) | 1.50 (1--3) |
| Deterministic selected group size | 1.93 (1--4) | 3.50 (2--4) |
| Gemini selected group size | 1.93 (1--4) | 2.00 (2--2) |
| State waiting spread (s) | 3.37 (0.00--14.00) | 8.25 (2.00--11.00) |
| Finite ETA spread (s) | 5.79 (0.00--164.39) | 6.92 (0.00--12.09) |
| Turn diversity | 1.69 (1--3) | 2.75 (2--3) |
| Gemini comparator rank | 1.00 (1--1) | 3.00 (3--3) |

The four disagreements are concentrated in one S2 8V epoch and one epoch for each S3 12V seed. They occur in comparatively rich candidate sets, but agreement also occurs with up to 28 candidates. Candidate richness is therefore an observed association, not a sufficient condition or causal explanation.

## Individual disagreement records

Comparator rank is reconstructed from the frozen comparator rule: group size descending, aggregate waiting descending, maximum waiting descending, finite minimum ETA ascending, then candidate ID.

| Scenario | Scale | Seed | Epoch / time (s) | Legal candidates | Deterministic rank | Deterministic group | Gemini rank | Gemini group |
|---|---:|---:|---:|---:|---:|---|---:|---|
| S2_SIMULTANEOUS_CONFLICT_V8 | 8 | 1 | 2 / 11 | 10 | 1 | 2 / LEFT|LEFT / wait 3/2 | 3 | 2 / LEFT|LEFT / wait 0/0 |
| S3_COOPERATIVE_OPPORTUNITY_V12 | 12 | 1 | 3 / 21 | 18 | 1 | 4 / RIGHT|RIGHT|RIGHT|RIGHT / wait 8/5 | 3 | 2 / STRAIGHT|STRAIGHT / wait 20/10 |
| S3_COOPERATIVE_OPPORTUNITY_V12 | 12 | 2 | 3 / 23 | 18 | 1 | 4 / RIGHT|RIGHT|RIGHT|RIGHT / wait 18/7 | 3 | 2 / STRAIGHT|STRAIGHT / wait 24/13 |
| S3_COOPERATIVE_OPPORTUNITY_V12 | 12 | 3 | 3 / 20 | 18 | 1 | 4 / RIGHT|RIGHT|RIGHT|RIGHT / wait 4/4 | 3 | 2 / STRAIGHT|STRAIGHT / wait 19/10 |

### Repeated S3 12V structure

All three S3 12V seeds diverge exactly once (seed 1 at 21 s, seed 2 at 23 s, seed 3 at 20 s). Each has 18 legal candidates, one legal four-vehicle all-RIGHT deterministic choice at comparator rank 1, and Gemini selects the legal two-vehicle opposite-STRAIGHT group at comparator rank 3. The shared structural feature is a group-size/throughput priority competing with a higher-waiting opposite-straight pair. The retained evidence does not identify the model's internal rationale; it only establishes legal, successfully parsed selections under the frozen prompt.

### S2 8V distinction

The single S2 seed-1 divergence occurs at 11 s with 10 legal candidates. Both choices are two-vehicle all-LEFT groups; deterministic rank is 9 and Gemini rank is 10. It therefore does not exhibit the S3 12V four-RIGHT versus two-STRAIGHT, rank-1 versus rank-3 structure. It is one isolated low-frequency observation, not evidence of a general family.

## Complexity hypothesis

**PARTIALLY_SUPPORTED.** The disagreements have higher observed candidate count (mean 16.00 versus 5.84), broader group-size range (2.50 versus 0.93), higher waiting spread (8.25 s versus 3.37 s), and higher turn diversity (2.75 versus 1.69). These variables have descriptive discriminative potential. However, all 93 observations are not independent counterfactual states, the four disagreements are concentrated in S3 12V plus one S2 epoch, candidate-count ranges overlap (agreement reaches 28), and post-divergence states cannot be treated as shared paired states. The evidence therefore does **not** establish that complexity or trade-offs cause divergence.

## Limits

This audit cannot recover unretained provider-side reasoning, establish causation, test generalisation, or infer planner superiority/equivalence. The report preserves the frozen evidence boundary and makes no claim beyond observed record structure.
