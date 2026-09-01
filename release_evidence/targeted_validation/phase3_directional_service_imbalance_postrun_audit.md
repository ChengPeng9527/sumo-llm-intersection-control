# Phase 3 Directional Service-Imbalance Stage 2 Post-Run Audit

## Evidence boundary

This report audits the completed, independently executed Stage 2 evidence under
`results/phase3_directional_service_imbalance/`. It makes no provider request,
runs no SUMO episode, and does not modify the preregistration, raw outputs, or
frozen Phase 1/2/3 evidence. All comparisons are descriptive for three matched
seeds.

## Strict validity and matching

The Stage 2 manifest contains exactly one Gemini episode for each fixed seed
1, 2, and 3. There are no replacement run directories or failure artefacts.
Each episode completed with 16/16 vehicles and termination reason
`ALL_VEHICLES_COMPLETED`. The Gemini and deterministic run for each seed retain
the same scenario identity and the same `initial_demand_signature`:

| Seed | Initial-demand signature | Logical requests | Provider success | Parser success | Fallback | Legal selections | LLM-valid decisions | LLM episode valid |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `FB9A1668585FE88AE98C626E450D87A6E9A7C4656CA7CDB92799F53CE1720BE1` | 5 | 5 | 5 | 0 | 5 | 5 | true |
| 2 | `0A95AFC2E679466C31363277AA686BE955B2F4BC6CD8A6CF068A49F5CBDA7C02` | 5 | 5 | 5 | 0 | 5 | 5 | true |
| 3 | `3389EBBFE6F540C71E460AB471E2FFFD6B24ABB5339B06EFD8B8233C81C5C946` | 5 | 5 | 5 | 0 | 5 | 5 | true |

All 15 decision records retain raw model output, and every selected candidate
is in its recorded legal candidate set. Therefore all **3/3 matched pairs** are
eligible for the preregistered descriptive comparison. The run metadata does
not contain populated network/config/route hash values; scenario identity,
fixed runner construction, vehicle count, seed, and initial-demand signatures
provide the retained pairing evidence.

## Primary outcomes

All deltas are Gemini minus deterministic; lower is better for every field in
this table.

| Seed | Metric | Deterministic | Gemini | Delta |
|---:|---|---:|---:|---:|
| 1 | Total waiting (s) | 137.00 | 128.00 | -9.00 |
| 1 | Mean waiting (s) | 8.5625 | 8.0000 | -0.5625 |
| 1 | Episode duration (s) | 61.00 | 58.00 | -3.00 |
| 1 | Maximum vehicle waiting (s) | 32.00 | 28.00 | -4.00 |
| 1 | P95 vehicle waiting (s) | 32.00 | 28.00 | -4.00 |
| 1 | Maximum approach mean waiting (s) | 8.75 | 10.00 | +1.25 |
| 1 | Approach waiting range (s) | 0.50 | 4.00 | +3.50 |
| 2 | Total waiting (s) | 159.00 | 149.00 | -10.00 |
| 2 | Mean waiting (s) | 9.9375 | 9.3125 | -0.6250 |
| 2 | Episode duration (s) | 66.00 | 61.00 | -5.00 |
| 2 | Maximum vehicle waiting (s) | 36.00 | 30.00 | -6.00 |
| 2 | P95 vehicle waiting (s) | 33.00 | 27.00 | -6.00 |
| 2 | Maximum approach mean waiting (s) | 10.25 | 11.25 | +1.00 |
| 2 | Approach waiting range (s) | 0.75 | 4.00 | +3.25 |
| 3 | Total waiting (s) | 122.00 | 112.00 | -10.00 |
| 3 | Mean waiting (s) | 7.6250 | 7.0000 | -0.6250 |
| 3 | Episode duration (s) | 62.00 | 57.00 | -5.00 |
| 3 | Maximum vehicle waiting (s) | 30.00 | 25.00 | -5.00 |
| 3 | P95 vehicle waiting (s) | 29.25 | 24.25 | -5.00 |
| 3 | Maximum approach mean waiting (s) | 8.00 | 9.50 | +1.50 |
| 3 | Approach waiting range (s) | 0.75 | 4.75 | +4.00 |

### Three-seed descriptive means

| Metric | Deterministic mean | Gemini mean | Mean paired delta |
|---|---:|---:|---:|
| Total waiting (s) | 139.3333 | 129.6667 | -9.6667 |
| Mean waiting (s) | 8.7083 | 8.1042 | -0.6042 |
| Episode duration (s) | 63.0000 | 58.6667 | -4.3333 |
| Maximum vehicle waiting (s) | 32.6667 | 27.6667 | -5.0000 |
| P95 vehicle waiting (s) | 31.4167 | 26.4167 | -5.0000 |
| Maximum approach mean waiting (s) | 9.0000 | 10.2500 | +1.2500 |
| Approach waiting range (s) | 0.6667 | 4.2500 | +3.5833 |

## Secondary outcomes and safety

| Seed | Mean speed D/G (m/s) | Waiting SD D/G (s) | Eligible-not-selected D/G | Longest non-service D/G | Completion and throughput | Collisions | Safety interventions | Grant timeouts |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 1 | 7.0732 / 7.1002 | 12.8839 / 9.1506 | 3 / 1 | 3 / 1 | 1.0 and 16 / 1.0 and 16 | 0 / 0 | 0 / 0 | 0 / 0 |
| 2 | 6.6482 / 6.7221 | 13.3340 / 9.1704 | 3 / 1 | 3 / 1 | 1.0 and 16 / 1.0 and 16 | 0 / 0 | 0 / 0 | 0 / 0 |
| 3 | 7.3968 / 7.2933 | 12.5107 / 8.1158 | 3 / 1 | 3 / 1 | 1.0 and 16 / 1.0 and 16 | 0 / 0 | 0 / 0 | 0 / 0 |

Mean speed changes are small and mixed. Waiting dispersion, the number of
eligible-but-not-selected epochs, and the longest non-service sequence are
lower in every Gemini episode. No safety event distinguishes the planners.

## Planner mechanism

The deterministic and Gemini trajectories are shared through decision epoch 2
in each seed. At decision epoch 3, while the exact S2 target is legal and a
larger legal group is also available, the planners first diverge. Comparisons
after this point are full-policy trajectory observations, not same-state
counterfactuals.

| Seed | Deterministic S2 waiting progression (aggregate s) | Deterministic first S2 service | Gemini S2 waiting progression (aggregate s) | Gemini first S2 service | Earlier by |
|---:|---|---|---|---|---:|
| 1 | 2, 20, 38, 56 | epoch 5, 39 s, aggregate 56 s | 2, 20 | epoch 3, 21 s, aggregate 20 s | 18 s |
| 2 | 2, 24, 42, 60 | epoch 5, 41 s, aggregate 60 s | 2, 24 | epoch 3, 23 s, aggregate 24 s | 18 s |
| 3 | 3, 19, 35, 55 | epoch 5, 38 s, aggregate 55 s | 3, 19 | epoch 3, 20 s, aggregate 19 s | 18 s |

At epoch 2 both planners select the same legal three-vehicle group and leave
S2 unserved. At epoch 3 the deterministic comparator selects an available
four-vehicle RIGHT group, whereas Gemini selects the legal two-vehicle
opposite-STRAIGHT S2 group. Gemini therefore serves S2 18 s earlier in all
three runs and reduces both non-service measures from 3 to 1. The divergence
temporally precedes the observed outcome differences, but this temporal chain
does not reveal Gemini's internal reasoning and does not isolate a single
action effect across the remaining full-policy trajectory.

## Preregistered classification

Each seed meets the efficiency-improvement rule: at least two of total waiting,
mean waiting, and duration improve by their frozen margins, with no material
efficiency degradation. The service-distribution rule is not met in any seed:
maximum and P95 waiting improve, but maximum approach mean and approach range
worsen by at least 1 s. Consequently, the unique frozen classification is:

**`EFFICIENCY_ONLY_BENEFIT`**

This is not `MULTI_DOMAIN_BENEFIT`: the evidence shows lower extreme
vehicle-level waiting alongside greater between-approach imbalance.

## Relationship to the historical same-state counterfactual

The historical result `R4_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES` concerns a
single forced R4-versus-S2 action from each identical historical checkpoint,
followed by the same deterministic continuation. This Stage 2 result compares
independent complete closed-loop policies over multiple decisions in a new,
preregistered directional stress condition. A single S2 intervention can have
an immediate local efficiency cost while a continuing policy that services S2
earlier and then makes later decisions can produce a different cumulative
trajectory. The two studies therefore answer different questions and are not
contradictory. Neither result generalises to universal planner superiority.

## Claim audit

| Claim | Status | Evidence boundary |
|---|---|---|
| A. Gemini produces genuine legal choices distinct from the comparator. | **SUPPORTED** | Valid provider/parser provenance and legal epoch-3 divergence in all three stress seeds; frozen Phase 2 also retains legal disagreements. |
| B. Gemini selection is repeatably sensitive to aggregate waiting in controlled fixed states. | **SUPPORTED, bounded** | W08 selected R4 5/5; W19/W20/W24 selected S2 15/15 in the fixed-state repeatability study. |
| C. Gemini reduced mean/total waiting in the registered stress. | **SUPPORTED, bounded** | Both decrease in all 3/3 matched seeds. |
| D. Gemini improved service-distribution outcomes. | **PARTIALLY SUPPORTED** | Maximum and P95 improve in all seeds, but maximum approach mean and approach range worsen; the registered domain rule fails. |
| E. Gemini produced a preregistered multi-domain benefit. | **NOT SUPPORTED** | Frozen classification is efficiency-only. |
| F. Gemini is generally superior to deterministic control. | **NOT SUPPORTED** | Three seeds, one topology, one post-hoc stress condition, and conflicting local counterfactual evidence cannot generalise. |
| G. Gemini optimises fairness. | **NOT SUPPORTED** | No internal objective is observed; approach imbalance worsens. |
| H. LLM use is justified in all intersection scenarios. | **NOT SUPPORTED** | The result is conditional and provider latency/cost remain external burdens. |
| I. Conditional system-level LLM value exists under the tested stress. | **SUPPORTED, bounded** | The full-policy matched comparison meets the frozen efficiency-only rule in 3/3 strict-valid seeds. |

## Dissertation-ready wording

### Results

> In the preregistered 16-vehicle directional service-imbalance stress test,
> all three Gemini episodes were strict-valid, with 15/15 successful provider
> requests, 15/15 parser successes, and no fallback. Relative to matched
> deterministic runs, Gemini reduced total waiting by 9, 10, and 10 s, mean
> waiting by 0.5625, 0.6250, and 0.6250 s, and episode duration by 3, 5, and
> 5 s across seeds 1--3. Gemini selected the legal opposite-straight pair 18 s
> earlier in every seed, reducing its eligible-but-unserved sequence from
> three epochs to one. Maximum and P95 vehicle waiting also fell, but maximum
> approach-mean waiting and approach waiting range increased. The frozen
> classification was therefore EFFICIENCY_ONLY_BENEFIT, not a multi-domain or
> fairness benefit.

### Discussion

> The supplementary evidence separates local action effects from complete
> policy effects. In historical same-state interventions, forcing the observed
> Gemini S2 choice once produced worse primary outcomes than forcing R4 and
> then applying the same deterministic continuation. Under the later dynamic
> directional stress, however, the complete Gemini policy repeatedly served
> S2 earlier and produced modest, consistent efficiency improvements across
> three matched seeds. These findings are compatible because the experiments
> manipulate different causal objects: one legal action at a fixed state
> versus a sequence of decisions in independently evolving closed-loop
> episodes. The result supports conditional system-level value in the tested
> stress condition, not general Gemini superiority or fairness optimisation.

### Contribution

> The study provides a provenance-complete example in which strict-valid LLM
> candidate selections were behaviourally distinct, repeatably associated
> with controlled waiting information, and linked to a bounded full-policy
> efficiency benefit under a preregistered service-imbalance stress, while also
> documenting a contrary local same-state counterfactual and mixed
> service-distribution effects.

### Limitation

> The Stage 2 result is descriptive evidence from three matched seeds in one
> simulated 16-vehicle scenario and topology. It does not identify Gemini's
> internal objective, establish an exact waiting threshold, demonstrate
> fairness optimisation, provide statistical population inference, guarantee
> real-world safety, or justify LLM deployment across intersection scenarios.
> The stress study is a post-hoc supplementary validation, and the increased
> approach-level waiting imbalance must be retained alongside the efficiency
> improvements.

## Stop decision

The preregistered stopping rule is now active:

**`STOP_ALL_SUPPLEMENTARY_EXPERIMENTS`**

No result-driven scenario search or replacement run is justified.
