# Pilot Experiment Report

## Pilot Objective

Validate the full four-controller experiment chain after the parser compatibility fix.

This pilot is a readiness and execution check for:

- one fixed scenario
- one fixed seed
- four controllers
- one controlled execution path
- one consistent logging schema
- one live Groq provider path for the LLM-bearing controllers

It is not intended to be the final dissertation-scale comparative experiment.

## Frozen Configuration

The pilot configuration is frozen as follows:

- scenario density: low
- vehicle count: 4
- seed: 1
- route set: the existing four route ids
- SUMO version: the repository's configured SUMO installation
- Python: the repository's recovered runtime bundle
- LLM provider: Groq
- provider base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- decision interval: 1

## Controller Definitions

The pilot uses four controllers:

1. Rule-based
2. Raw LLM
3. Hybrid
4. Hybrid + Safety

The first controller is deterministic and does not send live LLM requests.
The other three controllers use the same live Groq provider settings.

## Canonical Revalidation Sequence

The current canonical evidence now includes a successful live parser compatibility revalidation:

- `request_count`: `3`
- `provider_request_success_count`: `3`
- `parser_success_count`: `3`
- `fallback_count`: `0`
- response shapes observed: `JSON`, `MARKDOWN_WRAPPED_JSON`

This revalidation supports the parser compatibility patch without changing prompt, model, decision space, fallback policy, controller semantics, or safety rules.

## Canonical Pilot Result

The canonical four-controller pilot completed successfully at:

`results/pilot/dissertation_pilot_v1/`

### Controller Outcomes

| Controller | Scheduled | Departed | Arrived | Completion rate | Collision count | Live requests | Successful requests | Failed requests | Parser success | Fallback |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rule-based | 4 | 4 | 4 | 100% | 0 | 0 | 0 | 0 | 0 | 0 |
| Raw LLM | 4 | 4 | 4 | 100% | 0 | 53 | 7 | 46 | 7 | 46 |
| Hybrid | 4 | 4 | 4 | 100% | 0 | 53 | 0 | 53 | 0 | 53 |
| Hybrid + Safety | 4 | 4 | 4 | 100% | 0 | 53 | 0 | 53 | 0 | 53 |

### Controller-Level Metrics

- Rule-based
  - mean waiting time: `125.00` steps
  - mean speed: `1.655047` m/s
  - decision source: deterministic interface rules only
- Raw LLM
  - mean waiting time: `11.00` steps
  - mean speed: `7.58386` m/s
  - provider: `Groq`
  - model: `openai/gpt-oss-20b`
- Hybrid
  - mean waiting time: `11.00` steps
  - mean speed: `7.58386` m/s
  - provider: `Groq`
  - model: `openai/gpt-oss-20b`
- Hybrid + Safety
  - mean waiting time: `11.00` steps
  - mean speed: `7.58386` m/s
  - provider: `Groq`
  - model: `openai/gpt-oss-20b`

### Pilot Integrity Checks

- decision-flow records are present
- schema consistency is preserved
- no owned residual SUMO processes remain
- TraCI cleanup succeeded
- logging artifacts were written for each controller

## Runtime

Measured pilot runtime from the latest canonical run:

- Rule-based controller runtime: `9.16` s
- Raw LLM controller runtime: `137.606` s
- Hybrid controller runtime: `29.843` s
- Hybrid + Safety controller runtime: `30.435` s

These are execution measurements, not evidence of comparative superiority.

## Interpretation

The pilot shows that:

- the canonical pilot runner now completes end-to-end
- the parser compatibility fix is compatible with real Groq responses
- the live LLM controllers still contain fallback-dominated regions in the pilot trace
- one-seed pilot evidence is sufficient for readiness validation but not for formal dissertation claims

The pilot does **not** support claims such as:

- Hybrid is better than Raw
- LLM is better than Rule
- Safety improves performance

Those require formal experiments.

## Superseded Evidence

An earlier fallback-dominated pilot record is now superseded by this canonical pilot revalidation.

Keep the superseded record only for provenance and failure analysis.

## Formal Readiness

The canonical pilot has completed successfully and the repository is now ready for formal experiment planning.

This does **not** mean formal experiment results are already available.

## Final Verdict

**CANONICAL_PILOT_PASSED_READY_FOR_FORMAL_EXPERIMENT**
