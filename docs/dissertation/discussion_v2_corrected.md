# Corrected Discussion v2

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

This discussion interprets the corrected evidence base:

- valid 4V evidence from `formal_v2`
- corrected 8V evidence from `formal_v4`

## 1. RQ1: Rule-based vs LLM-assisted architecture

### Observed result

The LLM-assisted pipeline exhibits lower waiting time and higher mean speed than the rule-based baseline in the corrected evidence.

- 4V rule-based: waiting `82.0` steps, speed `2.3098 m/s`
- 4V LLM-assisted: waiting `15.0` steps, speed `6.8026 m/s`
- 8V rule-based: waiting `242.0417` steps, speed `1.1895 m/s`
- 8V LLM-assisted: waiting `15.2917` steps, speed `6.5991 m/s`

### Interpretation

The evidence supports a cautious statement that the LLM-assisted pipeline improves traffic efficiency in the tested SUMO scenarios.

The safe dissertation wording is:

> The LLM-assisted pipeline exhibited lower waiting time and higher mean speed than the rule-based baseline in the tested SUMO scenarios.

### What not to claim

- Do not claim pure LLM superiority.
- Do not claim deployment readiness.
- Do not claim the result generalises to dense traffic or real roads.

The live provider path is fallback-heavy, so the observed traffic advantage belongs to the pipeline rather than to a model-only controller.

## 2. RQ2: Raw vs Hybrid

### Observed result

The corrected evidence does **not** show a clear traffic-performance advantage for hybrid over raw LLM.

The 4V and 8V valid cells are effectively similar on the traffic metrics, and the corrected evidence contains no visible postprocessor intervention.

### Interpretation

The cooperative stage is implemented, but the valid formal evidence does not show that it changes traffic outcomes in a measurable way. The correct reading is therefore:

> No clear traffic-performance advantage was observed for the hybrid architecture over the raw LLM architecture in the corrected formal evidence.

Provider reliability also does not show a stable hybrid advantage. The live-provider path remains weak and seed-sensitive.

## 3. RQ3: Safety layer behaviour

### Observed result

The corrected valid evidence shows:

- `0` collisions in every valid run,
- `0` safety overrides in every valid run,
- no visible safety-verifier intervention.

### Interpretation

The safety layer is present and traceable, but the evaluated scenarios did not sufficiently exercise it. Therefore the dissertation should not claim that safety improved safety.

A defensible formulation is:

> The safety layer was implemented and operationally present, but the formal evidence did not sufficiently exercise it.

## 4. RQ4: 4V to 8V scalability

### Observed result

The corrected evidence supports a dual-layer interpretation.

1. **Traffic-level behaviour**
   - Rule-based performance degrades substantially from 4V to 8V.
   - LLM-assisted traffic metrics remain comparatively stable over the evaluated 4V-to-8V range.

2. **Provider-level behaviour**
   - Live-provider reliability remains weak at both scales.
   - The corrected 8V evidence is especially fallback-heavy.

### Interpretation

The bounded dissertation claim should be:

> Within the evaluated low-density 4V and 8V SUMO scenarios, the LLM-assisted pipeline remained operational and showed comparatively stable traffic-level performance, while provider reliability remained a first-order limitation.

### What not to claim

- Do not claim the system scales well generally.
- Do not claim scalability to 16V or dense traffic.
- Do not generalise beyond the tested single-intersection environment.

## 5. Provider reliability as a validity threat

Provider reliability is the main interpretive limitation of the dissertation.

In the corrected evidence:

- provider success is low,
- `RateLimitError` dominates failures,
- fallback-heavy execution is the norm,
- successful provider calls are rare and seed-sensitive.

This means the dissertation’s traffic results should be read as the behaviour of a structured pipeline under constrained provider availability, not as a clean test of model intelligence alone.

## 6. What the study actually shows

The corrected dissertation supports the following bounded claims:

- a structured, traceable LLM-assisted control pipeline can be implemented in SUMO,
- the pipeline can be compared against a rule-based baseline in a frozen experimental design,
- the pipeline shows lower waiting time and higher mean speed than the rule-based baseline in the tested scenarios,
- traffic-level performance remains comparatively stable from 4V to 8V,
- provider reliability and fallback behaviour are first-order validity threats,
- the safety layer exists but was not strongly exercised,
- the cooperative postprocessor was not visibly exercised in the valid formal evidence.

## 7. What the study does not show

The corrected evidence does **not** prove:

- pure LLM superiority,
- general scalability to denser or larger scenarios,
- real-world validity,
- safety superiority,
- a visible effect from cooperative postprocessing,
- sufficient provider reliability for deployment.

## 8. Recommended dissertation wording

Use cautious formulations such as:

- “the LLM-assisted pipeline exhibited lower waiting time”
- “traffic-level performance remained comparatively stable over the evaluated 4V-to-8V range”
- “provider reliability remained weak and fallback-heavy”
- “the safety layer was implemented but not sufficiently exercised”

Avoid formulations such as:

- “the LLM beat traditional control”
- “the system scales well generally”
- “the safety layer improved safety”
- “the hybrid controller clearly improved traffic metrics”

## 9. Revised RQ summary

- **RQ1:** supported cautiously, at the pipeline level.
- **RQ2:** no clear traffic-performance advantage for hybrid over raw LLM.
- **RQ3:** safety layer present but insufficiently exercised.
- **RQ4:** traffic robustness is visible from 4V to 8V, but provider reliability remains a major limitation.

The near-identical 8V traffic results for Raw LLM, Hybrid, and Hybrid + Safety are best explained by the evidence showing fallback dominance, very low provider success, zero visible postprocessor intervention, and zero safety overrides. That does **not** mean the three architectures are intrinsically equivalent; it means the distinctive LLM/postprocessing/safety stages were rarely exercised in the corrected formal evidence.
