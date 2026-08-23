# Phase 2 Complete Formal Experiment Matrix

## Status

**Status: FORMAL_MATRIX_COMPLETE_WITH_LIMITATIONS.**

This report combines frozen Batch 1 evidence at commit
735758a9725eb9ba1e34ad4165b7a7d4246b01ed and the Step 10 remaining matrix.
The frozen method was unchanged: mixed-turn semantics, deterministic conflict
model, safe candidate groups, deterministic comparator, Gemini selector,
deterministic fallback, safety authority, grant persistence, a 45-second timeout,
one request per new grant, and canonical provenance. The provider was Google
Gemini / gemini-3.6-flash.

## Matrix completion and validity

The complete matrix contains 36 independent closed-loop SUMO episodes.

| Condition | Seeds | Deterministic | Gemini | Total |
| --- | ---: | ---: | ---: | ---: |
| S1 8V | 1, 2, 3 | 3 | 3 | 6 |
| S2 8V | 1, 2, 3 | 3 | 3 | 6 |
| S3 8V | 1, 2, 3 | 3 | 3 | 6 |
| S4 8V | 1, 2, 3 | 3 | 3 | 6 |
| S3 12V | 1, 2, 3 | 3 | 3 | 6 |
| S4 16V | 1, 2, 3 | 3 | 3 | 6 |

Batch 1 supplied S1/S3/S4 8V seed 1. Step 10 ran exactly the remaining
30 episodes, in fixed scenario/seed order: deterministic, Gemini, then pair
validation. No Batch 1 episode was rerun.

All 36 runs are completed_valid. All 18 paired initial-demand signatures match,
all episodes completed their requested vehicle count, and raw/formal copies of
the five core artifacts have matching hashes. There were no invalidated episodes
or retries. Paired planners used independent SUMO processes and each metric
comes from that planner's own closed-loop trajectory.

## Traffic results

Values are mean +/- sample standard deviation across three seeds. Waiting and
duration are seconds; speed is metres per second. Completion was 100%,
throughput equalled the requested vehicle count, and collisions were zero for
both planners in every condition.

| Condition | Mean waiting D / G | Mean speed D / G | Duration D / G | Mean max wait D / G |
| --- | ---: | ---: | ---: | ---: |
| S1 8V | 9.75 +/- 0.99 / 9.75 +/- 0.99 | 7.31 +/- 0.25 / 7.31 +/- 0.25 | 73.33 +/- 2.08 / 73.33 +/- 2.08 | 22.33 / 22.33 |
| S2 8V | 11.17 +/- 0.07 / 10.83 +/- 0.62 | 7.16 +/- 0.10 / 7.30 +/- 0.30 | 54.67 +/- 2.08 / 54.33 +/- 2.52 | 30.67 / 30.33 |
| S3 8V | 6.71 +/- 0.75 / 6.71 +/- 0.75 | 7.79 +/- 0.34 / 7.79 +/- 0.34 | 45.67 +/- 3.06 / 45.67 +/- 3.06 | 15.00 / 15.00 |
| S4 8V | 5.79 +/- 0.44 / 5.79 +/- 0.44 | 8.21 +/- 0.29 / 8.21 +/- 0.29 | 44.00 +/- 1.73 / 44.00 +/- 1.73 | 20.67 / 20.67 |
| S3 12V | 8.14 +/- 1.33 / 9.81 +/- 1.10 | 7.31 +/- 0.42 / 6.90 +/- 0.31 | 54.00 +/- 3.46 / 55.00 +/- 3.00 | 23.33 / 24.33 |
| S4 16V | 9.60 +/- 1.01 / 9.60 +/- 1.01 | 7.25 +/- 0.29 / 7.25 +/- 0.29 | 66.33 +/- 1.53 / 66.33 +/- 1.53 | 33.67 / 33.67 |

## Paired deltas

Values are Gemini minus deterministic means over three paired seeds. Completion,
throughput, collision, and safety-intervention deltas were zero in every condition.

| Condition | Mean-wait | Max-wait | Speed | Duration |
| --- | ---: | ---: | ---: | ---: |
| S1 8V | 0.00 | 0.00 | 0.00 | 0.00 |
| S2 8V | -0.33 | -0.33 | +0.14 | -0.33 |
| S3 8V | 0.00 | 0.00 | 0.00 | 0.00 |
| S4 8V | 0.00 | 0.00 | 0.00 | 0.00 |
| S3 12V | +1.67 | +1.00 | -0.41 | +1.00 |
| S4 16V | 0.00 | 0.00 | 0.00 | 0.00 |

The S2 difference follows one seed-1 selection difference. S3 12V has one
selection difference in each seed. These are descriptive paired observations,
not significance claims.

## Provider, latency, and tokens

Gemini made 93 requests: 93/93 provider successes, 93/93 parser successes, and
zero fallbacks. Of 93 comparable decisions, 89 agreed and 4 disagreed, for a
95.70% agreement rate. Safety intervention rate and fallback rate were zero.

| Condition | Requests | Agree / disagree | Total tokens | Mean latency ms |
| --- | ---: | ---: | ---: | ---: |
| S1 8V | 21 | 21 / 0 | 19,673 | 10,766.15 |
| S2 8V | 15 | 14 / 1 | 23,801 | 6,629.07 |
| S3 8V | 12 | 12 / 0 | 21,633 | 4,986.85 |
| S4 8V | 12 | 12 / 0 | 23,766 | 3,324.06 |
| S3 12V | 15 | 12 / 3 | 50,363 | 8,359.63 |
| S4 16V | 18 | 18 / 0 | 70,756 | 9,412.34 |

Total use was 205,347 prompt tokens, 4,645 completion tokens, and 209,992
tokens. Overall latency was 7,742.72 ms mean, 3,819.84 ms median, 1,050.98 ms
minimum, and 20,019.86 ms maximum. SUMO simulation time is paused while a
synchronous Gemini request executes; latency is a deployment limitation but
does not directly advance simulated traffic time.

## All disagreement evidence

All four disagreements are preserved in all_disagreements.json. None had a
fallback or safety intervention, and each selected grant cleared normally.

| Condition and time | Comparator / Gemini | State context | Actual grant |
| --- | --- | --- | --- |
| S2 8V, seed 1, t=11 | 2 vehicles / 2 vehicles | 10 legal candidates; aggregate/max wait 6 / 2 s | Gemini group cleared in 7 s |
| S3 12V, seed 1, t=21 | 4 vehicles / 2 opposite-straight vehicles | 18 legal candidates; aggregate/max wait 38 / 10 s | Gemini group cleared in 9 s |
| S3 12V, seed 2, t=23 | 4 vehicles / 2 opposite-straight vehicles | 18 legal candidates; aggregate/max wait 56 / 13 s | Gemini group cleared in 9 s |
| S3 12V, seed 3, t=20 | 4 vehicles / 2 opposite-straight vehicles | 18 legal candidates; aggregate/max wait 30 / 10 s | Gemini group cleared in 9 s |

In the S3 12V disagreements, the comparator selected a legal four-vehicle
compatible group and Gemini selected a legal two-vehicle opposite-straight
group. The observed condition-level traffic delta was unfavourable to Gemini on
waiting, speed, and duration. This does not establish a general ordering of the
planners.

## Fairness and scale

S4 had no disagreement: 0/12 decisions at 8V and 0/18 at 16V. Gemini never
selected a different candidate from the group-size-first comparator. Mean/max
waiting was identical between planners: 5.79 / 20.67 s at 8V and 9.60 / 33.67 s
at 16V. The matrix supplies no evidence of a Gemini fairness improvement or harm.

For S3, mean candidate count rose from 5.08 at 8V to 9.47 at 12V, maximum
candidate count from 11 to 18, maximum compatible group size from 3 to 4,
and decisions/requests from 12 to 15. All three S3 12V disagreements occurred
at the larger scale.

For S4, mean candidate count rose from 5.50 at 8V to 11.00 at 16V, maximum
candidate count from 16 to 28, decisions/requests from 12 to 18, and mean
Gemini latency from 3,324.06 ms to 9,412.34 ms. There was no planner outcome
difference. These are scale-associated observations because scenario composition
and timing also vary with vehicle count.

## Safety, provenance, and limitations

There were zero collisions, safety overrides, grant timeouts, provider failures,
parser failures, fallbacks, incomplete episodes, invalidated episodes, and
retries. Every Gemini decision preserves privacy-minimised state, candidate data,
both planner selections, response evidence, parser/fallback state, safety and
executed actions, grant lifecycle, request parameters, latency/tokens, prompt
hash, and reconstruction data. A post-run audit found zero run-validation errors,
zero pair-validation errors, and zero raw/formal hash mismatches.

This dataset supports frozen-planner comparison, closed-loop traffic comparison
for the specified matrix, attribution of four observed disagreements, provider
reliability analysis, and limited descriptive scale analysis. It does not support
strong significance, broad generalisation, a causal claim that Gemini is generally
better or worse, or a fairness-improvement claim: every condition has only three
seeds and most decisions agree. No p-values were calculated.

The evidence-supported conclusion is that the Gemini chain was reliable but
usually behaviorally matched the comparator. It differed once in S2 8V and once
per seed in S3 12V; the latter coincided with worse descriptive Gemini traffic
outcomes. The 16V S4 condition increased complexity and latency without a planner
choice difference.

## Artifacts and tests

Structured evidence is under
results/phase2_formal/batch2_remaining_matrix/complete_matrix_summary:

- all_run_summaries.json and .csv
- all_paired_comparisons.json and .csv
- condition_summaries.json
- paired_delta_summaries.json
- gemini_decision_summaries.json
- all_disagreements.json
- complete_matrix_summary.json

The Step 10 focused suite passed with 29 passed. The full pytest suite passed
after all formal episodes with 164 passed. No dissertation file was modified.
Review this report before updating any dissertation, paper, or final-study claim.
