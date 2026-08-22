# Results v1

## 1. Summary Statement

The formal v2 experiment completed all `24` planned runs and produced a collision-free dataset. The results are therefore suitable for dissertation reporting, but they must be interpreted as pipeline outcomes rather than pure LLM behavior because fallback and deterministic intervention are substantial.

## 2. Overall Formal v2 Outcome

- planned runs: `24`
- completed runs: `24`
- valid runs: `24`
- collisions: `0`
- truncations: `0`
- provider attempts: `2664`
- provider successes: `109`
- provider failures: `2555`
- parser successes: `109`
- fallback count: `2555`
- finish reason: `stop` on all successful provider responses

## 3. Controller Comparison

| Controller | Scale | Completion | Collisions | Provider attempts | Provider successes | Parser successes | Fallbacks | Mean waiting time | Mean speed | Mean latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rule-based | 4 | 100% | 0 | 0 | 0 | 0 | 0 | 82 | 2.31 m/s | N/A |
| Rule-based | 8 | 100% | 0 | 0 | 0 | 0 | 0 | 82 | 2.31 m/s | N/A |
| Raw LLM | 4 | 100% | 0 | 444 | 26 | 26 | 418 | 15 | 6.80 m/s | 456.37 ms |
| Raw LLM | 8 | 100% | 0 | 444 | 3 | 3 | 441 | 15 | 6.80 m/s | 766.23 ms |
| Hybrid | 4 | 100% | 0 | 444 | 22 | 22 | 422 | 15 | 6.80 m/s | 451.61 ms |
| Hybrid | 8 | 100% | 0 | 444 | 18 | 18 | 426 | 15 | 6.80 m/s | 447.77 ms |
| Hybrid + Safety | 4 | 100% | 0 | 444 | 22 | 22 | 422 | 15 | 6.80 m/s | 356.22 ms |
| Hybrid + Safety | 8 | 100% | 0 | 444 | 18 | 18 | 426 | 15 | 6.80 m/s | 342.59 ms |

## 4. RQ1: Rule-based vs LLM-assisted control

The rule-based baseline and the LLM-assisted modes all completed the formal v2 runs without collisions. However, the rule-based controller was much more conservative in this low-density setup:

- rule-based mean waiting time: `82` steps
- LLM-assisted mean waiting time: `15` steps
- rule-based mean speed: `2.31 m/s`
- LLM-assisted mean speed: `6.80 m/s`

Interpretation:

- the LLM-assisted pipeline appears more flow-friendly in this dataset
- completion rate alone is not enough to distinguish controllers because it is saturated at `100%`

## 5. RQ2: Raw LLM vs Hybrid

The hybrid pipeline retained collision-free completion while changing the reliability profile of the live provider path.

Key evidence:

- Raw LLM 4V: `26/444` provider successes, `418` fallbacks
- Raw LLM 8V: `3/444` provider successes, `441` fallbacks
- Hybrid 4V: `22/444` provider successes, `422` fallbacks
- Hybrid 8V: `18/444` provider successes, `426` fallbacks

Interpretation:

- raw LLM reliability degrades sharply at 8 vehicles
- hybrid is more reliable than raw LLM at 8 vehicles, but the improvement is modest relative to the amount of fallback still observed
- this is evidence for pipeline robustness, not evidence that the raw model itself is incapable of producing correct decisions

## 6. RQ3: Hybrid vs Hybrid + Safety

Formal v2 does not show a measurable safety-efficiency trade-off because safety overrides are zero across the dataset.

Key evidence:

- safety override count: `0`
- collision count: `0`
- hybrid and hybrid+safety have identical traffic metrics in the aggregate report
- postprocessor interventions: `1` total, only in `hybrid_8`

Interpretation:

- the safety verifier did not need to intervene in the formal v2 runs
- the dissertation should therefore describe safety as verified but not strongly exercised in this dataset
- the correct claim is an absence-of-evidence statement, not a proof that safety has no effect

## 7. RQ4: 4V to 8V scalability

The raw LLM path shows the clearest scale sensitivity:

- 4V provider success: `26`
- 8V provider success: `3`

The hybrid and hybrid+safety modes also weaken at 8V, but not nearly as sharply as raw LLM.

Interpretation:

- larger vehicle counts increase reliability pressure on the live provider path
- the current formal v2 dataset supports a cautious scalability discussion, but not a broad generalization beyond the tested 4V and 8V conditions

## 8. Decision-flow evidence

Across the formal v2 step records, the final decision pipeline was dominated by deterministic control and fallback handling rather than raw model output.

Observed counts:

- deterministic interface rule: `3522`
- fallback: `1722`
- raw LLM direct source: `23`
- cooperative postprocessor source: `1`
- safety verifier source: `0`

Interpretation:

- the dissertation should not describe the system as pure end-to-end LLM control
- instead, the results support a staged decision architecture in which the LLM is one component among several

## 9. Safe results wording

A defensible results sentence is:

> The formal v2 dataset shows a completed, collision-free 24-run matrix with clear traceability across raw, validated, postprocessed, and final decisions, but the live LLM-bearing controllers are heavily mediated by fallback behavior, so the system's performance must be interpreted at the pipeline level rather than as pure model performance.
