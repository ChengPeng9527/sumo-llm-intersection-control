# Phase 2 Step 7 Targeted Scenario Pilot Report

## Scope and status

Step 7 evaluates whether the existing single-intersection network can produce reproducible, decision-rich mixed-turn states for a fair comparison between the deterministic cooperative comparator and the frozen Gemini candidate selector. It does not run the formal experiment campaign and makes no planner-superiority claim.

Status: `STEP7_SCENARIO_PILOT_COMPLETE`

## Existing architecture audit

- The existing `net.net.xml` contains legal lane connections for all 12 Phase 2 LEFT, STRAIGHT, and RIGHT routes. No new network is required.
- Historical density generation uses a seeded weighted route draw and seeded integer departure gaps. Explicit vehicle counts already support 8V and 16V, and now support targeted 12V without changing Phase 1 behavior.
- Random density generation could not guarantee clustered arrivals, exact mixed-turn composition, or fairness pressure. The existing generator was therefore extended with explicit targeted route/departure cycles rather than replaced.
- Targeted route/departure plans are deterministic for a fixed seed. S1 and S3 use at most one second of seed-controlled departure jitter; S2 and S4 use exact departure offsets.
- The legacy full-run LLM controller still uses the historical per-vehicle decision interface. The Step 7 pilot therefore reuses the Step 5 candidate pipeline directly rather than silently reverting to the old interface.
- Candidate states are observed from real SUMO execution under the native signal and car-following behavior. Planner actions are evaluated through the existing candidate-to-action and safety pipeline but are not actuated during this pilot. These results are therefore Layer 1 Offline Paired Decision Analysis evidence only; they are not causal traffic-controller performance evidence.

## Targeted scenario definitions

All templates use two vehicles per incoming approach in their base 8V cycle. Higher counts repeat the explicit cycle in a later wave.

| Scenario | 8V route cycle | Base departure offsets (s) | Intended pressure |
|---|---|---|---|
| S1 `BALANCED_MIXED_TURN` | `N_W, E_W, S_W, W_N, N_S, E_N, S_N, W_E` | `0, 3, 6, 9, 12, 15, 18, 21` | Balanced approaches, all three movement classes, moderate separation |
| S2 `SIMULTANEOUS_CONFLICT` | `N_S, E_W, S_N, W_E, N_E, E_S, S_W, W_N` | `0, 0, 1, 1, 2, 2, 3, 3` | Four-approach arrival cluster with small ETA differences and conflicting alternatives |
| S3 `COOPERATIVE_OPPORTUNITY` | `N_W, E_N, S_E, W_S, N_S, S_N, E_S, W_N` | `0, 0, 1, 1, 3, 3, 5, 5` | Four compatible right turns plus competing compatible straight/left opportunities |
| S4 `FAIRNESS_PRESSURE` | `N_E, E_N, S_E, W_S, N_W, E_W, S_N, W_E` | `0, 0, 1, 1, 2, 2, 3, 3` | Waiting `N_E` left turn competing with larger compatible groups |

Each generated scenario records its stable scenario class, vehicle count, seed, exact route sequence, exact departure times, movement sequence, and SUMO configuration path.

## Deterministic SUMO observer pilot

Candidate-set counts below are controlled SUMO time-step decisions, not duplicated per-vehicle log rows.

| Scenario/scale | Completed | Candidate decisions | Multiple-candidate sets | Multi-vehicle opportunity sets | Max candidates | Mean candidates | Mean group size | Max group | Richness ratio | Cooperative ratio | Fairness states | Label |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| S1 8V | 8/8 | 45 | 37 | 24 | 8 | 4.356 | 1.158 | 2 | 0.822 | 0.533 | 0 | MEDIUM |
| S2 8V | 8/8 | 49 | 45 | 45 | 12 | 6.265 | 1.326 | 2 | 0.918 | 0.918 | 0 | MEDIUM |
| S3 8V | 8/8 | 42 | 41 | 41 | 16 | 7.643 | 1.464 | 4 | 0.976 | 0.976 | 0 | HIGH |
| S4 8V | 8/8 | 47 | 42 | 39 | 17 | 6.149 | 1.398 | 4 | 0.894 | 0.830 | 30 | HIGH |
| S3 12V | 12/12 | 43 | 41 | 41 | 31 | 16.023 | 1.840 | 6 | 0.953 | 0.953 | 0 | HIGH |
| S4 16V | 16/16 | 48 | 45 | 44 | 34 | 17.021 | 1.758 | 6 | 0.938 | 0.917 | 30 | HIGH |

All six runs completed with zero observed collisions and zero safety interventions in the evaluated candidate traces.

The richness labels use a transparent rule: HIGH requires at least 0.8 multiple-candidate ratio, at least 0.5 cooperative-opportunity ratio, and a compatible group of at least three vehicles; MEDIUM requires at least 0.5 richness, at least one cooperative opportunity, and more than one candidate. S1 and S2 are useful despite their MEDIUM label because they present frequent legal alternatives while limiting maximum compatible groups to two.

## Targeted scale decision

- S3 12V is retained because maximum candidate count increased from 16 to 31 and maximum compatible group size increased from 4 to 6.
- S4 16V is retained because maximum candidate count increased from 17 to 34 and maximum compatible group size increased from 4 to 6 while preserving 30 fairness-pressure states.
- Other 12V/16V combinations were not run because the two selected validations already answer whether scale can materially increase candidate richness. A symmetric sweep would add cost without a new Step 7 question.

## Test validation

- Focused Step 7: `7 passed`.
- Directly affected generator/candidate/comparator/provider/metrics regression: `41 passed`.
- Final full suite: `148 passed`.
- Additional final Step 7 plus Gemini guard check: `13 passed`.

The focused tests verify fixed-seed reproducibility, S2 timing clusters, S3 compatible mixed-turn groups, S4 waiting-pressure structure, exact 8V/12V/16V counts, valid route IDs and movements, unchanged Phase 1 density behavior, and candidate-decision metric denominators.

## Gemini live pilot

Exactly one representative 8V state per S1-S4 scenario was sent through the frozen Step 5/6 path. The payload contained only the authorized local traffic state and safe candidate features. No origin, destination, route history, complete navigation route, credential, dissertation content, or unrelated repository data was sent.

Provider: `Gemini`

Model: `gemini-3.6-flash`

| Scenario | Candidates | HTTP/provider success | Parser | Fallback | Latency (ms) | Prompt tokens | Completion tokens | Total tokens | Comparator agreement | Safety interventions |
|---|---:|---|---|---|---:|---:|---:|---:|---|---:|
| S1 8V | 8 | success / 200 | success | no | 1664.18 | 2622 | 51 | 2673 | yes | 0 |
| S2 8V | 6 | success / 200 | success | no | 2459.57 | 1949 | 55 | 2004 | yes | 0 |
| S3 8V | 16 | success / 200 | success | no | 2250.21 | 5364 | 91 | 5455 | yes | 0 |
| S4 8V | 5 | success / 200 | success | no | 1738.40 | 1651 | 49 | 1700 | yes | 0 |

Aggregate live evidence:

- Requests: `4`
- Provider success: `4/4` (`100%`)
- Parser success: `4/4` (`100%`)
- Fallback: `0/4` (`0%`)
- Comparable decisions: `4`
- Agreement: `4/4` (`100%`)
- Disagreement: `0/4` (`0%`)
- Safety interventions: `0`
- Latency: minimum `1664.18 ms`, mean `2028.09 ms`, maximum `2459.57 ms`
- Prompt tokens: total `11586`, mean `2896.5`
- Completion tokens: total `246`, mean `61.5`
- Total tokens: total `11832`, mean `2958.0`

There are no representative live disagreement cases to report. The S4 representative state included a non-selected fairness-target left turn with 32 seconds waiting, but both planners selected the same legal two-vehicle group. Four agreements do not prove policy equivalence or superiority.

## Scenario usefulness assessment

- S1 is a useful mixed-turn reference: 82.2% of candidate decisions had multiple alternatives, but cooperative groups remained small.
- S2 successfully creates an explicit three-second departure cluster: 91.8% of candidate decisions had multiple alternatives and 91.8% offered a multi-vehicle candidate. The persisted pilot's representative TTI spread of zero was caused by fewer than two finite ETA values and must not be interpreted as measured simultaneous arrival. Step 8 corrects future selection so TTI spread is used only when at least two finite ETAs exist.
- S3 most clearly exposes throughput/cooperation choice: 97.6% cooperative-opportunity ratio and a four-vehicle candidate at 8V.
- S4 creates reproducible fairness pressure: 30 observed states met the configured waiting-pressure condition while legal larger-group alternatives existed.
- Usefulness is based on candidate choice, not on whether Gemini disagreed with or outperformed the comparator.

## Proposed formal Phase 2 matrix

Do not execute this matrix as part of Step 7.

Controller conditions:

1. Deterministic Cooperative Comparator using the frozen Step 4 ranking.
2. Gemini Candidate Selector using `gemini-3.6-flash`, the same candidate universe, Step 4 fallback, and existing safety final authority.

Scenario/scale conditions:

- S1 8V
- S2 8V
- S3 8V
- S4 8V
- S3 12V targeted scale extension
- S4 16V targeted scale extension

Use seeds `1, 2, 3` for each condition. This produces `6 conditions x 3 seeds x 2 planners = 36` paired planner evaluations: 18 deterministic and 18 Gemini.

The formal method is two-layer. Layer 1 evaluates both planners on the same recorded state and exact candidate groups for attribution metrics. Layer 2 starts independent SUMO episodes from the same scenario, seed, routes, and departures, applies each planner's grants to its own trajectory, and measures causal traffic outcomes. Observer completion/collision checks remain scenario-validity metrics only; closed-loop completion, throughput, waiting, speed, duration, and collisions are controller outcomes. The Step 8 readiness report defines the closed-loop lifecycle.

## Projected request and token budget

The six seed-7 observer runs produced 274 candidate-bearing time steps, or 42 to 49 per scenario episode. Applying that dense observer cadence to three seeds gives `822` Gemini requests, but this is not a valid closed-loop request estimate. Step 8 calls Gemini once per persistent passage grant and recalculates the closed-loop budget from grant decisions.

Using the actual Step 7 live averages:

- Approximate prompt tokens: `822 x 2896.5 = 2,380,923`
- Approximate completion tokens: `822 x 61.5 = 50,553`
- Approximate total tokens: `2,431,476`
- Planning total with 25% headroom for larger 12V/16V prompts: approximately `3,039,345` tokens

This is a token/request budget, not a monetary-cost claim. No frozen price evidence exists in the repository. A pre-formal dry-run should confirm the actual sampling rule and 12V/16V prompt sizes before spending this budget.

## Research validity assessment

- Scenario distinction: acceptable. Arrival dispersion, conflict clustering, compatible group size, and fairness pressure differ measurably.
- Decision choice: acceptable. Every 8V scenario has a candidate-richness ratio above 0.82.
- Baseline strength/fairness: acceptable. The deterministic comparator is unchanged and receives the exact same states and candidates as Gemini.
- Candidate conservatism: not currently blocking. Multi-candidate and cooperative opportunities are frequent, although the route-level model remains conservative for mixed movement pairs.
- Safety masking: not observed. Safety intervention count was zero in deterministic observations and live selections.
- Fallback attribution: acceptable in the pilot. Live fallback was zero.
- Reproducibility: acceptable. Demand is explicit and fixed-seed tests pass.
- Planner distinction: unresolved. The four live selections all agreed, so the formal evaluation must remain an attribution study rather than assume disagreement or LLM benefit.

## Efficiency, limitations, and deferred improvements

- An initial closed-loop comparator pilot exposed per-step candidate switching that prevented some scenarios from completing. Changing comparator policy or inventing candidate locking was out of scope, so the corrected pilot uses paired observer states and records this boundary explicitly.
- The first live execution approval was rejected before any request because external payload authorization needed to be more explicit. After explicit approval, exactly four requests were sent; the completed deterministic runs were reused rather than repeated.
- The pilot uses one live seed and one representative state per 8V scenario. It establishes operability, not reliability confidence or statistical significance.
- Higher-scale S3/S4 states were validated deterministically but were not sent to Gemini.
- Candidate compatibility remains route-based rather than lane/trajectory-based. Repeated same-route vehicles can enlarge compatible groups; formal interpretation must not equate route compatibility with simultaneous physical occupancy.
- Step 8 adds closed-loop candidate persistence/actuation and a grant-based request cadence without changing the frozen candidate, comparator, provider, or safety methods. Statistical power, pricing, prompt tuning, model comparison, and dissertation updates remain deferred.
- `docs/dissertation/` was not modified.
