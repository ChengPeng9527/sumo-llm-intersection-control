# S3 Same-State R4 versus S2 Counterfactual Preregistration

## Research question and boundary

RQ-CF asks: from the same pre-decision traffic and controller state, what downstream closed-loop consequences follow from executing the observed legal Gemini S2 choice rather than the legal deterministic-comparator R4 choice?

This supplementary experiment estimates a local single-action intervention effect in three frozen historical states. It does not evaluate the full Gemini policy, establish planner superiority, or support population-level or real-world claims. Gemini is not called.

## Technical gate

Scientific branching is permitted only because `replay_equivalence_attempt3` passed `REPLAY_EQUIVALENT` with exact discrete equality and the preregistered absolute numerical tolerance `1e-6`. The runner revalidates this retained gate before creating output.

## Frozen historical states

All states are the first shared Phase 2 S3-12V disagreement epoch. Frozen deterministic and Gemini records must have identical privacy-minimised state, candidate features, and candidate set.

| Seed | Epoch | Time (s) | R4 source | R4 candidate ID | S2 source | S2 candidate ID |
|---:|---:|---:|---|---|---|---|
| 1 | 3 | 21.0 | `DETERMINISTIC_R4` | `phase2_s3_cooperative_opportunity_v12_seed1_1_10|phase2_s3_cooperative_opportunity_v12_seed1_1_11|phase2_s3_cooperative_opportunity_v12_seed1_1_8|phase2_s3_cooperative_opportunity_v12_seed1_1_9` | `OBSERVED_GEMINI_S2` | `phase2_s3_cooperative_opportunity_v12_seed1_1_4|phase2_s3_cooperative_opportunity_v12_seed1_1_5` |
| 2 | 3 | 23.0 | `DETERMINISTIC_R4` | `phase2_s3_cooperative_opportunity_v12_seed2_2_10|phase2_s3_cooperative_opportunity_v12_seed2_2_11|phase2_s3_cooperative_opportunity_v12_seed2_2_8|phase2_s3_cooperative_opportunity_v12_seed2_2_9` | `OBSERVED_GEMINI_S2` | `phase2_s3_cooperative_opportunity_v12_seed2_2_4|phase2_s3_cooperative_opportunity_v12_seed2_2_5` |
| 3 | 3 | 20.0 | `DETERMINISTIC_R4` | `phase2_s3_cooperative_opportunity_v12_seed3_3_11|phase2_s3_cooperative_opportunity_v12_seed3_3_10|phase2_s3_cooperative_opportunity_v12_seed3_3_9|phase2_s3_cooperative_opportunity_v12_seed3_3_8` | `OBSERVED_GEMINI_S2` | `phase2_s3_cooperative_opportunity_v12_seed3_3_4|phase2_s3_cooperative_opportunity_v12_seed3_3_5` |

R4 must be a legal four-vehicle all-RIGHT candidate and S2 a legal two-vehicle opposite-STRAIGHT candidate. Any provenance, candidate, checkpoint, or configuration mismatch fails closed.

## Matrix and intervention

The matrix is three historical states by two continuations: six scientific continuation runs. One technical checkpoint-preparation session is required per seed. Both branches load the same saved SUMO, controller, and experiment checkpoint. Checkpoint hashes, candidate-set hash, time, epoch, active grant, and configuration hashes must match.

At epoch 3, each branch forces its preregistered legal candidate exactly once. After that grant, every later selection uses the unchanged deterministic comparator. A missing or illegal candidate, repeated force, second forced action, or non-deterministic post-force selection invalidates the run.

## Outcomes

Primary outcomes, in fixed order, are:

1. episode completion;
2. total and mean waiting;
3. maximum waiting;
4. episode duration.

Secondary outcomes are waiting sample SD, per-approach waiting, mean speed, throughput, arrival sequence/time, subsequent decision count and selections, collisions, safety interventions, and grant timeouts.

The paired unit is seed. Results report R4, S2, and S2-minus-R4 for each seed, plus descriptive three-seed mean differences for mean waiting, maximum waiting, duration, and mean speed. No inferential test or population-level conclusion is preregistered.

## Interpretation rules

Rules are applied only if all three pairs are valid:

- `MINIMAL_SYSTEM_CONSEQUENCE`: completion is identical and all four numeric primary fields (total waiting, mean waiting, maximum waiting, and duration) are equal within `1e-6` for every seed.
- `S2_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES`: in every seed, S2 completion is no lower, all numeric primary outcomes are no higher within `1e-6`, and at least one primary outcome is strictly better beyond `1e-6` in that seed.
- `R4_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES`: the symmetric rule favouring R4.
- `MIXED_TRADEOFF`: all pairs are valid but none of the preceding rules applies.
- `INCONCLUSIVE`: fewer than three valid matched pairs or incomplete required evidence.

An allowed conclusion is limited to downstream differences from forcing the observed S2 rather than R4 within these three replayed historical states. Claims that Gemini generally improves traffic, is superior, optimises fairness, provides a general causal effect, or improves real-world safety are prohibited.

## Evidence namespace

All outputs are written under `results/counterfactual_validation/s3_r4_vs_s2_branches/`. Existing replay-equivalence and frozen Phase 1/2/3 evidence are not modified. Existing output causes fail-closed termination; there is no retry or overwrite policy.
