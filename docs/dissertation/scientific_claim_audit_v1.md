# Scientific Claim Audit v1

## Scope

This audit checks the most important dissertation claims for overstatement risk.

## Claim-by-claim audit

| Claim | Status | Recommended wording |
| --- | --- | --- |
| LLM-assisted methods improved traffic efficiency | READY, but must stay bounded | "In the tested low-density SUMO scenarios, the LLM-assisted pipeline exhibited lower waiting time and higher speed than the rule-based baseline." |
| LLMs generally outperform rule-based intersection control | WEAKEN / DO NOT USE | Unsupported by the current evidence. The formal v2 data only support the specific tested scenarios. |
| Zero collisions proves safety | WEAKEN / DO NOT USE | "The formal v2 runs were collision-free." That is an observation, not a proof of general safety. |
| Zero safety overrides means the safety layer is unnecessary | DO NOT USE | Zero overrides only mean the current dataset did not trigger the verifier. |
| 100% completion means all controllers are equivalent | DO NOT USE | Completion is saturated and therefore not discriminative in formal v2. |
| Fallback-heavy traces prove pure LLM performance | DO NOT USE | The opposite is true: fallback-heavy traces mean the result is pipeline-level, not pure LLM performance. |
| 4V/8V evidence proves broad scalability | WEAKEN / DO NOT USE | The dissertation can claim stability only within the tested low-density 4V and 8V scenarios. |
| Hybrid improves provider reliability relative to raw LLM at 8V | READY | Supported by the formal v2 trace counts. |
| Provider reliability is the main validity threat | READY | Supported by 2664 attempts, 109 successes, and 2555 failures. |
| The study demonstrates a functioning LLM-assisted decision pipeline | READY | Supported, but should be framed as pipeline behaviour rather than model-only capability. |
| The work validates real-world traffic performance | DO NOT USE | The evidence is simulation-only. |
| The safety layer had no effect because it was unnecessary | DO NOT USE | No overrides does not equal no effect in all possible scenarios. |

## Claims that were softened in the supervisor draft

- "better traffic efficiency" was kept, but only in the tested low-density scenario.
- "pure LLM superiority" was removed.
- "safe" was replaced with "collision-free" or "verified and available" where appropriate.
- "scalability" was restricted to the tested 4V / 8V range.
- Discussion and Conclusion were aligned so the same finding is not overstated in multiple places.

## Bottom line

The draft is scientifically conservative enough for supervisor review.
