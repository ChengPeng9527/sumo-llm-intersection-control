# Final Dissertation Replacement Text Package

This package is written for the final dissertation editing pass only. It does not modify the dissertation itself.

## PART A - Replacement Abstract

Replace the current Abstract with the following text:

> This dissertation examines whether a structured LLM-assisted decision pipeline can support unsignalised intersection control in Simulation of Urban MObility (SUMO). The architecture separates prompt construction, live-provider requests, parsing, deterministic validation, deterministic fallback, cooperative post-processing, safety verification, and trace logging so that each stage can be observed independently. Four controller configurations were evaluated: a rule-based baseline, a raw LLM controller, a hybrid controller with cooperative post-processing, and a hybrid controller with an additional safety-verification layer. The retained formal evidence comprises valid 4V runs from `formal_v2` and corrected 8V runs from `formal_v4`. Across that formal boundary, the LLM-assisted pipeline exhibits lower operational waiting and higher mean speed than the selected rule-based baseline, with complete vehicle completion and no collisions, but the formal result must be interpreted at pipeline level because live-provider reliability was poor and fallback dominated many runs. Post-hoc diagnostic work then established a reliable Gemini 4V seed1 condition with complete provider success, complete parser success, complete provenance, and no fallback usage. In that diagnostic condition, fallback-only behaviour produced the same traffic outcome, and decision-level as well as high-discrimination analyses showed complete Gemini-vs-fallback agreement on the evaluated states. The dissertation therefore contributes a reproducible and traceable comparison of controller architectures, together with an explicit attribution analysis showing that favourable pipeline-level performance cannot be attributed independently to the LLM in the evaluated evidence.

## PART B - Chapter 1 Patches

### B1. Contributions replacement

Replace the current contribution paragraph in Section 1.5 with:

> The main contributions of the dissertation are therefore:
> - the implementation of four comparable controller architectures within a common SUMO unsignalised-intersection environment;
> - a modular LLM-assisted decision pipeline combining model-generated decisions with deterministic validation, fallback handling, cooperative processing, and safety verification;
> - a controlled evaluation of traffic performance across four-vehicle and eight-vehicle scenarios; and
> - an evaluation framework that considers provider reliability, parsing, fallback behaviour, downstream interventions, and attribution limits alongside conventional traffic-performance measures.
>
> Together, these contributions provide an experimental basis for assessing both the potential and the practical limitations of integrating LLM-based reasoning into cooperative traffic-control systems, while keeping the claim boundary at the level of the complete pipeline rather than independent LLM superiority.

### B2. Aim, objectives, and research questions

No textual replacement is required for the aim, objectives, or research questions if the editor keeps the current phrasing careful and pipeline-level.

If a small terminology consistency pass is desired, keep the present RQs but ensure that the surrounding prose uses "LLM-assisted pipeline" for system-level outcomes and reserves "Gemini" or "live LLM" for the diagnostic evidence.

## PART C - Chapter 3 Fallback Replacement

Replace Section 3.5.3 `Deterministic Fallback` with:

> The deterministic fallback is not merely an error stub that returns WAIT. It is a local traffic-control policy used when the live model response is unavailable or unusable, and it operates inside the same restricted action space as the rest of the pipeline. Vehicles outside the active control region are assigned FREE. For vehicles inside the control region, the fallback policy uses a deterministic priority rule based on proximity or time-to-intersection together with route-compatibility information and conflicting-movement structure. The priority vehicle is allowed to PROCEED, compatible vehicles may also be permitted to PROCEED, and vehicles that conflict with the active movement are assigned WAIT. This means the fallback policy can release multiple compatible vehicles in the same decision episode rather than simply blocking every non-priority vehicle.
>
> This distinction matters because the rule-based baseline is stricter. The baseline assigns FREE to vehicles outside the control zone, PROCEED to the priority vehicle, and WAIT to all other controlled vehicles. By contrast, the fallback policy is a meaningful deterministic control rule that can produce better traffic progression even without any live provider contribution. That is why fallback-dominant evidence must be interpreted as pipeline behaviour rather than as direct evidence of live LLM superiority.

## PART D - Chapter 4 Evidence-Boundary Patch

Use the following insertion text at the end of Section 4.9, or as a short bridge paragraph immediately after Chapter 4 and before Chapter 5:

> Supplementary attribution analyses were conducted after the retained formal evaluation to refine interpretation of the observed traffic results. These analyses use separate live Gemini diagnostics, fallback-only comparisons, and decision-level agreement checks. They are discussed in Chapters 6 and 7 and are not part of the retained 24-run formal matrix. The formal evidence boundary therefore remains unchanged: Chapter 4 reports the validated formal runs, while the post-hoc diagnostics are used only to refine attribution.

## PART E - Chapter 5 Wording Replacements

Chapter 5 does not require a full rewrite, but the following wording replacements are recommended wherever the current text sounds too causal.

| Location | Current text | Replace with |
|---|---|---|
| Results interpretation for traffic performance | `The LLM-assisted pipelines achieved lower operational waiting time and higher mean speed than the rule-based baseline in the tested scenarios.` | `The LLM-assisted pipelines exhibited lower operational waiting time and higher mean speed than the selected rule-based baseline in the tested scenarios.` |
| Any sentence implying model-level causation in the results narrative | `The LLM-assisted pipeline improves traffic efficiency.` | `The LLM-assisted pipeline exhibits lower operational waiting time and higher mean speed in the tested scenarios.` |
| Any sentence that reads as if the model alone caused the effect | `The LLM performed better than the baseline.` | `The LLM-assisted pipeline performed better than the selected rule-based baseline at the pipeline level.` |

If the editor wants a stricter Chapter 5 pass, the guiding rule should be:

> Use "exhibits" or "shows" for observed traffic results, and reserve "causes" or "improves" only for statements that are explicitly bounded to the complete pipeline and supported by the attribution evidence.

## PART F - Complete Replacement Chapter 6

Replace Chapter 6 with the following text.

### 6.1 RQ1: Rule-based versus LLM-assisted architecture

The corrected formal evidence supports a pipeline-level claim that the LLM-assisted architecture achieves lower waiting time and higher mean speed than the selected rule-based baseline in the tested SUMO scenarios. In the retained formal matrix, the LLM-assisted controllers outperform the stricter rule-based controller on the traffic measures that are most informative in this study, and that is the most defensible reading of the formal results.

The attribution evidence, however, requires this result to be framed carefully. The formal runs were heavily fallback-dominated, so the observed traffic advantage cannot be attributed directly to independent live-provider reasoning. The correct interpretation is that the LLM-assisted architecture performs better as an operational pipeline under the tested conditions, but the formal evidence alone does not isolate the LLM component as the sole causal source of that improvement.

The later genuine Gemini 4V seed1 diagnostic pilot clarifies this point. In that pilot, all 53 logical provider requests succeeded, all 53 responses parsed successfully, and no fallback was used. This removes the provider-failure confound for that diagnostic condition. Even so, the traffic outcome did not improve beyond fallback-only: Gemini and fallback-only both achieved operational waiting of 11.0 steps, mean speed of approximately 7.5839 m/s, full completion, and zero collisions.

Taken together, the formal and diagnostic evidence support a pipeline-level claim only. The dissertation can state that the architecture is effective in the tested scenarios, but it should not state that the LLM itself independently caused the traffic-performance improvement.

### 6.2 RQ2: Raw LLM versus hybrid control

The corrected evidence does not show a clear traffic-performance advantage for the hybrid architecture over the raw LLM architecture. The hybrid and raw LLM modes remain effectively similar on the traffic metrics, and the corrected formal evidence does not show a material postprocessor effect.

The most plausible reading is that the cooperative layer is implemented and traceable, but rarely exercises enough influence to produce a measurable traffic-level gain in the valid formal evidence. The absence of a clear hybrid advantage should therefore be reported as an empirical result, not as a design failure. It indicates limited differentiation between the raw LLM and the cooperative stage in the evaluated conditions.

### 6.3 RQ3: Safety layer behaviour

The corrected valid evidence shows that the safety layer is present, traceable, and operational, but it is not meaningfully exercised in the final evidence set. Collisions remain at 0 and safety overrides remain at 0, which means the verifier did not become an active differentiating factor in the tested scenarios.

The dissertation should therefore avoid claiming that safety improved the measured traffic metrics. The defensible claim is narrower: deterministic safety verification was implemented, logged, and available, but the tested scenarios did not produce enough unsafe or conflict-inducing states to demonstrate a visible safety-efficiency trade-off.

### 6.4 RQ4: 4V to 8V scalability

The corrected evidence supports only a bounded scalability claim. The traffic-side behaviour remains comparatively stable from 4V to 8V in the corrected evidence, while provider reliability becomes weaker and more fallback-heavy at the larger scale.

This is not a basis for a general scalability claim. It supports only the statement that, under the frozen low-density scenario used here, the pipeline remains operational at both scales and the traffic metrics remain comparatively stable. The attribution evidence also shows that stable traffic metrics do not necessarily imply an independent LLM contribution.

### 6.5 Attribution of LLM-specific effects

The formal experiment supports a pipeline-level claim rather than a pure model-level claim. In the retained formal evidence, the LLM-assisted controllers outperform the rule-based baseline on the key traffic metrics, but the provider layer in those runs is highly unreliable and frequently replaced by deterministic fallback. As a result, the formal matrix is best interpreted as evidence that the architecture can improve traffic efficiency under the tested scenarios, not as a clean demonstration that the LLM itself is the sole causal source of the improvement.

The genuine Gemini 4V seed1 diagnostic pilot removes that reliability confound for one controlled condition. In that pilot, all 53 logical provider requests succeeded, all 53 responses parsed successfully, and no fallback was used. This establishes that the live Gemini path can execute reliably under the evaluated configuration. It also means that, in this diagnostic condition, the traffic outcome cannot be dismissed as an artefact of provider failure.

However, the traffic comparison does not reveal an incremental LLM-specific benefit. The rule-based controller is substantially more conservative than the fallback-only controller, but the fallback-only and genuine Gemini runs are identical on the observed traffic measures: both achieve operational waiting of 11.0 steps, mean speed of approximately 7.5839 m/s, full completion, and zero collisions. In other words, the large improvement relative to the rule-based baseline is recovered by the deterministic fallback policy itself, whereas genuine Gemini participation does not add further traffic improvement in this seed.

This conclusion is reinforced at the decision level. On all 132 comparable rows, the Gemini raw decisions match the fallback-only raw decisions exactly, and the same perfect agreement persists at the final decision level. Because the similarity is already present at the raw layer, it cannot be explained as a downstream deterministic correction of divergent LLM proposals. The similarity is visible before any final safety or validation stage has an opportunity to alter the output.

A targeted analysis of the most discriminative observed states reaches the same conclusion. Across 11 mixed route-group states and 39 comparable vehicle-row decisions, Gemini again matches fallback exactly at both raw and final decision level. That strengthens the attribution result, but it still does not prove global policy equivalence. It does, however, show that the current prompt and state representation are sufficiently aligned with the fallback semantics that the evaluated states do not elicit a distinguishable LLM-specific policy.

The most defensible interpretation is therefore that fallback-dominant attribution remains the correct reading of the evidence. The current Gemini configuration reproduces the deterministic fallback behaviour under the evaluated states, and no incremental LLM-specific traffic benefit has yet been demonstrated.

### 6.6 Relationship to existing literature

The broader literature on autonomous intersection management, embodied reasoning, and hybrid decision architectures supports the dissertation's central methodological point: complex control systems should be evaluated as pipelines rather than as opaque end-to-end models. The present results extend that idea by showing that a traceable LLM-assisted pipeline can be implemented in SUMO, but that attribution remains difficult when the prompt and fallback semantics overlap closely.

This is consistent with the general literature on safety-relevant autonomy, which treats reliability, validation, and component separation as necessary conditions for meaningful evaluation. The dissertation therefore contributes not only a traffic-control implementation, but also an attribution lesson: a live LLM can be present and reliable without producing a traffic effect distinguishable from deterministic fallback.

### 6.7 Overall interpretation

The dissertation's strongest supported claim is a pipeline-level one. The architecture is modular, traceable, and operational in SUMO; it can outperform the selected rule-based baseline on the tested traffic metrics; and the later diagnostic evidence shows that reliable live Gemini execution is possible under the evaluated configuration.

At the same time, the dissertation does not establish independent LLM-specific superiority. The attribution evidence indicates that the deterministic fallback policy accounts for the observed traffic advantage in the examined 4V condition, while reliable Gemini behaviour is indistinguishable from fallback on the evaluated states. The correct final reading is therefore that the architecture works, the pipeline-level traffic result is real, and the independent causal contribution of the LLM remains unisolated.

## PART G - Complete Replacement Chapter 7

Replace Chapter 7 with the following text.

### 7.1 Experimental scale and statistical scope

The dissertation remains limited to a small number of controller-scale cells and seeds. The corrected formal evidence covers only 4V and 8V, with three seeds per controller-scale cell. That is sufficient for a descriptive comparison, but not for strong inferential claims or generalisation beyond the tested design.

### 7.2 Simulation scope and external validity

The evidence is simulation-based and restricted to a single low-density, unsignalised intersection. This makes the comparison controlled and reproducible, but it also narrows the scope of inference. The dissertation supports simulation-level claims about the tested SUMO scenario, not claims about dense traffic, multiple intersections, heterogeneous layouts, or real-road deployment.

### 7.3 Historical provider reliability and fallback dependence

Historical provider reliability remains a major validity threat for the formal evidence. In the corrected formal matrix, provider success is low, fallback-heavy execution is the norm, and successful provider calls are sparse and seed-sensitive. That means the traffic results in the formal dataset must be interpreted as pipeline outcomes under constrained provider availability rather than as pure model performance.

This limitation is not merely operational. It changes the meaning of the traffic comparisons, because a system that frequently falls back to deterministic control is not equivalent to a system whose decisions are consistently produced by live LLM reasoning. The dissertation therefore cannot claim that the formal traffic benefit isolates the LLM component.

### 7.4 Experimental identifiability of the LLM contribution

Traceability allows the dissertation to observe which component produced a given decision, but traceability alone does not make causal contribution identifiable. In this project, the canonical prompt and the deterministic fallback policy encode substantially overlapping decision semantics. Both reason over route compatibility and conflict structure, vehicle priority or approach state, and the constrained PROCEED / WAIT / FREE decision space.

That overlap creates an identifiability problem. Even when Gemini is reliable and all requests succeed, the system can still produce behaviour that is indistinguishable from the deterministic heuristic. The diagnostic 4V seed1 pilot makes this explicit: Gemini was reliable, provenance was complete, yet the observed traffic behaviour matched fallback-only exactly; the decision-level audit and the high-discrimination probe both found complete agreement.

This does not show that Gemini and fallback are globally equivalent. It does not show that Gemini cannot contribute in other traffic states. What it does show is narrower and more important for this dissertation: the current experiment does not isolate an independent LLM contribution. The evidence is strong enough to support pipeline-level attribution, but not strong enough to support a claim of distinct LLM reasoning value in the evaluated states.

### 7.5 Cooperative and safety mechanisms

The cooperative postprocessor and safety verifier are part of the architecture and are clearly logged, but the corrected formal evidence shows that they are not strongly exercised. The cooperative layer does not produce a visible traffic advantage, and the safety verifier records zero overrides in the final evidence set. Their presence is therefore methodologically important, but their causal effect is limited in the evaluated runs.

The absence of visible intervention should not be mistaken for evidence that the stages are useless in general. It only shows that the retained scenarios do not create enough opportunities for those mechanisms to alter the observed behaviour in a measurable way.

### 7.6 Metrics and evidence limitations

Completion rate saturates at 100% across the valid runs, so it is not a useful differentiator by itself. The more informative metrics are waiting time, mean speed, provider success, parser success, fallback rate, and decision-flow agreement. Even those measures must be interpreted with care, because identical traffic metrics can arise from different causal pathways.

The dissertation also depends on corrected evidence provenance. The nominal 8V traces in the original batch are not retained as final evidence because they were later shown to have loaded the wrong scenario configuration. That correction strengthens the final analysis, but it also demonstrates the importance of execution-level validation in simulation studies.

### 7.7 Overall scope of the conclusions

Taken together, these limitations define a relatively narrow interpretation of the dissertation findings. The study provides evidence that a structured and traceable LLM-assisted pipeline can be implemented and evaluated in a controlled SUMO intersection scenario, and that the complete pipeline produced favourable traffic metrics relative to the selected rule-based baseline in the tested conditions.

However, the experiments do not establish superiority of the LLM component itself, general scalability, real-world effectiveness, or measurable benefits from the cooperative and safety stages. The strongest conclusion is therefore a pipeline-level one: the architecture remained operational and produced comparatively efficient traffic behaviour under the evaluated conditions, while external-provider reliability and attribution identifiability substantially constrained the extent to which this behaviour could be attributed to live LLM decision-making.

## PART H - Complete Replacement Chapter 8

Replace Chapter 8 with the following text.

### 8.1 Conclusion

This dissertation investigated whether a structured LLM-assisted decision pipeline could support cooperative decision-making at an unsignalised intersection in SUMO. Rather than treating the LLM as an end-to-end controller, the proposed architecture separates model-based decision generation from response parsing, deterministic validation and fallback, cooperative post-processing, safety verification, and trace logging. This design enabled the behaviour of different stages of the control pipeline to be recorded and evaluated separately.

Four controller architectures were evaluated: a rule-based baseline, a Raw LLM controller, a Hybrid controller incorporating cooperative post-processing, and a Hybrid + Safety controller incorporating both cooperative post-processing and deterministic safety verification. The final evaluation considered four-vehicle and eight-vehicle scenarios with three seeds for each controller-scale condition.

The corrected evidence shows a clear difference between the rule-based baseline and the LLM-assisted pipelines within the tested scenarios. At 4V, the rule-based controller recorded a mean operational waiting measure of approximately 82 steps and a mean speed of 2.31 m/s, compared with approximately 15 steps and 6.80 m/s for the LLM-assisted controllers. At 8V, the difference became larger: the rule-based controller recorded approximately 242.04 waiting steps and a mean speed of 1.19 m/s, whereas the LLM-assisted controllers recorded approximately 15.29 waiting steps and 6.60 m/s. All retained runs achieved complete vehicle arrival and no collisions were recorded.

These results indicate that the evaluated LLM-assisted pipelines maintained comparatively stable traffic-level performance as the scenario increased from four to eight vehicles, while the rule-based baseline experienced a substantial reduction in efficiency. However, this result must be interpreted together with the reliability evidence and the later attribution evidence. In the corrected 8V experiments, only 4 of 2,784 live-provider requests succeeded, and the post-hoc Gemini diagnostics showed that when live Gemini was reliable, its behaviour matched fallback-only in the evaluated 4V condition. The observed traffic performance therefore characterises the complete fallback-capable architecture under constrained provider availability rather than the independent capability of the LLM.

### 8.2 Answers to the Research Questions

RQ1 asked whether an LLM-assisted architecture could improve traffic efficiency relative to rule-based control. Within the evaluated SUMO scenarios, the LLM-assisted pipelines produced substantially lower operational waiting and higher mean speed than the rule-based baseline. This supports a pipeline-level performance advantage under the tested conditions, but it does not establish that the LLM component itself was responsible for the improvement.

RQ2 examined whether cooperative post-processing meaningfully changed the behaviour of the Raw LLM controller. No clear traffic-performance advantage was observed for the Hybrid controller over the Raw LLM controller. The corrected evidence contains insufficient postprocessor intervention to establish a measurable benefit from the cooperative stage. Consequently, the study confirms the presence and traceability of this stage but not its effectiveness.

RQ3 considered the effect of deterministic safety verification. No collisions occurred in the retained experiments, but no safety overrides were recorded either. The safety verifier was therefore implemented as part of the architecture but was not sufficiently exercised by the tested scenarios to establish either a safety benefit or a safety-efficiency trade-off.

RQ4 examined behaviour as the scenario increased from four to eight vehicles. The rule-based baseline showed substantially higher operational waiting and lower mean speed at 8V, whereas the traffic metrics of the LLM-assisted pipelines remained comparatively stable. This provides evidence of robustness across the evaluated 4V-to-8V range. It does not demonstrate general scalability to denser traffic, larger vehicle populations, or more complex road networks.

### 8.3 Contributions

The principal contribution of this dissertation is a reproducible and traceable framework for evaluating LLM-assisted decision pipelines for unsignalised intersection control. The study demonstrates how model proposals, validation, fallback handling, cooperative processing, safety verification, and final control decisions can be separated rather than evaluated as a single opaque controller.

A second contribution is the inclusion of provider reliability and decision provenance as part of the experimental evaluation. The results demonstrate why traffic-level performance alone can provide an incomplete account of an LLM-assisted control system. In this study, favourable traffic metrics coexisted with extremely low live-provider availability, making fallback behaviour essential to understanding the observed results.

The dissertation therefore contributes primarily an engineering and evaluation framework rather than evidence of general LLM superiority in autonomous driving. Its value lies in showing how an LLM-assisted controller can be evaluated in a way that distinguishes system-level performance from the behaviour of the underlying language model.

### 8.4 Future Work

Future work should first address causal identification and experimental discriminability. The most useful next step is not simply to scale the scenario, but to create conditions in which deterministic fallback and live LLM decisions genuinely disagree. That would allow the LLM contribution to be isolated more cleanly.

A second priority is controlled ablation. Experiments could separately disable deterministic fallback, cooperative post-processing, and safety verification to quantify the contribution of each stage. In particular, scenarios containing deliberately constructed route conflicts and cooperative opportunities would allow the postprocessor and safety verifier to be exercised systematically rather than merely remaining available in the pipeline.

The experimental scope should also be expanded after identifiability has been strengthened. Higher-density traffic, larger vehicle populations such as 16V scenarios, additional intersection geometries, and a larger number of random seeds would provide stronger evidence about robustness and scalability. More complex scenarios could additionally include heterogeneous traffic behaviour, communication uncertainty, or multiple interacting intersections.

Finally, simulation results should eventually be tested under progressively more realistic conditions. Hardware-in-the-loop experiments, real-time execution constraints, and ultimately appropriately controlled physical validation would provide evidence about whether the pipeline architecture remains practical when assumptions made in SUMO no longer hold.

## PART I - Terminology Standard

Use the following terms consistently in the final dissertation edit:

- `LLM-assisted pipeline` for system-level outcomes and behaviour.
- `Raw LLM`, `Hybrid`, and `Hybrid + Safety` only as controller labels.
- `live LLM` or `Gemini` only when referring to the diagnostic provider evidence.
- `deterministic fallback` for the local fallback policy.
- `rule-based baseline` for the comparison controller in the formal experiment.
- `provider success` and `parser success` as separate reliability metrics.
- `operational waiting` when referring to the dissertation metric.
- `traceability` for the ability to observe each stage of the pipeline separately.

Avoid the following:

- using `LLM controller` when `LLM-assisted pipeline` is more precise;
- using `pure LLM performance` except in negative or qualifying statements;
- using `equivalent` or `identical` for Gemini and fallback except where the evidence explicitly supports it in the evaluated states;
- collapsing the rule-based baseline and the deterministic fallback into a single concept.

## PART J - Old -> New Replacement Map

### 1. Abstract

- **Location:** Abstract paragraphs 3 to 6
- **Current text:** begins `Large language models (LLMs) have shown potential for high-level reasoning and decision-making...`
- **Action:** `REPLACE`
- **New text:** use the full abstract in Part A
- **Reason:** incorporate the final attribution evidence and keep the claim boundary at pipeline level

### 2. Chapter 1 contributions

- **Location:** Section 1.5, contribution list, paragraphs 39 to 44
- **Current text:** begins `the implementation of four comparable controller architectures within a common SUMO unsignalised-intersection environment;`
- **Action:** `REPLACE`
- **New text:** use the contribution paragraph in Part B1
- **Reason:** remove any implication that the LLM alone caused the observed traffic improvement

### 3. Chapter 3 fallback subsection

- **Location:** Section 3.5.3 `Deterministic Fallback`
- **Current text:** begins `The LLM-assisted architectures include deterministic fallback behaviour for cases in which a usable model response is unavailable.`
- **Action:** `REPLACE`
- **New text:** use the fallback subsection in Part C
- **Reason:** explain that fallback is a meaningful deterministic control policy, not a simple failure stub

### 4. Chapter 4 evidence boundary

- **Location:** Section 4.9, or the bridge between Chapters 4 and 5
- **Current text:** the current chapter ends without a clear statement that the later attribution diagnostics are supplementary
- **Action:** `INSERT`
- **New text:** use the insertion paragraph in Part D
- **Reason:** keep the formal experiment boundary separate from the post-hoc attribution evidence

### 5. Chapter 5 wording

- **Location:** Chapter 5 traffic-results narrative
- **Current text:** `The LLM-assisted pipelines achieved lower operational waiting time and higher mean speed than the rule-based baseline in the tested scenarios.`
- **Action:** `REPLACE`
- **New text:** `The LLM-assisted pipelines exhibited lower operational waiting time and higher mean speed than the selected rule-based baseline in the tested scenarios.`
- **Reason:** soften causal wording without changing any numbers

### 6. Chapter 6

- **Location:** Entire Chapter 6
- **Current text:** begins `1. RQ1: Rule-based vs LLM-assisted architecture`
- **Action:** `REPLACE`
- **New text:** use the full Chapter 6 in Part F
- **Reason:** integrate formal traffic results, fallback-dominant attribution, and the live Gemini diagnostic into one coherent discussion

### 7. Chapter 7

- **Location:** Entire Chapter 7
- **Current text:** begins `7.1 Experimental scale and statistical scope`
- **Action:** `REPLACE`
- **New text:** use the full Chapter 7 in Part G
- **Reason:** make experimental identifiability a core limitation rather than a side note

### 8. Chapter 8

- **Location:** Entire Chapter 8
- **Current text:** begins `8.1 Conclusion`
- **Action:** `REPLACE`
- **New text:** use the full Chapter 8 in Part H
- **Reason:** ensure the final conclusion matches the evidence boundary and the attribution result

## PART K - Final Evidence-Boundary Verification

Before applying the next edit pass, verify that the final dissertation still obeys the following boundary:

1. The retained formal evidence supports a pipeline-level traffic comparison only.
2. The later Gemini diagnostics are supplementary attribution evidence, not part of the retained formal matrix.
3. The dissertation can claim a traceable LLM-assisted architecture and favourable pipeline-level traffic performance.
4. The dissertation cannot claim independent LLM superiority, because the reliable Gemini diagnostic condition matched fallback-only behaviour on the evaluated states.
5. Rule-based baseline and deterministic fallback remain distinct and must not be collapsed into one concept.
6. Chapter 6 should perform the interpretation, Chapter 7 should state the limitation, and Chapter 8 should restate the final boundary and future-work priorities.

## Final Status

`REPLACEMENT_PACKAGE_READY_WITH_MINOR_ISSUES`

Minor issues remain only in the sense that citation placement and any later title-page placeholders still need the final human editing pass. The actual replacement text package is complete and ready for direct use.
