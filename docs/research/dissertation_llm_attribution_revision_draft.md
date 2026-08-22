# Dissertation LLM Attribution Revision Draft

## 1. Evidence Summary

This review distinguishes between the retained formal experiment evidence and the later post-hoc attribution diagnostics.

### Formal evidence retained in the dissertation

- The formal matrix supports a pipeline-level traffic-performance comparison between the LLM-assisted architecture and the rule-based baseline.
- In the corrected formal evidence, the LLM-assisted modes achieve lower waiting time and higher mean speed than the rule-based baseline, while completion remains `100%` and collisions remain `0`.
- The formal evidence also shows that live-provider reliability is weak, fallback-dominated, and uneven across seeds and controller variants.

### Post-hoc attribution evidence

- Genuine Gemini Raw LLM 4V seed1 achieved `53/53` provider success, `53/53` parser success, complete provenance, `0` fallback usage, `100%` completion, `0` collision, operational waiting `11.0` steps, and mean speed approximately `7.5839 m/s`.
- Fallback-only 4V seed1 produced the same traffic outcome: operational waiting `11.0` steps and mean speed approximately `7.5839 m/s`.
- Rule-based 4V seed1 was materially worse: operational waiting `82.0` steps and mean speed approximately `2.3098 m/s`.
- Decision-level alignment between genuine Gemini and fallback-only was exact on all comparable rows: `132/132` raw agreement and `132/132` final agreement.
- The targeted high-discrimination probe identified `11` mixed route-group states, `39` comparable vehicle rows, and `39/39` agreement at both raw and final decision level.

### Interpretation boundary

The formal experiment still supports the claim that the overall LLM-assisted pipeline outperformed the rule-based baseline in the tested scenarios. However, the later attribution evidence does not support attributing that improvement to independent Gemini reasoning. Instead, the evidence indicates that the deterministic fallback policy accounts for the observed traffic advantage in the examined 4V condition, while reliable Gemini decisions were behaviourally indistinguishable from fallback under the evaluated states.

The correct dissertation boundary is therefore:

- valid: pipeline-level traffic advantage relative to the rule-based baseline;
- valid but qualified: provider reliability as a major limitation;
- newly required: semantic overlap between prompt and fallback as an identifiability limitation;
- not supported: a claim that the traffic improvement can be attributed cleanly to the LLM alone.

## 2. Proposed Chapter 6 Subsection

### 6.X Attribution of LLM-Specific Effects

The formal experiment supports a pipeline-level claim rather than a pure model-level claim. In the retained formal evidence, the LLM-assisted controllers outperform the rule-based baseline on the key traffic metrics, but the provider layer in those runs is highly unreliable and frequently replaced by deterministic fallback. As a result, the original formal matrix is best interpreted as evidence that the *architecture* can improve traffic efficiency under the tested scenarios, not as a clean demonstration that the LLM itself is the sole causal source of the improvement.

The subsequent genuine Gemini 4V seed1 diagnostic pilot removes that particular reliability confound for one controlled condition. In that pilot, all `53` logical provider requests succeeded, all `53` responses parsed successfully, and no fallback was used. This establishes that the live Gemini path can execute reliably under the evaluated configuration. It also means that, in this diagnostic condition, the traffic outcome cannot be dismissed as an artefact of provider failure.

However, the traffic comparison does not reveal an incremental LLM-specific benefit. The rule-based controller is substantially more conservative than the fallback-only controller, but the fallback-only and genuine Gemini runs are identical on the observed traffic measures: both achieve operational waiting of `11.0` steps, mean speed of approximately `7.5839 m/s`, full completion, and zero collisions. In other words, the large improvement relative to the rule-based baseline is recovered by the deterministic fallback policy itself, whereas genuine Gemini participation does not add further traffic improvement in this seed.

This conclusion is reinforced at the decision level. On all `132` comparable rows, the Gemini raw decisions match the fallback-only raw decisions exactly, and the same perfect agreement persists at the final decision level. Because the similarity is already present at the raw layer, it cannot be explained as a downstream deterministic correction of divergent LLM proposals. The similarity is visible before any final safety or validation stage has an opportunity to alter the output.

A targeted analysis of the most discriminative observed states reaches the same conclusion. Across `11` mixed route-group states and `39` comparable vehicle-row decisions, Gemini again matches fallback exactly at both raw and final decision level. That strengthens the attribution result, but it still does not prove global policy equivalence. It does, however, show that the current prompt and state representation are sufficiently aligned with the fallback semantics that the evaluated states do not elicit a distinguishable LLM-specific policy.

The most defensible interpretation is therefore that fallback-dominant attribution remains the correct reading of the evidence. The current Gemini configuration reproduces the deterministic fallback behaviour under the evaluated states, and no incremental LLM-specific traffic benefit has yet been demonstrated.

## 3. Proposed Chapter 7 Subsection

### 7.X Experimental Identifiability of the LLM Contribution

The architecture is traceable, but traceability alone does not guarantee that its components are experimentally identifiable. In this dissertation, the canonical prompt and the deterministic fallback policy both reason over closely related information: route compatibility and conflict structure, vehicle priority or approach state, and a constrained action set consisting of `PROCEED`, `WAIT`, and `FREE`. This creates a methodological risk that the LLM is not being asked to discover an independent policy, but rather to reproduce a policy already encoded in deterministic form.

The post-hoc attribution evidence makes this identifiability issue concrete. Even when the provider is reliable and the Gemini path executes successfully with complete provenance, the evaluated 4V seed1 condition still produces no observable divergence from fallback-only behaviour. The decision-level audit shows perfect agreement on all comparable rows, and the high-discrimination probe repeats that perfect agreement in states that should, in principle, have been capable of exposing a difference.

This does not establish universal equivalence between Gemini and the deterministic fallback policy. It does not show that Gemini is incapable of different decisions in all traffic states, nor does it show that LLMs have no general value for intersection control. What it does show is narrower and methodologically more important: within the current prompt, route representation, and state space, the experiment did not produce evidence of an independent LLM contribution.

Accordingly, provider reliability is no longer the only major validity threat. Even a fully reliable live provider would not by itself resolve the attribution problem if the prompt and fallback semantics remain so closely aligned that they collapse onto the same decision surface. This is a limitation of experimental identifiability, not merely of connectivity or rate limiting.

The limitation matters because it constrains what can be inferred from the formal traffic results. The dissertation can still claim a favourable pipeline-level comparison against the rule-based baseline, but it cannot claim that the observed traffic improvement has been causally isolated to the LLM component alone.

## 4. Optional Chapter 8 Future-Work Paragraph

Future work should focus on improving causal identifiability rather than merely increasing model size or execution cost. A stronger design would introduce more discriminative traffic states, reduce unnecessary semantic overlap between prompt and fallback where scientifically justified, and evaluate explicit counterfactual pairs in which deterministic and LLM-based policies are genuinely in tension. If future experiments are pursued, they should compare the LLM and deterministic heuristic on states with competing route conflicts, near-tie priority cases, and more complex multi-vehicle interactions, while preserving the same safety and traceability standards. The aim should be a cleaner separation of policy contribution, not the manufacture of disagreement for its own sake.

## 5. Existing Claims Requiring Qualification

| Existing claim | Status | Why |
|---|---|---|
| `LLM-assisted pipelines achieved better traffic performance` | B. Valid but should be qualified | Supported at the pipeline level versus the rule-based baseline, but not as proof of independent LLM causation. |
| `fallback-heavy execution remains the dominant explanatory factor` | B. Valid but should be qualified | Still supported for the formal evidence, but the later Gemini pilot shows that a reliable LLM path can exist without changing the traffic outcome. |
| `the architecture demonstrates LLM-assisted cooperative control` | B. Valid but should be qualified | The architecture is real and operational, but the attribution evidence shows that the observed traffic advantage does not isolate LLM-specific contribution. |
| `provider reliability is the main limitation` | B. Valid but should be qualified | Still true for the formal evidence, but experimental identifiability and prompt/fallback semantic overlap now also require explicit discussion. |
| `the LLM-assisted pipeline remained operational and showed comparatively stable traffic-level performance` | A. Still valid | This is consistent with the formal evidence and with the diagnostic pilot. |

## 6. Claims That Should Not Be Made

- Do not claim that Gemini independently caused the traffic improvement.
- Do not claim that Gemini and fallback are globally equivalent.
- Do not claim that LLMs provide no benefit.
- Do not claim that Gemini simply copies the fallback algorithm.
- Do not claim pure model superiority.
- Do not claim that the diagnostic evidence proves universal policy equivalence.
- Do not collapse the formal experiment and the post-hoc attribution evidence into a single undifferentiated dataset.

## 7. Recommended Insertion Locations

### Chapter 6

- Insert the new subsection after the existing RQ1 discussion in `docs/dissertation/full_draft_submission_v7.md`, around the discussion material that states the LLM-assisted pipeline has lower waiting time than the rule-based baseline.
- A natural anchor is the current discussion block near line `949` in `docs/dissertation/full_draft_submission_v7.md`, where the draft already states that the pipeline can outperform the rule-based baseline but that provider reliability remains a first-order validity threat.

### Chapter 7

- Insert the new subsection after the existing limitations discussion on provider reliability in `docs/dissertation/full_draft_submission_v7.md`, around the current material near line `951`.
- This is the most appropriate place to add the identifiability limitation because it extends the current provider-reliability argument without duplicating Chapter 6.

### Chapter 8

- Insert the future-work paragraph in `docs/dissertation/full_draft_submission_v7.md` after the existing future-work discussion of provider availability and alternative execution paths.
- The existing conclusion/future-work wording near the end of the chapter is a suitable anchor because it already frames future work as a method-improvement question rather than a claim of proven superiority.

## 8. Recommended Reading Order for Revision

1. Update Chapter 6 to add the attribution subsection.
2. Update Chapter 7 to add the experimental identifiability subsection.
3. Append the short future-work paragraph to Chapter 8.
4. Keep the formal-results language unchanged except for qualification where the new attribution evidence now requires it.

## 9. Bottom Line

The strongest defensible interpretation remains:

> The evaluated LLM-assisted architecture achieved favourable pipeline-level traffic performance relative to the original rule-based baseline, but subsequent attribution experiments showed that the deterministic fallback policy accounts for the observed improvement in the examined 4V condition, while reliable Gemini decisions were behaviourally indistinguishable from fallback under the evaluated states.

This is a bounded empirical result, not a global statement about LLM-based traffic control.
