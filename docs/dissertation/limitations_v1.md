# Limitations v1

This chapter should only contain limitations that are directly supported by the current evidence.

## 1. Only 4V and 8V formal scenarios

- The formal v2 matrix evaluates only `4` and `8` vehicles.
- There is no formal v2 evidence for `16V`.
- Any scalability claim beyond `8V` would be unsupported.

## 2. Only three seeds

- The formal v2 dataset uses seeds `1`, `2`, and `3`.
- This is sufficient for descriptive reporting, but not for strong generalisation.

## 3. Simulation-only evaluation

- All formal v2 evidence comes from SUMO simulation.
- There is no physical robot or real traffic validation.

## 4. Single intersection topology

- The experiment uses one unsignalized intersection setting.
- Results cannot be generalized to multi-intersection networks without new evidence.

## 5. External LLM provider dependency

- The live LLM path depends on Groq.
- Provider availability and throttling are part of the system?s observed behavior.

## 6. High provider failure / fallback dependence

- Provider successes: `109`
- Provider failures: `2555`
- Fallback decisions dominate the live-provider traces.

This means the dissertation must not describe the result as pure LLM performance.

## 7. No observed safety overrides

- Safety overrides are `0` across the formal v2 dataset.
- This prevents a strong safety-efficiency trade-off claim.

## 8. Limited postprocessor intervention

- Cooperative post-processing is observed only once across the full formal v2 sweep.
- The cooperative mechanism is present, but its effect size is sparse in this dataset.

## 9. Completion-rate saturation

- Completion rate is `100%` in every formal v2 run.
- Because of that saturation, completion rate is not useful for separating controllers.
- Waiting time, speed, and provider reliability are more informative.

## 10. No evidence for dense-traffic generalisation

- The formal v2 runs are low-density.
- The evidence does not support claims about dense traffic or stressful congestion.

## 11. Sequential reliability confound

- The provider reliability pattern is uneven across seeds and controller order.
- This is a validity threat for interpreting controller differences as if they were purely algorithmic.

## 12. What should not be claimed

The dissertation should not claim:

- that LLM-assisted control is universally better,
- that safety verification improved metrics in formal v2,
- that the system scales to 16V,
- that the raw model alone explains the observed traffic advantage,
- that the study generalizes to real-world traffic without further validation.
