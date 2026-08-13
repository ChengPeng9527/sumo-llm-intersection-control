# Canonical Prompt Final Revalidation v2

## Purpose

This report records the final prompt-selection revalidation after freezing the shared Groq request budget at `max_completion_tokens = 256`.

It is evidence for dissertation method freeze and supervisor communication. It does not change prompt semantics, controller semantics, safety logic, or decision space.

## Repository State

- Repository: `D:/Sumo/sumo_train`
- Branch: `phase-18-decision-pipeline-separation`
- HEAD: `3bd76ac0f252cfdf897eadde40dda6b2bd9532e4`
- Frozen request config:
  - provider = `Groq`
  - base_url = `https://api.groq.com/openai/v1`
  - model = `openai/gpt-oss-20b`
  - max_completion_tokens = `256`
  - reasoning_effort = `low`
  - timeout = `30.0`
  - max_retries = `0`

## Run Design

- Prompt candidates: `P1_BASELINE`, `P2_STRUCTURED`, `P3_COOPERATIVE_OBJECTIVE`
- Development seeds: `404`, `505`, `606`
- Prompt order by seed:
  - `404`: `P1_BASELINE -> P2_STRUCTURED -> P3_COOPERATIVE_OBJECTIVE`
  - `505`: `P2_STRUCTURED -> P3_COOPERATIVE_OBJECTIVE -> P1_BASELINE`
  - `606`: `P3_COOPERATIVE_OBJECTIVE -> P1_BASELINE -> P2_STRUCTURED`
- Vehicle count: `4`
- LLM mode: `real`
- Decision interval: `1`
- Planned runs: `9`
- Completed valid runs: `9`
- Technical retries: `0`

## Provider Precheck

- Provider request attempted: `yes`
- Provider request success: `yes`
- finish_reason: `stop`
- parser success: `yes`
- response content length: `39`
- latency: `869.35 ms`

## Prompt Comparison Summary

| Prompt | Run Count | Total Live Requests | Provider Success | Provider Success Rate | Parser Success Given Provider Success | Semantic Fallback Given Provider Success | Ambiguous Invalid Responses | Genuine WAIT | Mean Latency (ms) | Mean Response Length |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1_BASELINE | 3 | 165 | 51 | 30.91% | 0.00% | 0.00% | 51 | 51 | 368.30 | 24.09 |
| P2_STRUCTURED | 3 | 162 | 27 | 16.67% | 0.00% | 0.00% | 27 | 27 | 395.15 | 53.75 |
| P3_COOPERATIVE_OBJECTIVE | 3 | 166 | 21 | 12.65% | 0.00% | 0.00% | 21 | 21 | 339.07 | 20.01 |

## Evidence Observed

- `P1_BASELINE` had the highest provider success count and provider success rate in this batch.
- All three prompts preserved the same frozen decision contract and the same shared 256-token request configuration.
- All three prompts collapsed to a single genuine action (`WAIT`) in the valid provider-success rows, so semantic diversity did not distinguish the candidates in this batch.
- `P1_BASELINE` also had the shortest mean response length among the three candidates and a lower mean response length than `P2_STRUCTURED`.
- `P3_COOPERATIVE_OBJECTIVE` had the lowest mean latency, but not the strongest combined reliability profile.

## Selected Canonical Prompt

**Selected prompt: `P1_BASELINE`**

### Rationale

`P1_BASELINE` remained the best-supported option after conservative comparison across reliability, safety, efficiency, and simplicity metrics.

This selection is driven primarily by:

1. Highest provider success rate in the revalidation batch.
2. Stronger combined reliability profile than `P2_STRUCTURED` and `P3_COOPERATIVE_OBJECTIVE`.
3. Simpler and shorter prompt body than `P2_STRUCTURED`.
4. No evidence of a semantic advantage for the alternative prompts.

### Confidence

`Medium`

The confidence is medium rather than high because semantic action diversity was not strong and all prompts remained conservative / WAIT-dominant.

## Prompt Hashes

- `P1_BASELINE`: `EA435588BE1CAFC099D02685060CF00223852D8834CDFCF4DAFE66233C474ECD`
- `P2_STRUCTURED`: `09852507B087CAA59F88E4E67720F179F62A0F19356AE2898C880ADC3FF78EB2`
- `P3_COOPERATIVE_OBJECTIVE`: `B7C0873AAAEF80BC15F13F8F034BBB7A106FC89416969FDAFC4C66661B978989`

## Freeze Status

- Prompt changed: `No`
- Parser changed: `No`
- Method changed: `No`
- Controller semantics changed: `No`
- Request config changed: `No`

## Final Verdict

`CANONICAL_PROMPT_SELECTED_READY_TO_FREEZE`

## Evidence Paths

- `results/prompt_development/canonical_prompt_final_revalidation_v2/run_manifest.json`
- `results/prompt_development/canonical_prompt_final_revalidation_v2/provider_precheck.json`
- `results/prompt_development/canonical_prompt_final_revalidation_v2/run_level_results.csv`
- `results/prompt_development/canonical_prompt_final_revalidation_v2/prompt_comparison.csv`
- `results/prompt_development/canonical_prompt_final_revalidation_v2/request_trace.jsonl`
- `results/prompt_development/canonical_prompt_final_revalidation_v2/prompt_selection_summary.json`

## Interpretation

This batch closes the prompt-selection phase as an engineering freeze decision.

The evidence supports freezing `P1_BASELINE` as the canonical prompt for formal experiments under the frozen 256-token request budget.
