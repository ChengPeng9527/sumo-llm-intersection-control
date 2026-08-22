# Results v2

## 1. Formal Results Statistical Audit

This section re-derives the formal v2 results from the raw `step_records.csv` and `run_metadata.json` artifacts under:

`D:\Sumo\sumo_train\results\formal_experiment\dissertation_formal_v2\`

The experiment is descriptive rather than inferential. The sample size is `n = 3` per controller-scale cell, so the analysis should remain at the level of means, standard deviations, and seed-level values.

### 1.1 Formal v2 coverage

- planned runs: `24`
- completed runs: `24`
- valid runs: `24`
- missing runs: `0`
- duplicate runs: `0`
- technical reruns: `0`
- collisions: `0`
- truncations: `0`

### 1.2 Failure classification

All `2555` provider failures in the formal v2 LLM-bearing traces are classified as:

- `RateLimitError`: `2555`

Saved artifacts do not preserve HTTP status for these failed calls, so the evidence supports a provider-side throttling / rate-limit classification at the client error layer, not a parser or prompt-contract failure.

### 1.3 Decision-flow summary

Across the full formal v2 step records, the final decision source counts are:

- `DETERMINISTIC_INTERFACE_RULE`: `3522`
- `FALLBACK`: `1722`
- `LLM_RAW`: `23`
- `COOPERATIVE_POSTPROCESSOR`: `1`
- `SAFETY_VERIFIER`: `0`

This means the dissertation should treat the evaluated system as a staged pipeline, not as pure end-to-end LLM control.

## 2. Table 1: Formal Experiment Configuration

| Item | Value |
| --- | --- |
| Repository | `D:\Sumo\sumo_train` |
| Branch | `phase-18-decision-pipeline-separation` |
| Freeze commit | `7b363fa8add58ac83775eb26dd6ff0b68bea022e` |
| Freeze tag | `v0.9.1-formal-experiment-freeze` |
| Canonical prompt | `P1_BASELINE` |
| Prompt hash | `EA435588BE1CAFC099D02685060CF00223852D8834CDFCF4DAFE66233C474ECD` |
| Provider | Groq |
| Base URL | `https://api.groq.com/openai/v1` |
| Model | `openai/gpt-oss-20b` |
| Request config | `max_completion_tokens=256`, `reasoning_effort=low`, `timeout=30.0`, `max_retries=0` |
| Controllers | `rule_based`, `raw_llm`, `hybrid`, `hybrid_safety` |
| Vehicle scales | `4`, `8` |
| Seeds | `1`, `2`, `3` |
| Planned runs | `24` |
| Scenario density | `low` |

## 3. Table 2: Traffic Performance by Controller and Scale

Traffic outcomes are stable across seeds, so the seed values are shown explicitly.

| Controller | Scale | Completion rate | Mean waiting time | Mean speed | Collision count | Throughput | Seed-level values |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Rule-based | 4V | `100%` | `82.0 ? 0.0` steps | `2.31 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[82, 82, 82]`, speed `[2.31, 2.31, 2.31]`, collisions `[0, 0, 0]` |
| Rule-based | 8V | `100%` | `82.0 ? 0.0` steps | `2.31 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[82, 82, 82]`, speed `[2.31, 2.31, 2.31]`, collisions `[0, 0, 0]` |
| Raw LLM | 4V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |
| Raw LLM | 8V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |
| Hybrid | 4V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |
| Hybrid | 8V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |
| Hybrid + Safety | 4V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |
| Hybrid + Safety | 8V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |

### Traffic observations

- Completion rate is saturated at `100%` in every cell, so it is not useful for separating controllers in formal v2.
- Waiting time and mean speed are the meaningful traffic discriminators in this dataset.
- Rule-based control is much more conservative than the LLM-assisted controllers under the tested low-density scenarios.

## 4. Table 3: LLM Reliability by Controller and Scale

| Controller | Scale | Provider attempts | Provider successes | Success rate | Parser success given provider success | Fallback rate | Mean latency | Seed-level provider successes | Seed-level fallback counts | Seed-level latency means |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| Raw LLM | 4V | `444` | `26` | `5.86%` | `100%` | `94.14%` | `93.64 ? 36.42` ms | `[26, 0, 0]` | `[122, 148, 148]` | `[135.68, 73.45, 71.80]` |
| Raw LLM | 8V | `444` | `3` | `0.68%` | `100%` | `99.32%` | `75.93 ? 3.50` ms | `[2, 1, 0]` | `[146, 147, 148]` | `[79.59, 75.60, 72.60]` |
| Hybrid | 4V | `444` | `22` | `4.95%` | `100%` | `95.05%` | `97.98 ? 25.58` ms | `[22, 0, 0]` | `[126, 148, 148]` | `[123.96, 97.16, 72.81]` |
| Hybrid | 8V | `444` | `18` | `4.05%` | `100%` | `95.95%` | `87.53 ? 24.99` ms | `[0, 18, 0]` | `[148, 130, 148]` | `[70.84, 116.26, 75.50]` |
| Hybrid + Safety | 4V | `444` | `22` | `4.95%` | `100%` | `95.05%` | `86.10 ? 23.77` ms | `[22, 0, 0]` | `[126, 148, 148]` | `[113.50, 73.67, 71.12]` |
| Hybrid + Safety | 8V | `444` | `18` | `4.05%` | `100%` | `95.95%` | `83.34 ? 15.05` ms | `[0, 18, 0]` | `[148, 130, 148]` | `[75.97, 100.65, 73.39]` |

### Reliability observations

- All successful provider responses were parsed successfully.
- Every failure was a provider-call failure, not a parser failure.
- Raw LLM reliability drops sharply at 8V.
- Hybrid and hybrid+safety are slightly more stable than raw LLM at 8V, but the traces remain fallback-heavy.
- Latency is not the main issue; availability/reliability is.

## 5. Seed-Level Summary

The seed-level pattern is important because it shows that the provider reliability signal is not uniform across repetitions.

### Raw LLM

- 4V seed 1: `26` provider successes, `122` fallbacks
- 4V seed 2: `0` provider successes, `148` fallbacks
- 4V seed 3: `0` provider successes, `148` fallbacks
- 8V seed 1: `2` provider successes, `146` fallbacks
- 8V seed 2: `1` provider success, `147` fallbacks
- 8V seed 3: `0` provider successes, `148` fallbacks

### Hybrid

- 4V seed 1: `22` provider successes, `126` fallbacks
- 4V seed 2: `0` provider successes, `148` fallbacks
- 4V seed 3: `0` provider successes, `148` fallbacks
- 8V seed 1: `0` provider successes, `148` fallbacks
- 8V seed 2: `18` provider successes, `130` fallbacks
- 8V seed 3: `0` provider successes, `148` fallbacks

### Hybrid + Safety

- 4V seed 1: `22` provider successes, `126` fallbacks
- 4V seed 2: `0` provider successes, `148` fallbacks
- 4V seed 3: `0` provider successes, `148` fallbacks
- 8V seed 1: `0` provider successes, `148` fallbacks
- 8V seed 2: `18` provider successes, `130` fallbacks
- 8V seed 3: `0` provider successes, `148` fallbacks

### Interpretation of seed-level variation

- The reliability problem is not a uniform failure; it is uneven across runs.
- Because the live provider success window is narrow, the dissertation should avoid treating these controller means as stable universal model properties.
- The traffic metrics are stable across seeds, but the provider path is not.

## 6. RQ-focused Results Summary

### RQ1: Rule-based vs LLM-assisted architecture

Observed result:

- LLM-assisted controllers have lower waiting time (`15` steps) and higher mean speed (`6.80 m/s`) than rule-based control (`82` steps, `2.31 m/s`) in the formal v2 scenarios.

Interpretation:

- the evaluated LLM-assisted architecture is more flow-friendly under these low-density scenarios.

Limitation:

- provider availability is poor, so this is a pipeline-level result rather than a pure LLM-only result.

### RQ2: Raw vs Hybrid

Observed result:

- hybrid slightly improves provider reliability relative to raw LLM at 8V (`18/444` vs `3/444` provider successes), but traffic metrics are unchanged in the aggregate.

Interpretation:

- cooperative post-processing exists in the pipeline, but formal v2 shows only a small visible effect on traffic outcomes.

Limitation:

- provider failures dominate the trace, so the postprocessor has limited room to influence the final behavior.

### RQ3: Hybrid vs Hybrid + Safety

Observed result:

- safety overrides are `0` in all formal v2 runs.

Interpretation:

- the safety layer is present and verified, but it is not strongly exercised by this dataset.

Limitation:

- the data cannot support a measurable safety-efficiency trade-off claim.

### RQ4: 4V vs 8V scalability

Observed result:

- traffic metrics remain stable across 4V and 8V in this low-density setup, but raw LLM reliability collapses more sharply at 8V than at 4V.

Interpretation:

- the system is operationally stable on the traffic side for both tested scales, but provider reliability becomes a serious threat at 8V.

Limitation:

- formal v2 does not include 16V, so the dissertation should not claim broader scalability.

## 7. Proposed Tables and Figures

The dissertation should use a small number of high-value tables and figures.

### Table 1

**Formal experiment configuration**

- repository, branch, freeze commit/tag, prompt, model, request config, controllers, scales, seeds, planned runs

### Table 2

**Traffic performance by controller and vehicle scale**

- completion rate
- mean waiting time
- mean speed
- collision count
- throughput
- seed values

### Table 3

**LLM reliability metrics by controller and vehicle scale**

- provider attempts
- provider successes
- success rate
- parser success given provider success
- fallback rate
- latency
- seed values

### Table 4

**Decision-flow source distribution**

- deterministic interface rule
- fallback
- raw LLM
- cooperative postprocessor
- safety verifier

### Figure 1

**Mean waiting time by controller, separated by 4V / 8V**

- y-axis: waiting time in steps
- x-axis: controller
- grouped or faceted by scale
- caption should note `n = 3` per cell and that the plot is descriptive

### Figure 2

**Mean speed by controller, separated by 4V / 8V**

- y-axis: mean speed in m/s
- x-axis: controller
- grouped or faceted by scale
- caption should note the same low-density scenario and `n = 3`

### Figure 3

**Provider success and fallback rate by LLM controller and scale**

- y-axis: percentage of provider attempts
- x-axis: controller
- grouped by scale
- show success and fallback together

### Figure 4

**Latency by LLM controller and scale**

- y-axis: mean provider latency in ms
- x-axis: controller
- grouped by scale

## 8. Caption-ready wording

Short caption templates:

- **Table 2**: "Descriptive traffic performance summary for the formal v2 dataset. The table reports mean values across three seeds for each controller-scale cell."
- **Table 3**: "Live provider reliability summary for the formal v2 dataset. The table reports provider attempts, successful responses, parser success, fallback rate, and latency."
- **Figure 1**: "Mean waiting time by controller and vehicle scale in the formal v2 experiment. Error bars represent one standard deviation across three seeds."
- **Figure 2**: "Mean speed by controller and vehicle scale in the formal v2 experiment. Error bars represent one standard deviation across three seeds."
- **Figure 3**: "Provider success and fallback rate for live LLM-bearing controllers in the formal v2 experiment."
- **Figure 4**: "Mean provider latency for live LLM-bearing controllers in the formal v2 experiment."

## 9. Safe Results Wording

A defensible dissertation sentence is:

> The formal v2 dataset shows collision-free completion across all 24 runs, with lower waiting time and higher speed for the LLM-assisted architecture than for the rule-based baseline, but the live-provider traces are heavily fallback-driven and must therefore be interpreted at the pipeline level rather than as pure model performance.
