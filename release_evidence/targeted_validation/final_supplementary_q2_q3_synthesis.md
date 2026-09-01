# Final Supplementary Q2/Q3 Synthesis

## Evidence boundary

This synthesis combines retained formal Phase 2 and preregistered
supplementary evidence. It does not change any raw record or frozen result and
does not make population-level or internal-reasoning claims.

## Evidence chain

| Evidence component | Retained result | Interpretation |
|---|---|---|
| Formal Phase 2 | 93 strict-valid Gemini decisions: 89 agreements and 4 legal disagreements | Distinct Gemini choices exist but are uncommon in the original matrix. |
| Phase 3A decision audit | Three S3-12V disagreements share R4 rank 1 versus S2 rank 3; the fourth disagreement is structurally different | Candidate richness, group-size competition, waiting spread, and turn diversity are descriptive correlates, not established causes. |
| Aggregate-waiting repeatability | W08 selected R4 5/5; W19/W20/W24 selected S2 15/15 | Aggregate waiting is repeatably associated with selection distribution in this fixed state; no internal threshold is identified. |
| Individual waiting distribution | `NO_OBSERVED_DISTRIBUTION_EFFECT` | With aggregate waiting fixed, the registered endpoint comparison did not show an ordered distribution effect. |
| Matched turn composition | `NO_OBSERVED_TURN_COMPOSITION_EFFECT` | Neither registered target was selected because another legal competitor dominated; movement label alone was not isolated. |
| Group size x waiting | Valid LOW selections were another legal pair and valid HIGH selections were S2; no larger target was selected | A LOW/HIGH change recurred across two confounded contexts, but no registered group-size effect or interaction was established. |
| Same-state counterfactual | `R4_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES` in 3/3 historical checkpoints | The single observed S2 action was locally more costly than R4 under a shared deterministic continuation. |
| Directional full-policy stress | 3/3 strict-valid matched pairs; `EFFICIENCY_ONLY_BENEFIT` | Gemini served S2 18 s earlier and consistently reduced total/mean waiting and duration, while approach-level imbalance worsened. |

## Final Q2 answer

**Under what conditions does Gemini exhibit distinct candidate-selection
behaviour?**

Gemini's distinct behaviour is observed in bounded, decision-discriminative
states containing multiple legal compatible groups with competing group size
and waiting characteristics. In the retained S3 structure, the deterministic
comparator chooses a larger all-RIGHT group, whereas Gemini can choose a
smaller opposite-STRAIGHT pair with greater accumulated waiting. Fixed-state
repeatability shows a stable association between aggregate-waiting
manipulation and this selection distribution: R4 was selected in 5/5 W08
requests and S2 in 15/15 W19/W20/W24 requests. The evidence does not establish
an internal waiting threshold, a group-size utility, a turn preference,
fairness reasoning, or a universal decision rule. Individual waiting
distribution and matched turn-composition probes did not satisfy their
registered effect criteria, and the group-size probe did not isolate a causal
group-size response.

## Final Q3 answer

**When does distinct behaviour produce system-level benefit or cost?**

The system consequence depends on the intervention and operating context. In
three historical same-state single-action interventions, forcing S2 instead of
R4 increased total and mean waiting under the same subsequent deterministic
policy; this is bounded evidence of a local cost. In the preregistered dynamic
16-vehicle directional stress, the complete strict-valid Gemini policy served
S2 18 s earlier in all three seeds and reduced total waiting by 9--10 s, mean
waiting by 0.5625--0.6250 s, and duration by 3--5 s. This met the frozen
`EFFICIENCY_ONLY_BENEFIT` rule. It did not meet the service-distribution rule:
maximum and P95 waiting decreased, while maximum approach mean and approach
range increased. Thus the retained evidence supports conditional, bounded
full-policy efficiency value in the tested stress, alongside local
counterfactual cost and mixed distributional effects. It does not support
general planner superiority, fairness optimisation, or universal LLM use.

## Claim boundary

### Supported

- Gemini produced genuine, legal, provider-backed choices distinct from the
  deterministic comparator.
- Aggregate-waiting manipulation was repeatably associated with Gemini's
  fixed-state selection distribution in the tested template.
- The complete Gemini policy produced a preregistered efficiency-only benefit
  in three matched directional-stress seeds.
- The historical single S2 intervention was locally worse than R4 on the
  preregistered primary outcomes in three same-state branches.

### Partially supported

- Service-distribution improvement: vehicle-level maximum, P95, and waiting SD
  improved in the directional stress, but approach-level mean imbalance and
  range worsened.

### Not supported

- A fixed internal waiting threshold.
- A causal group-size or turn-composition rule.
- Fairness optimisation or human-like reasoning.
- General Gemini or deterministic superiority.
- Statistical significance, broad scalability, deployment readiness, or
  real-world safety.

### Still unknown

- Whether the same full-policy effect replicates across other demand patterns,
  topologies, models, or larger samples.
- Which internal model features produce the observed legal selection pattern.
- Whether the efficiency/distribution balance persists beyond the registered
  three-seed stress condition.

## Final research stop

The completed evidence addresses the bounded supplementary Q2 and Q3 questions
without warranting result-driven scenario search. The frozen stop decision is:

**`STOP_ALL_SUPPLEMENTARY_EXPERIMENTS`**
