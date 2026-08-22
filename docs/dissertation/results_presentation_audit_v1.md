# Results Presentation Audit v1

## Scope

Based on:

- `D:\Sumo\sumo_train\results\formal_experiment\dissertation_formal_v2\`
- `D:\Sumo\sumo_train\docs\research\formal_experiment_v2_execution_report.md`
- `D:\Sumo\sumo_train\docs\dissertation\results_v2.md`

## Best figures to keep

### Figure 1: Mean waiting time by controller and vehicle scale

- Comparison target: `rule_based`, `raw_llm`, `hybrid`, `hybrid_safety`
- Scale split: `4V` vs `8V`
- Aggregation: mean over `3` seeds
- Unit: `steps`

**Figure-ready data**

| Controller | 4V mean waiting | 8V mean waiting |
| --- | ---: | ---: |
| Rule-based | `82.0` | `82.0` |
| Raw LLM | `15.0` | `15.0` |
| Hybrid | `15.0` | `15.0` |
| Hybrid + Safety | `15.0` | `15.0` |

### Figure 2: Mean speed by controller and vehicle scale

- Comparison target: same four controllers
- Scale split: `4V` vs `8V`
- Aggregation: mean over `3` seeds
- Unit: `m/s`

**Figure-ready data**

| Controller | 4V mean speed | 8V mean speed |
| --- | ---: | ---: |
| Rule-based | `2.31` | `2.31` |
| Raw LLM | `6.80` | `6.80` |
| Hybrid | `6.80` | `6.80` |
| Hybrid + Safety | `6.80` | `6.80` |

### Figure 3: Provider success / fallback behaviour by LLM controller and scale

- Comparison target: `raw_llm`, `hybrid`, `hybrid_safety`
- Scale split: `4V` vs `8V`
- Aggregation: `444` provider attempts per controller-scale cell
- Unit: counts and percentages

**Figure-ready data**

| Controller | Scale | Provider successes | Provider failures / fallbacks | Success rate |
| --- | --- | ---: | ---: | ---: |
| Raw LLM | 4V | `26` | `418` | `5.86%` |
| Raw LLM | 8V | `3` | `441` | `0.68%` |
| Hybrid | 4V | `22` | `422` | `4.95%` |
| Hybrid | 8V | `18` | `426` | `4.05%` |
| Hybrid + Safety | 4V | `22` | `422` | `4.95%` |
| Hybrid + Safety | 8V | `18` | `426` | `4.05%` |

### Figure 4: Provider latency by controller and scale

- Comparison target: live LLM-bearing controllers
- Scale split: `4V` vs `8V`
- Aggregation: mean latency over successful provider calls within each cell
- Unit: `ms`

**Figure-ready data**

| Controller | 4V mean latency | 8V mean latency |
| --- | ---: | ---: |
| Raw LLM | `93.64` | `75.93` |
| Hybrid | `97.98` | `87.53` |
| Hybrid + Safety | `86.10` | `83.34` |

## Best tables to keep

### Table 1: Formal experiment configuration

Keep, but in the supervisor draft it is best presented as a short reproducibility table rather than a project-log table.

Recommended content:

- canonical prompt
- provider
- base URL
- model
- request config
- controllers
- vehicle scales
- seeds
- planned runs
- scenario density

### Table 2: Traffic performance by controller and scale

Keep exactly as a main results table.

Why it matters:

- it carries the main RQ1 / RQ4 traffic evidence
- it shows completion, waiting time, speed, collisions, throughput
- it is the clearest comparison table for the dissertation marker

### Table 3: LLM reliability by controller and scale

Keep exactly as a main results table.

Why it matters:

- it shows provider attempts and success rates
- it exposes fallback dependence
- it explains why the dissertation must not be framed as pure LLM performance

### Table 4: Decision-flow distribution

Keep as a compact summary table or appendix table.

Recommended rows:

- `DETERMINISTIC_INTERFACE_RULE`
- `FALLBACK`
- `LLM_RAW`
- `COOPERATIVE_POSTPROCESSOR`
- `SAFETY_VERIFIER`

## Presentation recommendations

1. Use a single bar chart or grouped bar chart for Figures 1 and 2.
2. Use stacked or paired bars for Figure 3 so success and fallback are visually linked.
3. Use a grouped bar chart for Figure 4.
4. Put the exact seed-level numeric values in the table captions or appendix notes, not in the figure body.
5. Keep captions explicit about aggregation basis:
   - `4V / 8V`
   - `3` seeds
   - units (`steps`, `m/s`, `ms`, counts)

## What not to add

- Do not add extra figures just to fill space.
- Do not split one evidence family into multiple redundant charts.
- Do not create a figure for collision count, because the value is already saturated at zero and is better discussed in text.

## Bottom line

The current dataset is sufficient for four dissertation-grade figures and four core tables. No extra experiment is needed to support the present results presentation.
