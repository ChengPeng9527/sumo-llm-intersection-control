# Corrected Results v3

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

This results chapter uses only:

- valid 4V evidence from `results/formal_experiment/dissertation_formal_v2/`
- corrected 8V evidence from `results/formal_experiment/dissertation_formal_v4/`

The nominal 8V `formal_v2` traces are excluded because the raw traces show only 4 observed / departed / arrived vehicles.

## 1. Experimental validity

- Valid 4V evidence: 12 runs, 4 observed / departed / arrived vehicles per run, 0 collisions.
- Corrected 8V evidence: 12 runs, 8 observed / departed / arrived vehicles per run, 0 collisions.
- Corrected dissertation evidence base: 24 valid runs total.

### Table 1. Experimental configuration

| Dataset | Controllers | Vehicle scales | Seeds | Valid runs used | Status |
|---|---:|---:|---:|---:|---|
| `formal_v2` | 4 | 4V + 8V planned | 1, 2, 3 | 12 valid 4V runs | 4V valid, 8V invalid |
| `formal_v4` | 4 | 8V | 1, 2, 3 | 12 corrected 8V runs | Fully valid 8V evidence |
| Corrected dissertation evidence | 4 | 4V + 8V | 1, 2, 3 | 24 valid runs total | 4V from `formal_v2`, 8V from `formal_v4` |

## 2. Traffic performance

The analysis remains descriptive because each controller-scale cell has `n = 3` seeds.

### Table 2. Traffic performance by controller and scale

| Controller | Scale | Completion rate | Mean waiting time | Mean speed | Throughput | Collision count | Seed-level values |
|---|---|---:|---:|---:|---:|---:|---|
| Rule-based | 4V | 100% | 82.000 ± 0.000 [82.000, 82.000] steps | 2.310 ± 0.000 [2.310, 2.310] m/s | 4.000 ± 0.000 [4.000, 4.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[82, 82, 82]`, speed `[2.310, 2.310, 2.310]` |
| Rule-based | 8V | 100% | 242.042 ± 110.586 [86.000, 329.125] steps | 1.189 ± 0.754 [0.655, 2.255] m/s | 8.000 ± 0.000 [8.000, 8.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[86, 311, 329.125]`, speed `[2.255, 0.655, 0.658]` |
| Raw LLM | 4V | 100% | 15.000 ± 0.000 [15.000, 15.000] steps | 6.803 ± 0.000 [6.803, 6.803] m/s | 4.000 ± 0.000 [4.000, 4.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.803, 6.803, 6.803]` |
| Raw LLM | 8V | 100% | 15.292 ± 2.045 [12.875, 17.875] steps | 6.599 ± 0.254 [6.265, 6.880] m/s | 8.000 ± 0.000 [8.000, 8.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[17.875, 12.875, 15.125]`, speed `[6.265, 6.880, 6.652]` |
| Hybrid | 4V | 100% | 15.000 ± 0.000 [15.000, 15.000] steps | 6.803 ± 0.000 [6.803, 6.803] m/s | 4.000 ± 0.000 [4.000, 4.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.803, 6.803, 6.803]` |
| Hybrid | 8V | 100% | 15.292 ± 2.045 [12.875, 17.875] steps | 6.599 ± 0.254 [6.265, 6.880] m/s | 8.000 ± 0.000 [8.000, 8.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[17.875, 12.875, 15.125]`, speed `[6.265, 6.880, 6.652]` |
| Hybrid + Safety | 4V | 100% | 15.000 ± 0.000 [15.000, 15.000] steps | 6.803 ± 0.000 [6.803, 6.803] m/s | 4.000 ± 0.000 [4.000, 4.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.803, 6.803, 6.803]` |
| Hybrid + Safety | 8V | 100% | 15.292 ± 2.045 [12.875, 17.875] steps | 6.599 ± 0.254 [6.265, 6.880] m/s | 8.000 ± 0.000 [8.000, 8.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[17.875, 12.875, 15.125]`, speed `[6.265, 6.880, 6.652]` |

### Interpretation

- The rule-based baseline degrades substantially from 4V to 8V.
- The LLM-assisted pipeline remains comparatively stable over the tested 4V-to-8V range.
- Completion rate saturates at 100% in every valid cell, so it does not separate controllers.
- Collision count remains 0 throughout the valid corrected evidence.

## 3. LLM/provider reliability

### Table 3. Provider/parser/fallback reliability

| Controller | Scale | Provider attempts | Provider successes | Success rate | Parser success given success | Fallback steps | Mean latency | Seed-level successes | Seed-level fallback counts |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| Raw LLM | 4V | 53.000 ± 0.000 [53.000, 53.000] | 3.333 ± 4.714 [0.000, 10.000] | 6.29% ± 8.89% [0.00%, 18.87%] | 100% | 49.667 ± 4.714 [43.000, 53.000] | 101.412 ± 29.695 ms | `[10, 0, 0]` | `[43, 53, 53]` |
| Raw LLM | 8V | 106.333 ± 0.471 [106.000, 107.000] | 0.667 ± 0.471 [0.000, 1.000] | 0.63% ± 0.44% [0.00%, 0.94%] | 100% | 105.667 ± 0.471 [105.000, 106.000] | 76.846 ± 1.552 ms | `[1, 1, 0]` | `[106, 105, 106]` |
| Hybrid | 4V | 53.000 ± 0.000 [53.000, 53.000] | 3.000 ± 4.243 [0.000, 9.000] | 5.66% ± 8.00% [0.00%, 16.98%] | 100% | 50.000 ± 4.243 [44.000, 53.000] | 111.021 ± 23.614 ms | `[9, 0, 0]` | `[44, 53, 53]` |
| Hybrid | 8V | 106.333 ± 0.471 [106.000, 107.000] | 0.333 ± 0.471 [0.000, 1.000] | 0.31% ± 0.44% [0.00%, 0.93%] | 100% | 106.000 ± 0.000 [106.000, 106.000] | 79.035 ± 4.074 ms | `[1, 0, 0]` | `[106, 106, 106]` |
| Hybrid + Safety | 4V | 53.000 ± 0.000 [53.000, 53.000] | 3.000 ± 4.243 [0.000, 9.000] | 5.66% ± 8.00% [0.00%, 16.98%] | 100% | 50.000 ± 4.243 [44.000, 53.000] | 96.152 ± 22.919 ms | `[9, 0, 0]` | `[44, 53, 53]` |
| Hybrid + Safety | 8V | 106.333 ± 0.471 [106.000, 107.000] | 0.333 ± 0.471 [0.000, 1.000] | 0.31% ± 0.44% [0.00%, 0.94%] | 100% | 106.000 ± 0.816 [105.000, 107.000] | 76.398 ± 1.312 ms | `[0, 0, 1]` | `[107, 106, 105]` |

### Interpretation

- Provider success is low in every live LLM-bearing cell.
- The 8V corrected evidence is especially weak on provider availability.
- Successful responses used `finish_reason = stop` and finite token usage (`prompt_tokens = 543`, `completion_tokens = 35–37`, `reasoning_tokens = 9–11`).
- Parser success given provider success is 100% in the corrected evidence.
- Because fallback dominates, traffic outcomes must be interpreted as pipeline-level behavior rather than pure model behavior.

## 4. Decision-flow behaviour

The trace schema preserves raw, validated, postprocessed, and final decisions separately.

### Table 4. Decision-source / postprocessor / safety behaviour

| Controller | Scale | Dominant decision pattern | Postprocessor intervention | Safety override | Practical note |
|---|---|---|---:|---:|---|
| Rule-based | 4V | deterministic interface rule | 0 | 0 | No live provider path is used. |
| Rule-based | 8V | deterministic interface rule | 0 | 0 | No live provider path is used. |
| Raw LLM | 4V | fallback-heavy live path | 0 | 0 | Live provider exists, but most attempts fail. |
| Raw LLM | 8V | fallback-heavy live path | 0 | 0 | Live provider reliability is weaker at 8V. |
| Hybrid | 4V | fallback-heavy live path | 0 | 0 | Cooperative logic is present, but not visibly exercised in the valid evidence. |
| Hybrid | 8V | fallback-heavy live path | 0 | 0 | No visible cooperative intervention in the corrected 8V evidence. |
| Hybrid + Safety | 4V | fallback-heavy live path | 0 | 0 | Safety verifier is operational but not triggered. |
| Hybrid + Safety | 8V | fallback-heavy live path | 0 | 0 | Safety verifier is operational but not triggered. |

## 5. Safety observations

- Collision count is 0 in every valid run.
- Safety override count is 0 in every valid run.
- The safety verifier exists and is logged, but it is not meaningfully exercised in the corrected formal evidence.

## 6. Corrected result boundary

- `formal_v2` valid 4V is usable evidence.
- `formal_v4` corrected 8V is usable evidence.
- `formal_v2` nominal 8V traces are historical execution-layer failure evidence and must not be used in the final dissertation results.

## 7. Final evidence provenance

- Final 4V source: `formal_v2` valid 4V runs
- Final 8V source: `formal_v4`
- Excluded from final tables: `formal_v2` nominal 8V, `formal_v3`

The identical 8V traffic results for Raw LLM, Hybrid, and Hybrid + Safety are consistent with fallback dominance, very low provider success, zero visible postprocessor intervention, and zero safety overrides. This is a pipeline-level explanation, not evidence that the three architectures are intrinsically equivalent.
