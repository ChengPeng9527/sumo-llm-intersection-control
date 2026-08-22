# Dissertation Chapter 6/7 Attribution Final Draft

## 1. Evidence Summary

This draft is designed to reconcile the retained formal experiment with the later attribution diagnostics without collapsing the two evidence sets into one.

### Retained formal experiment

The retained formal evidence consists of the 24 formal runs preserved for the dissertation: the valid 4V `formal_v2` runs and the corrected 8V `formal_v4` runs. These results support a pipeline-level traffic-performance comparison between the LLM-assisted architecture and the selected rule-based baseline. In the corrected formal evidence, the LLM-assisted modes achieve lower waiting time and higher mean speed than the rule-based baseline, while completion remains `100%` and collisions remain `0`.

The same formal evidence also shows that live-provider reliability is weak, fallback-dominated, and uneven across seeds and controller variants. That means the formal result is necessarily a pipeline-level result rather than a clean isolation of model-level contribution.

### Post-hoc attribution and diagnostic evidence

The later diagnostic evidence provides a more precise attribution test for the 4V condition:

- Genuine Gemini Raw LLM 4V seed1 achieved `53/53` provider success, `53/53` parser success, complete provenance, `0` fallback usage, `100%` completion, `0` collision, operational waiting `11.0` steps, and mean speed of approximately `7.5839 m/s`.
- Fallback-only 4V seed1 produced the same traffic outcome: operational waiting `11.0` steps and mean speed of approximately `7.5839 m/s`.
- Rule-based 4V seed1 was materially worse: operational waiting `82.0` steps and mean speed of approximately `2.3098 m/s`.
- Decision-level alignment between genuine Gemini and fallback-only was exact on all comparable rows: `132/132` raw agreement and `132/132` final agreement.
- The high-discrimination probe identified `11` mixed route-group states, `39` comparable vehicle rows, and `39/39` agreement at both raw and final decision level, with `100%` provider and parser success.

### Interpretation boundary

The formal experiment therefore still supports a cautious claim that the LLM-assisted pipeline outperformed the rule-based baseline in the tested scenarios. However, the later attribution evidence does not support attributing that improvement to independent Gemini reasoning. Under the evaluated states, the deterministic fallback policy accounts for the observed traffic advantage, while reliable Gemini decisions were behaviourally indistinguishable from fallback.

The correct dissertation boundary is therefore:

- valid: pipeline-level traffic advantage relative to the rule-based baseline;
- valid but qualified: provider reliability as a major limitation;
- newly required: semantic overlap between prompt and fallback as an identifiability limitation;
- not supported: a claim that the traffic improvement can be attributed cleanly to the LLM alone.

## 2. Recommended Chapter 6 Final Text

### 6.1 RQ1: Rule-based vs LLM-assisted architecture

The corrected formal evidence supports the claim that the LLM-assisted pipeline achieves lower waiting time and higher mean speed than the selected rule-based baseline in the tested SUMO scenarios. In the retained formal matrix, the pipeline-level traffic performance is better than the stricter rule-based controller, and this is the most defensible reading of the formal results.

The attribution evidence, however, requires that this result be framed carefully. The formal runs were heavily fallback-dominated, so the observed traffic advantage cannot be attributed directly to independent live-provider reasoning. The correct interpretation is that the LLM-assisted architecture performs better as an operational pipeline under the tested conditions, but the formal evidence alone does not isolate the LLM component as the sole causal source of that improvement.

The subsequent genuine Gemini 4V seed1 diagnostic pilot clarifies this point. In that pilot, all `53` logical provider requests succeeded, all `53` responses parsed successfully, and no fallback was used. This removes the provider-failure confound for that diagnostic condition. Even so, the traffic outcome did not improve beyond fallback-only: Gemini and fallback-only both achieved operational waiting of `11.0` steps, mean speed of approximately `7.5839 m/s`, full completion, and zero collisions.

Taken together, the formal and diagnostic evidence support a pipeline-level claim only. The dissertation can state that the architecture is effective in the tested scenarios, but it should not state that the LLM itself independently caused the traffic-performance improvement.

### 6.2 RQ2: Raw LLM versus hybrid control

The corrected evidence does not show a clear traffic-performance advantage for the hybrid architecture over the raw LLM architecture. The hybrid and raw LLM modes remain effectively similar on the traffic metrics, and the corrected formal evidence does not show a material postprocessor effect.

The most plausible reading is that the cooperative layer is implemented and traceable, but rarely exercises enough influence to produce a measurable traffic-level gain in the valid formal evidence. The absence of a clear hybrid advantage should therefore be reported as an empirical result, not as a design failure. It indicates limited differentiation between the raw LLM and the cooperative stage in the evaluated conditions.

### 6.3 RQ3: Safety layer behaviour

The corrected valid evidence shows that the safety layer is present, traceable, and operational, but it is not meaningfully exercised in the final evidence set. Collisions remain at `0` and safety overrides remain at `0`, which means the verifier did not become an active differentiating factor in the tested scenarios.

The dissertation should therefore avoid claiming that safety improved the measured traffic metrics. The defensible claim is narrower: deterministic safety verification was implemented, logged, and available, but the tested scenarios did not produce enough unsafe or conflict-inducing states to demonstrate a visible safety-efficiency trade-off.

### 6.4 RQ4: 4V to 8V scalability

The corrected evidence supports only a bounded scalability claim. The traffic-side behaviour remains comparatively stable from 4V to 8V in the corrected evidence, while provider reliability becomes weaker and more fallback-heavy at the larger scale.

This is not a basis for a general scalability claim. It supports only the statement that, under the frozen low-density scenario used here, the pipeline remains operational at both scales and the traffic metrics remain comparatively stable. The attribution evidence also shows that stable traffic metrics do not necessarily imply an independent LLM contribution.

### 6.5 Attribution of LLM-Specific Effects

The formal experiment supports a pipeline-level claim rather than a pure model-level claim. In the retained formal evidence, the LLM-assisted controllers outperform the rule-based baseline on the key traffic metrics, but the provider layer in those runs is highly unreliable and frequently replaced by deterministic fallback. As a result, the formal matrix is best interpreted as evidence that the architecture can improve traffic efficiency under the tested scenarios, not as a clean demonstration that the LLM itself is the sole causal source of the improvement.

The genuine Gemini 4V seed1 diagnostic pilot removes that reliability confound for one controlled condition. In that pilot, all `53` logical provider requests succeeded, all `53` responses parsed successfully, and no fallback was used. This establishes that the live Gemini path can execute reliably under the evaluated configuration. It also means that, in this diagnostic condition, the traffic outcome cannot be dismissed as an artefact of provider failure.

However, the traffic comparison does not reveal an incremental LLM-specific benefit. The rule-based controller is substantially more conservative than the fallback-only controller, but the fallback-only and genuine Gemini runs are identical on the observed traffic measures: both achieve operational waiting of `11.0` steps, mean speed of approximately `7.5839 m/s`, full completion, and zero collisions. In other words, the large improvement relative to the rule-based baseline is recovered by the deterministic fallback policy itself, whereas genuine Gemini participation does not add further traffic improvement in this seed.

This conclusion is reinforced at the decision level. On all `132` comparable rows, the Gemini raw decisions match the fallback-only raw decisions exactly, and the same perfect agreement persists at the final decision level. Because the similarity is already present at the raw layer, it cannot be explained as a downstream deterministic correction of divergent LLM proposals. The similarity is visible before any final safety or validation stage has an opportunity to alter the output.

A targeted analysis of the most discriminative observed states reaches the same conclusion. Across `11` mixed route-group states and `39` comparable vehicle-row decisions, Gemini again matches fallback exactly at both raw and final decision level. That strengthens the attribution result, but it still does not prove global policy equivalence. It does, however, show that the current prompt and state representation are sufficiently aligned with the fallback semantics that the evaluated states do not elicit a distinguishable LLM-specific policy.

The most defensible interpretation is therefore that fallback-dominant attribution remains the correct reading of the evidence. The current Gemini configuration reproduces the deterministic fallback behaviour under the evaluated states, and no incremental LLM-specific traffic benefit has yet been demonstrated.

## 3. Recommended Chapter 7 Final Text

### 7.1 Experimental scale and statistical scope

The dissertation remains limited to a small number of controller-scale cells and seeds. The corrected formal evidence covers only 4V and 8V, with three seeds per controller-scale cell. That is sufficient for a descriptive comparison, but not for strong inferential claims or generalisation beyond the tested design.

### 7.2 Simulation and external validity

The evidence is simulation-based and restricted to a single low-density, unsignalised intersection. This makes the comparison controlled and reproducible, but it also narrows the scope of inference. The dissertation supports simulation-level claims about the tested SUMO scenario, not claims about dense traffic, multiple intersections, heterogeneous layouts, or real-road deployment.

### 7.3 Historical provider reliability

Historical provider reliability remains a major validity threat for the formal evidence. In the corrected formal matrix, provider success is low, fallback-heavy execution is the norm, and successful provider calls are sparse and seed-sensitive. That means the traffic results in the formal dataset must be interpreted as pipeline outcomes under constrained provider availability rather than as pure model performance.

### 7.4 Experimental identifiability of the LLM contribution

Traceability allows the dissertation to observe which component produced a given decision, but traceability alone does not make causal contribution identifiable. In this project, the canonical prompt and the deterministic fallback policy encode substantially overlapping decision semantics. Both reason over route compatibility and conflict structure, vehicle priority or approach state, and the constrained `PROCEED` / `WAIT` / `FREE` decision space.

That overlap creates an identifiability problem. Even when Gemini is reliable and all requests succeed, the system can still produce behaviour that is indistinguishable from the deterministic heuristic. The diagnostic 4V seed1 pilot makes this explicit: Gemini was reliable, provenance was complete, yet the observed traffic behaviour matched fallback-only exactly; the decision-level audit and the high-discrimination probe both found complete agreement.

This does not show that Gemini and fallback are globally equivalent. It does not show that Gemini cannot contribute in other traffic states. What it does show is narrower and more important for this dissertation: the current experiment does not isolate an independent LLM contribution. The evidence is strong enough to support pipeline-level attribution, but not strong enough to support a claim of distinct LLM reasoning value in the evaluated states.

### 7.5 Cooperative and safety mechanisms

The cooperative postprocessor and safety verifier are part of the architecture and are clearly logged, but the corrected formal evidence shows that they are not strongly exercised. The cooperative layer does not produce a visible traffic advantage, and the safety verifier records zero overrides in the final evidence set. Their presence is therefore methodologically important, but their causal effect is limited in the evaluated runs.

### 7.6 Metrics and evidence limitations

Completion rate saturates at `100%` across the valid runs, so it is not a useful differentiator by itself. The more informative metrics are waiting time, mean speed, provider success, parser success, fallback rate, and decision-flow agreement. Even those measures must be interpreted with care, because identical traffic metrics can arise from different causal pathways.

### 7.7 Overall boundary

The dissertation is still defensible, but its claim boundary must remain modest. It supports a traceable pipeline-level comparison of controller architectures and shows that the architecture performs better than the selected rule-based baseline in the tested scenarios. It does not establish an independent LLM-specific traffic benefit, and it does not justify a universal claim about LLM-based traffic control.

## 4. Recommended Chapter 8 Exact Replacement Paragraphs

### 8.1 Replace the existing paragraph under `What was observed?`

Replace the current RQ1–RQ4 observation summary with:

> The corrected evidence supports four main observations. First, the LLM-assisted pipeline shows lower waiting time and higher mean speed than the selected rule-based baseline in the tested scenarios, but the later attribution evidence indicates that this improvement is better understood at the pipeline level than as an isolated LLM effect. Second, rule-based performance degrades substantially from 4V to 8V. Third, the LLM-assisted traffic-level metrics remain comparatively stable across the tested 4V-to-8V range. Fourth, provider reliability remains weak, fallback-heavy, and rate-limit constrained; the corrected 8V boundary records 4 successful provider calls out of 2,784 attempts.

### 8.2 Replace the existing paragraph under `What cannot be concluded?`

Replace the current bullet list with:

> The dissertation does not prove pure LLM superiority, general scalability to dense traffic, real-world validity, safety superiority, a visible effect from cooperative post-processing, sufficient provider reliability for deployment, or an independent Gemini-specific traffic benefit in the evaluated diagnostic condition.

### 8.3 Replace the current `RQ summary`

Replace the RQ summary with:

> **RQ1:** supported cautiously, at the pipeline level, but not as a clean causal claim about Gemini alone.  
> **RQ2:** no clear traffic-performance advantage for hybrid over raw LLM in the corrected evidence.  
> **RQ3:** safety layer present but insufficiently exercised.  
> **RQ4:** traffic robustness is visible from 4V to 8V, but provider reliability remains a major limitation, and prompt/fallback overlap now also limits attribution.

### 8.4 Replace the current `Main contribution`

Replace the current main contribution paragraph with:

> The dissertation's main contribution is a reproducible and traceable comparison of controller architectures for unsignalised intersection control, together with an explicit analysis of how live-provider availability, fallback behaviour, and prompt/fallback semantic overlap shape the final system behaviour. That is a stronger and more defensible contribution than a claim of universal LLM superiority.

### 8.5 Replace the current `Future work`

Replace the bullet list under future work with:

> Future work should focus on experimentally discriminative scenarios, stronger causal ablation, and states in which candidate policies genuinely disagree. It should also examine whether reducing unnecessary semantic overlap between prompt and fallback is methodologically justified, while preserving the same safety and traceability standards. Larger or more complex traffic conditions become more informative once identifiability has been established, not before. The aim should be cleaner causal identification, not weakening the baseline merely to make the LLM appear better.

### 8.6 Replace the current final conclusion paragraph

Replace the current final conclusion paragraph with:

> The corrected evidence shows that a frozen, traceable LLM-assisted decision pipeline can be implemented and evaluated systematically in SUMO. It can outperform the selected rule-based baseline on the tested traffic metrics, and the corrected 8V evidence confirms that the observed traffic behaviour persists in the larger of the two tested scales. At the same time, the post-hoc attribution evidence shows that the deterministic fallback policy accounts for the observed improvement in the examined 4V condition, while reliable Gemini decisions were behaviourally indistinguishable from fallback under the evaluated states. The final dissertation claim should therefore remain at the level of pipeline behaviour and experimental identifiability rather than pure LLM intelligence.

## 5. Delete/Replace List for Obsolete Existing Statements

| Existing statement or section | Action | Replacement / reason |
|---|---|---|
| `The evidence supports a cautious statement that the LLM-assisted pipeline improves traffic efficiency in the tested SUMO scenarios.` | Replace | Keep the traffic result, but add that the improvement is pipeline-level rather than isolated LLM causation. |
| `The LLM-assisted pipeline exhibited lower waiting time and higher mean speed than the rule-based baseline in the tested SUMO scenarios.` | Keep but qualify | This remains correct for the formal evidence, but it should not be followed by an implication of independent Gemini benefit. |
| `Provider reliability is the main interpretive limitation of the dissertation.` | Replace/qualify | Still valid, but experimental identifiability and prompt/fallback semantic overlap must now be added as co-equal limitations. |
| `The dissertation's main contribution is a reproducible and traceable comparison...` | Replace | Retain the contribution, but add attribution analysis and identifiability as part of the contribution boundary. |
| `The dissertation does not prove pure LLM superiority` | Keep | Still correct and now strengthened by the post-hoc attribution evidence. |
| `The LLM-assisted pipeline remains operational and shows comparatively stable traffic-level performance.` | Keep | This remains valid and supported by both formal and diagnostic evidence. |
| `The safety layer was implemented and operationally present, but the formal evidence did not sufficiently exercise it.` | Keep | Still valid. |
| `Future work should focus on higher-density traffic...` | Replace | Add explicit causal-identification priorities and avoid framing future work only as scaling. |

## 6. Final Consistency Check

### A. Still valid

- The formal experiment supports a pipeline-level traffic advantage for the LLM-assisted architecture over the selected rule-based baseline.
- The hybrid architecture does not show a clear traffic advantage over raw LLM in the corrected evidence.
- The safety verifier was implemented but not meaningfully exercised.
- The dissertation remains bounded to the tested 4V and 8V low-density scenarios.

### B. Valid but should be qualified

- The claim that the LLM-assisted pipeline improves traffic efficiency should be explicitly framed as a pipeline-level result, not as independent LLM causation.
- The claim that provider reliability is the main limitation should now be broadened to include experimental identifiability and prompt/fallback semantic overlap.
- The claim that the architecture is traceable should be paired with the warning that traceability does not guarantee causal identifiability.

### C. Potentially misleading if left unchanged

- Any wording that implies Gemini independently caused the traffic improvement.
- Any wording that implies the formal evidence alone isolates LLM contribution.
- Any wording that suggests the new diagnostic evidence is just a repeat of the formal experiment.

### D. Contradicted by the new diagnostic evidence

- A claim that there was a measurable incremental LLM-specific traffic benefit in the evaluated 4V diagnostic condition.
- A claim that downstream deterministic processing explains the similarity between Gemini and fallback.

## 7. Evidence-Boundary Check

The dissertation must continue to separate:

- formal experimental evidence, which supports a pipeline-level traffic comparison between controller architectures; and
- post-hoc attribution evidence, which shows that reliable Gemini execution does not, in the evaluated 4V condition, produce traffic or decision behaviour distinguishable from fallback.

The diagnostic evidence does not replace the formal experiment. It refines interpretation. The dissertation should therefore remain careful in two ways:

1. it may still claim that the architecture outperforms the selected rule-based baseline in the tested formal scenarios; and
2. it may not claim that the traffic advantage has been causally isolated to Gemini as an independent decision-maker.

## 8. Current Dissertation Claim Strength

**Recommended labels**

- `STRONG_PIPELINE_LEVEL_CONTRIBUTION`
- `LIMITED_LLM_SPECIFIC_EVIDENCE`
- `METHOD_REDESIGN_REQUIRED`

**Assessment**

The dissertation now supports a strong engineering and pipeline-level contribution, together with a clear methodological finding about attribution limits. The LLM-specific causal claim is limited by prompt/fallback semantic overlap and by the identical Gemini-vs-fallback decision traces in the evaluated states. That makes method redesign or a more discriminative experimental design necessary if the dissertation wishes to argue for independent LLM contribution in future work.
