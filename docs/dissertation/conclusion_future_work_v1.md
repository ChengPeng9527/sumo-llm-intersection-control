# Conclusion and Future Work v1

## 1. What was done?

This dissertation designed, implemented, and evaluated a structured LLM-assisted decision pipeline for unsignalised intersection control in SUMO. The system separates the decision stack into raw LLM proposal, validation, cooperative post-processing, deterministic safety verification, and trace logging. The evaluation used a frozen formal experiment matrix with four controllers, two vehicle scales, and three seeds.

The resulting formal v2 dataset is complete and collision-free:

- `24/24` runs completed
- `24/24` runs valid
- completion rate `100%` in every formal v2 run
- collision count `0`

## 2. What are the main findings?

The strongest traffic-side finding is that the LLM-assisted architecture is associated with lower waiting time and higher mean speed than the rule-based baseline in the tested low-density scenarios.

- rule-based waiting time: about `82` steps
- LLM-assisted waiting time: about `15` steps
- rule-based mean speed: about `2.31 m/s`
- LLM-assisted mean speed: about `6.80 m/s`

However, the live-provider traces show that this traffic advantage should not be presented as pure LLM performance. The formal v2 evidence shows heavy fallback dependence:

- provider attempts: `2664`
- provider successes: `109`
- provider failures: `2555`
- parser successes: `109`
- fallback-heavy behavior dominates the live LLM-bearing runs

Therefore, the most defensible conclusion is that the project demonstrates a functioning LLM-assisted decision pipeline, not a clean proof of pure model superiority.

## 3. Answers to the research questions

### RQ1

**Question:** Can an LLM-assisted architecture improve traffic efficiency relative to rule-based control?

**Answer:** Under the evaluated low-density scenarios, the LLM-assisted architecture exhibited lower waiting time and higher speed than the rule-based baseline. This supports a cautious claim that the architecture can improve traffic efficiency in this specific evaluation setting.

### RQ2

**Question:** Does cooperative post-processing change the behavior of raw LLM decisions in a meaningful way?

**Answer:** Cooperative post-processing exists in the pipeline, but formal v2 shows only a rare visible effect. There was only one recorded postprocessor intervention in the full formal v2 dataset. The effect is therefore present but small in the available evidence.

### RQ3

**Question:** What effect does deterministic safety verification have, and is there a safety-efficiency trade-off?

**Answer:** Safety verification was present and traceable, but it did not trigger any overrides in formal v2. The dataset therefore supports a statement that the safety layer is verified and available, but not that it produced a measurable safety-efficiency trade-off in this study.

### RQ4

**Question:** How does the system behave when scale increases from 4 vehicles to 8 vehicles?

**Answer:** The traffic metrics remain stable across 4V and 8V in the low-density setting, but provider reliability becomes more fragile, especially for raw LLM at 8V. This supports only a conservative scalability statement.

## 4. What is the most important limitation?

The most important limitation is provider reliability.

The formal v2 results are not invalid, but they are strongly mediated by live-provider fallback behavior. This affects how the results should be interpreted:

- the traffic metrics are pipeline outcomes,
- not pure direct LLM decision quality,
- and not a proof that the LLM itself is consistently available or robust.

Other limitations matter too, but none is more important than the provider reliability threat for this dissertation.

## 5. Overall research contribution

The dissertation's main contribution is not a claim of universal superiority. Its contribution is a reproducible, traceable comparison of controller architectures for unsignalised intersection control, together with an explicit analysis of how provider availability and fallback behavior shape the final system behavior.

That is a useful research contribution because it makes clear where the LLM helps, where it fails, and how much of the final behavior is attributable to deterministic pipeline stages.

## 6. Future work

The future work should follow directly from the real limitations of the current study.

### 6.1 Higher-density traffic and larger-scale evaluation

The current formal v2 matrix covers only 4V and 8V. A natural next step is to evaluate higher-density traffic and larger vehicle counts, including 16V or beyond, to test whether the pipeline remains operational under more demanding conditions.

### 6.2 More seeds

The formal v2 experiment uses three seeds. More seeds would improve the robustness of the descriptive comparison and help distinguish stable effects from run-level variation.

### 6.3 Additional intersection layouts

The current study uses one unsignalised intersection topology. Future work could evaluate additional intersection geometries or route structures to test whether the pipeline generalises beyond the current configuration.

### 6.4 Local or self-hosted LLM comparison

Because live provider reliability is a major validity threat, a useful follow-up would be to compare the current hosted provider path against a local or self-hosted model under the same prompt and decision contract. That would help separate model quality from provider availability.

### 6.5 Controlled fallback ablation

Future work could examine how much of the observed traffic behavior comes from fallback handling. A controlled fallback ablation would help quantify the contribution of deterministic fallback to the final system behavior.

### 6.6 Safety-triggered scenarios

The current dataset contains no safety overrides. Future experiments could include scenario designs that are more likely to trigger the safety verifier, so the dissertation can measure whether safety changes the final decision behavior in practice.

### 6.7 Real-time or hardware-in-the-loop validation

The present work is simulation-based. A later stage could move toward real-time or hardware-in-the-loop validation if the method is to be considered for more realistic deployment contexts.

## 7. Final conclusion

The dissertation shows that a frozen, traceable LLM-assisted decision pipeline can be evaluated systematically in SUMO and can exhibit lower waiting time than a rule-based baseline in the tested scenarios. At the same time, the formal v2 evidence makes clear that live-provider reliability is a first-order validity issue, so the final claim must stay at the level of pipeline behavior rather than pure LLM intelligence.
