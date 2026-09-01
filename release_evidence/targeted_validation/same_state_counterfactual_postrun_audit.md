# Same-State Counterfactual Post-Run Scientific Audit

## Scope and evidence boundary

This is a post-run audit of the completed S3-12V same-state counterfactual
study under `results/counterfactual_validation/s3_r4_vs_s2_branches/`. It
does not modify the preregistration, replay-equivalence evidence, raw branch
records, or frozen Phase 1/2/3 evidence. No SUMO run or provider request was
made during this audit.

The intervention is local and deliberately narrow: from each frozen first
S3-12V disagreement state, execute either the deterministic comparator's
legal four-vehicle all-RIGHT group (R4) or the observed Gemini legal
two-vehicle opposite-STRAIGHT group (S2) exactly once. Every later decision
uses the unchanged deterministic comparator. This is not a comparison of two
complete planner policies.

Vehicle identifiers below are abbreviated to their final numeric suffix. The
full canonical IDs remain in the raw records and preregistration.

## Evidence integrity

- Historical seeds are exactly 1, 2, and 3; each contains exactly one R4 and
  one S2 continuation, for six scientific continuation runs.
- Every required checkpoint, branch metadata, decision, grant, step,
  trajectory, loaded-identity, and summary artefact is present. No branch
  failure artefact is present.
- The recomputed SHA-256 values of `sumo_state.xml`,
  `controller_state.json`, `experiment_state.json`, and
  `checkpoint_metadata.json` match each seed's retained checkpoint hashes.
- Within each seed, R4 and S2 use the same checkpoint hashes, configuration
  hashes, candidate-set hash, simulation time, and decision epoch.
- Loaded checkpoint identities contain no discrete mismatch. The largest
  numeric load difference is `2.22e-16` in seed 1, `0` in seed 2, and
  `4.44e-16` in seed 3, all below the preregistered `1e-6` tolerance.
- Each checkpoint contains 18 legal candidates. Both forced candidate IDs
  are members of the same retained candidate set and are marked legal.
- Each branch contains exactly one forced decision. Every decision after the
  intervention has source `DETERMINISTIC_COMPARATOR`; no second forced action
  is present.
- Every branch records `provider_calls = 0`. The study does not call Gemini.
- All six runs complete with 12/12 throughput, zero collisions, zero safety
  interventions, and zero grant timeouts.

Accordingly, all three seed pairs are valid same-state comparisons.

## Intervention verification

| Seed | Checkpoint time / epoch | Candidate-set hash | R4 candidate | S2 candidate | Both legal | Same pre-state | Forced actions | Post-force policy |
|---:|---:|---|---|---|---|---|---:|---|
| 1 | 21 s / 3 | `67CDBE...B3E6` | `10|11|8|9` | `4|5` | Yes | Yes, max load difference `2.22e-16` | 1 per branch | Deterministic comparator |
| 2 | 23 s / 3 | `809791...6953` | `10|11|8|9` | `4|5` | Yes | Yes, exact retained JSON identity | 1 per branch | Deterministic comparator |
| 3 | 20 s / 3 | `CD22E0...D21A` | `11|10|9|8` | `4|5` | Yes | Yes, max load difference `4.44e-16` | 1 per branch | Deterministic comparator |

The design therefore compares `same state -> R4 once` with
`same state -> S2 once`; it does not compare independently evolved starting
trajectories.

## Primary outcomes

Differences are S2 minus R4. Waiting and duration are in seconds.

| Seed | Metric | R4 | S2 | S2-R4 |
|---:|---|---:|---:|---:|
| 1 | Completion | 1 | 1 | 0 |
| 1 | Total waiting | 97.000 | 115.000 | +18.000 |
| 1 | Mean waiting | 8.083 | 9.583 | +1.500 |
| 1 | Maximum waiting | 23.000 | 23.000 | 0.000 |
| 1 | Episode duration | 52.000 | 52.000 | 0.000 |
| 2 | Completion | 1 | 1 | 0 |
| 2 | Total waiting | 114.000 | 132.000 | +18.000 |
| 2 | Mean waiting | 9.500 | 11.000 | +1.500 |
| 2 | Maximum waiting | 27.000 | 27.000 | 0.000 |
| 2 | Episode duration | 58.000 | 58.000 | 0.000 |
| 3 | Completion | 1 | 1 | 0 |
| 3 | Total waiting | 82.000 | 106.000 | +24.000 |
| 3 | Mean waiting | 6.833 | 8.833 | +2.000 |
| 3 | Maximum waiting | 20.000 | 23.000 | +3.000 |
| 3 | Episode duration | 52.000 | 55.000 | +3.000 |

### Three-seed descriptive means

| Metric | Mean R4 | Mean S2 | Mean paired S2-R4 |
|---|---:|---:|---:|
| Completion | 1.000 | 1.000 | 0.000 |
| Total waiting (s) | 97.667 | 117.667 | +20.000 |
| Mean waiting (s) | 8.139 | 9.806 | +1.667 |
| Maximum waiting (s) | 23.333 | 24.333 | +1.000 |
| Episode duration (s) | 54.000 | 55.000 | +1.000 |

These are descriptive means over three historical matched states, not
population estimates.

## Secondary outcomes

| Seed | Branch | Waiting SD (s) | Mean speed | Throughput | Later decisions | Collisions | Safety interventions | Grant timeouts |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | R4 | 9.700 | 7.337 | 12 | 2 | 0 | 0 | 0 |
| 1 | S2 | 7.763 | 6.982 | 12 | 2 | 0 | 0 | 0 |
| 2 | R4 | 10.274 | 6.874 | 12 | 2 | 0 | 0 | 0 |
| 2 | S2 | 8.770 | 6.555 | 12 | 2 | 0 | 0 | 0 |
| 3 | R4 | 8.726 | 7.721 | 12 | 2 | 0 | 0 | 0 |
| 3 | S2 | 7.650 | 7.162 | 12 | 2 | 0 | 0 | 0 |

Mean speed is lower under S2 in every seed (paired differences
`-0.355`, `-0.319`, and `-0.559`; descriptive mean `-0.411`). Waiting sample
SD is also lower under S2 in every seed (mean R4 `9.567`, mean S2 `8.061`,
paired mean `-1.506 s`).

### Per-approach waiting

Cells are `total / mean / maximum` waiting in seconds.

| Seed | Branch | E | N | S | W |
|---:|---|---|---|---|---|
| 1 | R4 | 26 / 8.667 / 23 | 24 / 8.000 / 19 | 23 / 7.667 / 19 | 24 / 8.000 / 23 |
| 1 | S2 | 35 / 11.667 / 23 | 24 / 8.000 / 14 | 23 / 7.667 / 11 | 33 / 11.000 / 23 |
| 2 | R4 | 29 / 9.667 / 23 | 29 / 9.667 / 22 | 27 / 9.000 / 20 | 29 / 9.667 / 27 |
| 2 | S2 | 38 / 12.667 / 23 | 29 / 9.667 / 16 | 27 / 9.000 / 14 | 38 / 12.667 / 27 |
| 3 | R4 | 22 / 7.333 / 20 | 22 / 7.333 / 18 | 19 / 6.333 / 17 | 19 / 6.333 / 19 |
| 3 | S2 | 34 / 11.333 / 23 | 23 / 7.667 / 13 | 19 / 6.333 / 9 | 30 / 10.000 / 22 |

S2 redistributes waiting rather than uniformly increasing every approach. It
reduces the maximum waiting observed on the N/S approaches while increasing
E/W total and mean waiting, and it lowers the vehicle-level waiting SD. This
is an observed waiting-distribution trade-off; it is not evidence that Gemini
optimises fairness.

## Arrival order and time

The complete arrival sequences below use abbreviated vehicle suffixes.

| Seed | Branch | Arrival sequence |
|---:|---|---|
| 1 | R4 | 0, 2, 1, 3, 10, 8, 9, 11, 5, 4, 6, 7 |
| 1 | S2 | 0, 2, 1, 3, 5, 4, 10, 8, 9, 11, 6, 7 |
| 2 | R4 | 0, 1, 3, 2, 9, 11, 8, 10, 4, 5, 6, 7 |
| 2 | S2 | 0, 1, 3, 2, 4, 5, 9, 11, 10, 8, 6, 7 |
| 3 | R4 | 0, 1, 3, 2, 11, 8, 9, 10, 4, 5, 6, 7 |
| 3 | S2 | 0, 1, 3, 2, 4, 5, 8, 11, 9, 10, 6, 7 |

Relative to R4, forcing S2 advances vehicles 4/5 by 8--9 s but delays the
four right-turn vehicles 8--11 by 8--10 s. In seed 3, vehicles 6/7 also arrive
3 s later under S2, producing the observed duration difference. Exact arrival
times remain in each branch `summary.json`.

## Temporal consequence of the intervention

| Seed | Forced time | First trajectory divergence | Next deterministic epoch: R4 branch | Next deterministic epoch: S2 branch | Final later selection | Reconvergence |
|---:|---:|---:|---|---|---|---|
| 1 | 21 s | 22 s | 30 s: S2 from 6 candidates | 30 s: R4 from 15 candidates | 39 s: vehicles 6/7 in both | Active trajectory state equal again at 48 s; difference persists 26 s from 22--47 s |
| 2 | 23 s | 24 s | 32 s: S2 from 6 candidates | 32 s: R4 from 15 candidates | 41 s: vehicles 6/7 in both | Active trajectory state equal again at 50 s; difference persists 26 s from 24--49 s |
| 3 | 20 s | 21 s | 28 s: S2 from 6 candidates | 29 s: R4 from 15 candidates | R4 36 s / S2 39 s: vehicles 6/7 | No complete reconvergence before R4 ends at 52 s; S2 ends at 55 s |

The immediate mechanism supported by the records is queue-order propagation,
not model-internal reasoning. R4 releases vehicles 8--11 first and the next
deterministic epoch releases 4/5; S2 reverses that order. The branch-specific
active vehicles produce different candidate-set sizes at the next epoch
(6 versus 15), altered arrival order, and, in seed 3, a three-second shift in
the final deterministic grant. Thus one different legal intervention changes
the subsequent deterministic state even though both branches use the same
policy after the intervention.

## Preregistered classification

The retained result **strictly satisfies
`R4_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES`**:

- completion is equal in every seed;
- R4 total waiting and mean waiting are lower in every seed;
- R4 maximum waiting and duration are no higher in every seed; and
- each seed has at least one strict primary-outcome improvement beyond
  `1e-6`.

The category was frozen before execution and has not been altered.

## Claim audit

| Claim | Status | Audit basis |
|---|---|---|
| A. Gemini produced genuine legal selections distinct from the deterministic comparator. | **SUPPORTED** | Frozen Phase 2 retains 93 valid selections, including four legal disagreements; three share the S3 R4/S2 structure. |
| B. Those differences are repeatably sensitive to aggregate waiting in the controlled fixed-state probe. | **SUPPORTED, bounded** | W08 selected R4 5/5; W19/W20/W24 selected S2 15/15 under the fixed-state protocol. |
| C. Gemini therefore improves traffic. | **NOT_SUPPORTED** | Selection difference is not effectiveness; the tested S2 interventions worsened primary outcomes relative to R4. |
| D. The observed Gemini S2 choice produced better downstream outcomes than R4 in the three historical disagreement states. | **NOT_SUPPORTED** | The retained result is the opposite on the preregistered primary outcomes. |
| E. R4 produced better downstream primary outcomes in all three tested same-state interventions. | **SUPPORTED, bounded** | All three valid pairs satisfy the frozen R4-consistently-better rule. |
| F. The deterministic comparator is generally superior to Gemini. | **NOT_SUPPORTED** | Three local interventions do not evaluate either complete policy or generalise across states/topologies. |
| G. The LLM is unnecessary for all intersection-control problems. | **NOT_SUPPORTED** | The experiment covers three historical states in one simulated topology. |
| H. Additional latency/provider dependence was justified by demonstrated traffic benefit. | **NOT_SUPPORTED** | No traffic benefit from the observed S2 intervention was demonstrated in these states. |

## Dissertation-ready wording

### Results

> A preregistered same-state counterfactual analysis replayed the first S3-12V planner-disagreement state for each of three historical seeds. From an identical checkpoint, either the deterministic comparator's legal four-vehicle all-right group (R4) or Gemini's observed legal two-vehicle opposite-straight group (S2) was applied once, after which both branches used the deterministic comparator. All six continuations completed without collision, safety intervention, or grant timeout. Relative to R4, S2 increased total waiting by 18, 18, and 24 s and mean waiting by 1.5, 1.5, and 2.0 s across seeds 1--3; maximum waiting and duration were unchanged in seeds 1--2 and each increased by 3 s in seed 3. The result therefore met the preregistered classification R4_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES.

### Discussion

> The supplementary evidence separates behavioural distinctiveness from operational benefit. Gemini made genuine legal selections that differed from the deterministic comparator, and fixed-state probes showed a repeatable association between aggregate waiting information and the R4/S2 selection distribution. However, when the observed S2 choice was isolated in three matched SUMO states, it did not improve the preregistered primary traffic outcomes: R4 produced lower total and mean waiting in every pair and no worse completion, maximum waiting, or duration. S2 reduced waiting dispersion and advanced the selected straight-moving vehicles, but shifted additional waiting to other approaches. These local results do not establish general deterministic superiority; they show that the incremental LLM choice was behaviourally distinct yet not operationally beneficial in the three tested disagreement states.

### Limitation

> The counterfactual result is limited to three replayed disagreement states from one S3-12V SUMO topology and a single forced decision followed by deterministic control; it neither evaluates the complete Gemini policy nor supports population-level, fairness-optimisation, real-world-safety, or general planner-superiority claims.

## Final research decision

**`STOP_SUPPLEMENTARY_EXPERIMENTS`.** The current sequence answers the bounded
incremental-contribution question: legal LLM divergence exists and is
repeatably associated with aggregate waiting in a controlled fixed state, but
the observed S2 intervention does not provide traffic benefit in the three
matched historical states. Remaining generalisation questions would require a
new research phase rather than a low-risk gap-closing supplement and are not
needed to interpret the current dissertation evidence.
