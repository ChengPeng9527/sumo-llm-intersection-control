# Formal V4 Dissertation Impact Audit

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

## Why this audit exists
`formal_v2` contains a valid 4-vehicle evidence set and an invalid 8-vehicle evidence set. `formal_v4` is the corrected 8-vehicle evidence set. The dissertation must therefore be revised so that its claims use the corrected evidence boundary.

## What changes in the dissertation interpretation
1. **Replace invalid 8V formal-v2 evidence with formal-v4 evidence.**
   - Do not cite `formal_v2` 8V runs as evidence of 8-vehicle behavior.
   - Use `formal_v4` for all 8-vehicle result claims.

2. **Keep the 4V evidence from formal_v2.**
   - The 4-vehicle half of `formal_v2` remains valid and can still support the low-density 4V discussion.

3. **Do not overstate pure LLM performance.**
   - The live LLM-bearing runs are heavily fallback mediated.
   - Provider failures are mostly `RateLimitError`, and only a small subset of steps produced successful live responses.
   - The traffic outcomes are therefore pipeline-level outcomes, not model-only outcomes.

4. **Reframe RQ1/RQ4 more carefully.**
   - The corrected evidence supports that the LLM-assisted architecture *under the frozen pipeline* exhibits lower waiting time and higher mean speed than the rule-based baseline in the tested scenarios.
   - It does **not** prove universal superiority or deployment readiness for dense traffic or real roads.

5. **Keep RQ2/RQ3 claims modest.**
   - The cooperative postprocessor does not show a visible effect in the valid corrected evidence.
   - Safety overrides were not observed, so safety-related conclusions must be framed as absence of observed intervention rather than proof of safety equivalence.

## What does not change
- Prompt specification.
- Parser contract.
- Model choice.
- Request configuration.
- Controller semantics.
- Cooperative logic.
- Safety logic.
- Research method.

## Dissertation sections that need update
- Results: replace any use of invalid `formal_v2` 8V numbers with `formal_v4`.
- Discussion: explicitly separate pipeline-level performance from provider availability and fallback behavior.
- Limitations: make the provider reliability threat and the corrected evidence boundary explicit.
- Conclusion/Future work: keep the conclusion bounded by the corrected evidence.

## Current impact summary
- The dissertation remains defensible.
- The corrected 8V evidence strengthens the empirical base.
- The main interpretation risk is still provider reliability, not the traffic scenario itself.


