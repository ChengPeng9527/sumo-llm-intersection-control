# Canonical Prompt Revalidation Report

## 1. Repository Provenance

- Canonical repository: `D:\Sumo\sumo_train`
- Recovery source: `D:\Sumo1\sumo_train`
- Canonical branch: `phase-18-decision-pipeline-separation`
- Canonical HEAD: `3bd76ac0f252cfdf897eadde40dda6b2bd9532e4`

`D:\Sumo\sumo_train` is the only repository with valid Git history and phase provenance. `D:\Sumo1\sumo_train` is a recovery source and does not have usable commit history in this session.

## 2. Original Development Evidence

Prompt development evidence exists under:

- `results/prompt_development/canonical_prompt_selection_v1/`

Candidate prompts:

- `P1_BASELINE`
- `P2_STRUCTURED`
- `P3_COOPERATIVE_OBJECTIVE`

Development batch evidence:

- development seeds: `101`, `202`, `303`
- vehicle count: `4`
- planned runs: `9`
- completed valid runs: `9`

Prompt texts are stored in:

- `results/prompt_development/canonical_prompt_selection_v1/prompt_candidates/P1_BASELINE.txt`
- `results/prompt_development/canonical_prompt_selection_v1/prompt_candidates/P2_STRUCTURED.txt`
- `results/prompt_development/canonical_prompt_selection_v1/prompt_candidates/P3_COOPERATIVE_OBJECTIVE.txt`

## 3. Counterbalance Audit

The raw execution timestamps show counterbalanced order across seeds:

- Seed `101`: `P1 -> P2 -> P3`
- Seed `202`: `P2 -> P3 -> P1`
- Seed `303`: `P3 -> P1 -> P2`

Therefore:

- `COUNTERBALANCE_VALID = true`

## 4. Provider / Prompt Failure Separation

The summary report shows:

- `P1_BASELINE`: `198` live requests, `2` successful requests, `196` failed requests
- `P2_STRUCTURED`: `198` live requests, `0` successful requests, `198` failed requests
- `P3_COOPERATIVE_OBJECTIVE`: `198` live requests, `0` successful requests, `198` failed requests

However, inspection of the underlying `step_records.csv` files shows that the only `LLM_RAW` rows in `P1_BASELINE` came from `seed101` and had empty provider fields (`provider_request_attempted = False`, `provider_request_success = False`, `provider_name = ""`). This means the prompt-development evidence does **not** cleanly separate provider reliability from prompt quality.

Conclusion:

- `P1` has the best observed live behavior in the summary report.
- The evidence is still sparse and partially confounded by provider / runtime behaviour.
- Provider success cannot be attributed to prompt quality with high confidence.

## 5. Static Prompt Quality Comparison

### P1_BASELINE

- Strongest parser-contract compatibility
- Lowest token burden
- Lowest instruction complexity
- Lowest risk of instruction leakage
- Minimal ambiguity
- Good fit for frozen contract stability

### P2_STRUCTURED

- More explicit state organization
- Higher token burden than P1
- More instruction surface area
- Slightly higher risk of prompt drift / unnecessary complexity
- No disallowed leakage detected in the development report

### P3_COOPERATIVE_OBJECTIVE

- Similar to P2 but with an extra cooperative-objective sentence
- Slightly higher bias risk toward progress language
- Highest wording complexity among the three candidates
- No disallowed leakage detected in the development report

Static conclusion:

- `P1_BASELINE` is still the simplest and most contract-stable prompt.
- Static analysis alone does not prove superiority, but it supports freezing P1 if a freeze must be made.

## 6. Minimal Revalidation

Minimal revalidation was considered necessary because the prompt-development evidence does not fully disentangle provider availability from prompt quality.

In this session, minimal live revalidation could not be executed because no provider credential was available in the current shell environment.

Therefore:

- `MINIMAL_REVALIDATION_REQUIRED = true`
- `MINIMAL_REVALIDATION_RUNS = not executed in this session`

## 7. Selection Rationale

Current evidence supports `P1_BASELINE` as the most defensible canonical prompt candidate because:

1. It is the only prompt with any positive live-provider/parser signal in the development summary.
2. It has the simplest and most stable instruction contract.
3. It avoids extra wording that could increase ambiguity or token burden.
4. Counterbalance across seeds is valid, so order alone does not explain the observed P1 result.

But the evidence is not strong enough to claim a fully de-confounded provider-level validation.

## 8. Threats to Validity

1. Provider/runtime evidence is sparse.
2. The positive P1 signal is very small relative to the total number of requests.
3. Underlying step-record inspection shows empty provider fields for the only `LLM_RAW` rows in P1.
4. The development batch is engineering evidence, not the formal experiment.
5. No minimal live revalidation could be run in this session due missing credentials.

## 9. Canonical Prompt Decision

Current recommendation:

- `P1_BASELINE` remains the best candidate for canonical freeze.
- But the revalidation is not fully closed because provider confounding is still unresolved.

## 10. Freeze Status

- `READY_TO_COMMIT_PROMPT_FREEZE`
- `PROMPT_FROZEN_IN_GIT = false`
- The repository is still dirty and no Git commit has been created for the freeze in this session.

## 11. Final Verdict

`CANONICAL_PROMPT_REVALIDATION_INCONCLUSIVE`

## Post-Hoc Live Provider Gate Audit

The canonical prompt revalidation batch is no longer considered valid prompt-quality comparison evidence.

Observed contradiction:

- provider probe succeeded
- controller batch recorded `0/330` provider attempts
- controller rows fell back to the deterministic interface rule
- therefore the batch did not exercise the live provider path for the controller runs

Evidence impact:

- `P1_BASELINE` remains provisional canonical prompt
- do not freeze the prompt based on the invalid revalidation batch
- the live provider gate requires separate diagnostics before prompt comparison can be trusted again
