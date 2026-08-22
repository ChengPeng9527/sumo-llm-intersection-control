# Final Dissertation Consistency Audit

## 1. Executive Assessment

The dissertation is close to a coherent final state, but it is not yet fully consistent with the final attribution evidence.

The retained formal experiment still supports a pipeline-level claim: the LLM-assisted architecture outperforms the selected rule-based baseline on the tested traffic metrics in the formal 4V and corrected 8V evidence. However, the post-hoc diagnostic work materially changes the attribution story. Reliable Gemini execution in the 4V seed1 diagnostic condition did not produce any incremental traffic or decision benefit beyond fallback-only behaviour, and the decision-level traces show complete Gemini-vs-fallback agreement in the evaluated states.

That means the dissertation can still defend a strong engineering and pipeline-level contribution, but it cannot defend an independent LLM-specific traffic-improvement claim. The writing therefore needs a final consistency pass across the Abstract, Chapter 1, Chapter 6, Chapter 7, and Chapter 8 so that the thesis reads as one argument rather than two partially overlapping ones.

### Final status

`MAJOR_CONSISTENCY_REVISION_REQUIRED`

### Why this status is necessary

- The abstract still needs to be rewritten to incorporate the attribution finding explicitly.
- Chapter 6 needs to be revised so the new attribution logic is integrated into the RQ1 discussion rather than appended as a separate note.
- Chapter 7 needs a stronger identifiability limitation.
- Chapter 8 needs targeted replacement paragraphs so the final conclusion is not read as an LLM-superiority claim.
- Chapter 3 should disclose enough fallback semantics for the later attribution result to make methodological sense.

## 2. Final Research Story

The dissertation should now present the following story, consistently across the whole document:

1. A modular LLM-assisted SUMO intersection-control architecture was designed and implemented.
2. The formal experiment showed that the LLM-assisted pipeline achieved lower waiting time and higher mean speed than the selected rule-based baseline.
3. Historical live-provider reliability was extremely poor, so the formal evidence could not isolate an independent LLM contribution.
4. Later diagnostic work established a reliable Gemini 4V seed1 condition with complete provider success, complete parser success, and complete provenance.
5. Under that reliable condition, traffic performance did not improve beyond fallback-only behaviour.
6. Decision-level and high-discrimination analyses found complete Gemini-vs-fallback agreement in all evaluated comparable states.
7. The main methodological issue is therefore experimental identifiability: the prompt and fallback semantics overlap substantially.
8. The dissertation can claim pipeline-level effectiveness and traceable integration, but not independent LLM-specific superiority.

## 3. Evidence Hierarchy

### Level 1: Formal retained experimental evidence

- What it supports: pipeline-level traffic comparison, bounded RQ answers, corrected 4V and 8V formal results.
- What it does not support: independent Gemini causation, fallback-vs-LLM attribution, global scalability, or pure model superiority.

### Level 2: Post-hoc live Gemini diagnostic evidence

- What it supports: reliable provider execution in the 4V seed1 diagnostic condition; a clean live-LLM comparison free of the earlier provider-failure confound.
- What it does not support: claim that live Gemini adds traffic benefit beyond fallback-only.

### Level 3: Fallback-only ablation and decision-level attribution

- What it supports: fallback-only traffic performance, exact row-level agreement with Gemini, and the conclusion that the deterministic fallback accounts for the observed 4V improvement.
- What it does not support: universal equivalence between Gemini and fallback, or general conclusions about all traffic states.

### Level 4: Offline high-discrimination diagnostic analysis

- What it supports: the specific claim that even selected mixed route-group states do not expose a Gemini-vs-fallback difference in the evaluated condition.
- What it does not support: global policy equivalence or a claim that no future discriminative scenario could ever separate the methods.

## 4. Abstract Replacement Draft

> This dissertation investigates whether a structured large language model (LLM)-assisted decision pipeline can support unsignalised intersection control in Simulation of Urban MObility (SUMO). The system separates prompt construction, live-provider request handling, parsing, deterministic validation, cooperative post-processing, safety verification, and trace logging so that each stage can be observed independently. The retained formal evidence comprises valid 4V runs from `formal_v2` and corrected 8V runs from `formal_v4`. Across that formal boundary, the LLM-assisted pipeline exhibits lower waiting time and higher mean speed than the selected rule-based baseline, but historical live-provider reliability is extremely poor and the formal result must therefore be interpreted at pipeline level rather than as pure LLM performance. Post-hoc diagnostic work then establishes a reliable Gemini 4V seed1 condition with complete provider and parser success, complete provenance, and no fallback usage. In that diagnostic condition, fallback-only behaviour achieves the same traffic outcome, and decision-level as well as high-discrimination analyses show complete Gemini-vs-fallback agreement on the evaluated states. The dissertation therefore contributes a reproducible and traceable comparison of controller architectures, together with a methodological analysis of how provider reliability, fallback handling, and prompt/fallback semantic overlap shape attribution in LLM-assisted control.

## 5. Chapter 1 Audit

### 5.1 Background and problem statement

Status: `KEEP`

The introduction already frames the problem correctly as a multi-stage control and attribution problem, not as a claim that an LLM alone solves intersection control.

### 5.2 Aim and objectives

Status: `KEEP_BUT_QUALIFY`

The aim is still appropriate because it targets an LLM-assisted decision pipeline under traceable constraints. The wording should remain careful, but it should not be read as a promise of independent LLM superiority. The objectives are still valid, especially the objectives about separation of stages, freezing the prompt, and measuring provider reliability.

### 5.3 Research questions

Status: `KEEP_BUT_QUALIFY`

RQ1 remains meaningful because the dissertation still tests the architecture against a rule-based baseline. The later attribution evidence does not invalidate the question; it simply changes the interpretation of the answer.

RQ2 and RQ3 remain meaningful even though the observed hybrid and safety effects are weak or absent. Negative results are acceptable in a dissertation if they are clearly reported.

RQ4 remains meaningful because the 4V-to-8V comparison still provides a bounded robustness observation.

### 5.4 Contributions

Status: `REWRITE`

The contribution list should continue to emphasise architecture, traceability, controlled comparison, and the explicit attribution framework. It should not imply that the LLM itself caused the traffic improvement. The best contribution framing is:

- modular architecture design,
- end-to-end traceability,
- controlled SUMO comparison,
- provider/reliability analysis,
- and identification of an experimental-identifiability limitation.

### 5.5 Research gap

Status: `KEEP_BUT_QUALIFY`

The existing gap claim is still valid, but the new evidence suggests one additional conceptual bridge: the dissertation is not only about whether LLM-assisted intersection control can be run, but also about how to attribute final behaviour when fallback and safeguard layers materially affect the output.

## 6. Chapter 2 Audit

### 6.1 Overall status

Status: `KEEP`

Chapter 2 is broadly adequate. It already supports the story about autonomous intersection management, grounded reasoning, LLM-assisted driving, and reliability/safety constraints.

### 6.2 Missing conceptual bridge

Status: `KEEP_BUT_QUALIFY`

The literature review is already sufficient to support the dissertation, but it would benefit from one short bridge sentence or paragraph on experimental identifiability in hybrid LLM pipelines. The bridge should explain that when a system includes deterministic fallback and safety layers, evaluation must distinguish model capability from pipeline behaviour.

### 6.3 Citation policy

Status: `KEEP`

No new citation appears necessary for the revised argument. The existing literature can support the general point that LLMs need grounding, traceability, and careful evaluation in safety-relevant settings.

## 7. Chapter 3 Audit

### 7.1 Overall status

Status: `KEEP_BUT_QUALIFY`

Chapter 3 correctly describes the modular pipeline, but it should be explicit enough about fallback semantics that the Chapter 6 attribution result is intelligible.

### 7.2 Fallback semantics

Status: `REWRITE`

The fallback section must not sound as if fallback merely means "set WAIT when the LLM fails." The code and diagnostic evidence show that fallback is meaningful traffic control. It should be described as using:

- time-to-intersection or nearest priority selection,
- route compatibility information,
- a constrained `PROCEED` / `WAIT` / `FREE` action set,
- and deterministic priority semantics.

This disclosure is important because it explains why fallback-only can outperform the selected rule-based baseline.

### 7.3 Prompt and validation pipeline

Status: `KEEP`

The existing description of prompt construction, parsing, validation, and safety handling is suitable.

### 7.4 Traceability

Status: `KEEP`

The traceability story is strong and should remain. It is one of the dissertation's genuine methodological strengths.

## 8. Chapter 4 Audit

### 8.1 Formal evidence boundary

Status: `KEEP`

The chapter already distinguishes the retained 24-run formal evidence from other batches. That separation must remain explicit.

### 8.2 Diagnostic analyses

Status: `INSERT AFTER CHAPTER 4 OR IN CHAPTER 6/7`

Do not retroactively merge the diagnostic evidence into the formal matrix. The academically cleaner solution is to keep Chapter 4 reserved for the retained formal experiment and place the post-hoc attribution method in Chapter 6 or Chapter 7.

### 8.3 Recommended placement

Status: `KEEP_THE_DIAGNOSTIC_METHODS_IN_CHAPTER_6_7`

The least disruptive approach is to leave Chapter 4 as the formal experimental design chapter and to integrate the post-hoc attribution methodology into the Discussion and Limitations chapters.

## 9. Chapter 5 Wording Audit

### 9.1 Traffic-performance language

Status: `KEEP_BUT_QUALIFY`

Where Chapter 5 says the LLM-assisted pipeline shows better traffic performance, that is acceptable at the pipeline level. It should not be rewritten into a pure LLM causation claim.

### 9.2 Attribution language

Status: `REWRITE`

Any sentence that implies the LLM itself improved traffic should be changed to "the LLM-assisted pipeline" or "the observed pipeline behaviour". This is especially important if Chapter 5 currently echoes the earlier, pre-attribution narrative.

### 9.3 Metric interpretation

Status: `KEEP`

The traffic metrics themselves are still valid. The change is in interpretation, not in the reported numbers.

## 10. Chapter 6-8 Integration Plan

### 10.1 Chapter 6

Status: `REPLACE_RELEVANT_SECTIONS`

Use the revised Chapter 6 text from `docs/research/dissertation_ch6_ch7_attribution_final_draft.md` as the replacement logic for:

- RQ1 discussion,
- the new attribution subsection,
- and the final synthesis paragraph.

The RQ1 section should keep the formal traffic advantage, but it must explicitly distinguish between pipeline-level benefit and independent Gemini contribution.

### 10.2 Chapter 7

Status: `REPLACE_RELEVANT_SECTIONS`

Use the revised Chapter 7 text from the same draft to add the identifiability limitation. This should sit alongside provider reliability rather than replacing it.

### 10.3 Chapter 8

Status: `REPLACE_TARGETED_PARAGRAPHS`

Replace the conclusion paragraphs that currently read as if the LLM-assisted architecture's benefit is primarily a model-level effect. The conclusion should preserve the positive engineering contribution while making the attribution limit explicit.

### 10.4 Duplication control

Status: `DELETE_DUPLICATED_PHRASES`

Do not repeat "provider reliability", "fallback dominance", and "no LLM-specific benefit" in three different chapters in nearly identical wording. Use the same claim boundary, but vary the role of each chapter:

- Chapter 6: interpretation,
- Chapter 7: limitation,
- Chapter 8: final boundary and future work.

## 11. Terminology Corrections

### Canonical terms

- Use `LLM-assisted pipeline` for the whole architecture.
- Use `Raw LLM` only when referring to the controller variant.
- Use `Hybrid` and `Hybrid + Safety` only as controller labels.
- Use `deterministic fallback` for the local fallback decision rule.
- Use `rule-based baseline` for the comparison controller in the formal experiment.
- Use `provider success` and `parser success` as separate reliability metrics.
- Use `operational waiting` when referring to the dissertation metric, and `waiting time` only when the surrounding prose clearly means the same metric.
- Use `safety override` and `postprocessor intervention` as explicit mechanism terms.

### Avoid

- Avoid casual use of `LLM controller` when the correct term is `LLM-assisted pipeline`.
- Avoid `pure LLM performance` except in negative statements.
- Avoid `equivalent` when the evidence only shows identical behaviour in the evaluated states.

## 12. Claim-by-Claim Revision Table

| Location | Current claim | Status | Revision guidance |
|---|---|---|---|
| Abstract | The LLM-assisted pipeline exhibits lower waiting time and higher mean speed than the rule-based baseline. | `KEEP_BUT_QUALIFY` | Keep the traffic finding, but add the post-hoc attribution result and state that the claim is pipeline-level, not independent Gemini causation. |
| Abstract | Provider reliability remains the main validity threat. | `KEEP_BUT_QUALIFY` | Retain, but add experimental identifiability and prompt/fallback semantic overlap. |
| Chapter 1 aim | Evaluate whether a structured LLM-assisted decision pipeline can improve cooperative decision-making. | `KEEP_BUT_QUALIFY` | Fine as an aim, but it should not be read as a result claim. |
| Chapter 1 contributions | The dissertation establishes a decision pipeline with LLM proposal, fallback, cooperative post-processing, and safety verification. | `KEEP` | This is a genuine contribution. |
| Chapter 1 research gap | Need for a frozen, traceable comparison of multiple architectures. | `KEEP` | Still valid. |
| Chapter 2 | Literature on embodied reasoning, autonomous driving, and reliability/safety. | `KEEP` | No major rewrite needed. |
| Chapter 3 | Validation normalizes invalid or missing actions to `WAIT`. | `KEEP` | Fine as a defensive interface description. |
| Chapter 3 fallback | Fallback handling is described vaguely. | `REWRITE` | Must disclose compatibility, priority, and `PROCEED` / `WAIT` / `FREE` semantics. |
| Chapter 4 | Formal evidence boundary between valid 4V and corrected 8V. | `KEEP` | Keep the boundary explicit. |
| Chapter 4 | Post-hoc diagnostics should be merged into the formal matrix. | `DELETE` | Do not merge them; keep them as attribution evidence. |
| Chapter 5 | LLM-assisted pipeline shows lower waiting time / higher speed. | `KEEP_BUT_QUALIFY` | Keep the numbers, but avoid implying pure model causation. |
| Chapter 5 | Hybrid effect is not visible. | `KEEP` | Supported by the current evidence. |
| Chapter 6 | The LLM-assisted pipeline improves traffic efficiency. | `KEEP_BUT_QUALIFY` | Add the new attribution paragraph and keep the result at pipeline level only. |
| Chapter 6 | Provider reliability remains a first-order validity threat. | `KEEP_BUT_QUALIFY` | Keep, but mention identifiability as a co-equal issue. |
| Chapter 6 | Live LLM contribution cannot be cleanly isolated. | `KEEP` | This is directly supported and should remain. |
| Chapter 7 | Safety layer present but insufficiently exercised. | `KEEP` | Supported. |
| Chapter 7 | Fallback-heavy execution. | `KEEP` | Supported, but explain fallback semantics more explicitly. |
| Chapter 7 | Lack of independent LLM contribution evidence. | `KEEP` | This is now a central limitation. |
| Chapter 8 | Pipeline can be implemented and evaluated systematically. | `KEEP` | Supported. |
| Chapter 8 | It can outperform a rule-based baseline. | `KEEP_BUT_QUALIFY` | Add that the attribution evidence assigns the improvement primarily to fallback in the examined 4V condition. |
| Chapter 8 | Final claim must stay at pipeline behaviour rather than pure LLM intelligence. | `KEEP_BUT_QUALIFY` | Strengthen with the explicit Gemini-vs-fallback finding. |
| Chapter 8 future work | Higher-density traffic, more seeds, local/self-hosted LLM, controlled fallback ablation. | `REWRITE` | Add experimental identifiability and discriminative-state design. |

## 13. Examiner Attack Test

### 1. If fallback produced the improvement, why call this LLM-assisted?

- Severity: `HIGH`
- Current dissertation defence: The architecture is LLM-assisted because the LLM is a real stage in a traceable pipeline, even though the measured traffic advantage is pipeline-level and not isolated to Gemini.
- Revision required: `YES`

### 2. Is the rule-based baseline artificially conservative?

- Severity: `HIGH`
- Current dissertation defence: Yes, the baseline is stricter and therefore not a semantic equivalent comparator for the fallback policy.
- Revision required: `YES`

### 3. Why are fallback and baseline different?

- Severity: `HIGH`
- Current dissertation defence: The fallback policy uses richer deterministic control semantics than the rule-based baseline, including priority and compatibility logic.
- Revision required: `YES`

### 4. Does the prompt encode the fallback policy?

- Severity: `HIGH`
- Current dissertation defence: Yes, substantially, which is why identifiability is limited.
- Revision required: `YES`

### 5. What independent contribution does the LLM make?

- Severity: `HIGH`
- Current dissertation defence: None demonstrated in the evaluated diagnostic condition.
- Revision required: `YES`

### 6. Why were Hybrid and Safety not exercised?

- Severity: `MEDIUM`
- Current dissertation defence: The evidence shows they were implemented but not sufficiently activated in the valid formal runs.
- Revision required: `NO`, but keep the wording cautious.

### 7. Are three seeds enough?

- Severity: `MEDIUM`
- Current dissertation defence: Enough for descriptive comparison, not for strong inference.
- Revision required: `NO`

### 8. Why only 4V and 8V?

- Severity: `MEDIUM`
- Current dissertation defence: They are the retained valid formal scales; no 16V formal evidence exists.
- Revision required: `NO`

### 9. Why use this waiting metric?

- Severity: `LOW`
- Current dissertation defence: Waiting time is a more discriminative metric than completion, which saturates at `100%`.
- Revision required: `NO`

### 10. Why trust the diagnostic evidence if it is post-hoc?

- Severity: `HIGH`
- Current dissertation defence: Because it is not substituted for the formal matrix; it is used to refine attribution and is supported by complete provenance, exact decision agreement, and an offline high-discrimination probe.
- Revision required: `YES`

## 14. Remaining High-Risk Issues

1. The abstract must be rewritten so it does not imply a model-level causal claim that the later diagnostics do not support.
2. Chapter 3 needs a more explicit fallback description, or the later fallback-dominant attribution will feel surprising rather than methodologically motivated.
3. Chapter 6 must integrate the attribution evidence rather than leaving it as an optional interpretation.
4. Chapter 7 must treat experimental identifiability as a core limitation, not a side note.
5. Chapter 8 must avoid repeating the same caution in multiple slightly different forms.

## 15. Exact Next Editing Sequence

1. Replace the abstract with the draft in Section 4 of this audit.
2. Update Chapter 1 contributions so they emphasise architecture, traceability, controlled comparison, and attribution.
3. Expand Chapter 3's fallback description so it is clear why fallback-only can outperform the selected baseline.
4. Replace the relevant Chapter 6 and Chapter 7 sections using `docs/research/dissertation_ch6_ch7_attribution_final_draft.md`.
5. Replace the targeted Chapter 8 paragraphs so the final conclusion matches the attribution boundary.
6. Run a terminology pass to ensure `pipeline`, `fallback`, `provider success`, and `LLM-assisted` are used consistently.
7. Perform one final read-through for claim drift between Abstract, Discussion, Limitations, and Conclusion.

## 16. Final Status

`MAJOR_CONSISTENCY_REVISION_REQUIRED`

## 17. Top 5 Dissertation Risks

1. The abstract still reads too much like a positive LLM-effect claim unless rewritten.
2. The dissertation could be attacked for lacking experimental identifiability if the prompt/fallback overlap is not stated clearly enough.
3. The fallback semantics may be under-described in Chapter 3 unless explicitly expanded.
4. Chapter 6 and Chapter 8 may still sound like they attribute the traffic gain to the LLM unless the new attribution paragraphs are integrated.
5. The future-work section could look generic if it does not prioritise discriminative states and causal ablation.
