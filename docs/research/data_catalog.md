# Data Catalog

## Classification Rules

- `YES`: suitable for dissertation tables or figures after normal aggregation.
- `PRELIMINARY_ONLY`: useful for engineering or smoke evidence, not yet formal dissertation evidence.
- `ENGINEERING_EVIDENCE_ONLY`: useful to prove the system works, but not enough for the final experimental claims by itself.
- `NO`: not suitable for dissertation evidence.

## Current Catalog

| Dataset/Result | Phase | Controller | Scenario | Vehicle Count | Seed | Mock/Live | Purpose | Metrics | Path | Dissertation Eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Phase 18 pipeline unit tests | 18 | N/A | N/A | N/A | N/A | N/A | code regression | pipeline trace fields, parser behavior, safety behavior | `tests/` | ENGINEERING_EVIDENCE_ONLY |
| Phase 18 SUMO smoke summary | 18 | raw / hybrid / hybrid+safety | low smoke scenario | 4 | 1 | mock | runtime validation | completion rate, throughput, waiting time, decision-source breakdown | `results/phase18_smoke/phase18_sumo_smoke/smoke_summary.json` | PRELIMINARY_ONLY |
| Phase 18 live revalidation | 18 | hybrid pipeline | minimal one-vehicle input | 1 | 1 | live | provider-path validation | provider connection, parser success, decision trace, logging success | `results/phase18_live_revalidation/live_summary.json` | ENGINEERING_EVIDENCE_ONLY |
| Phase 18 live parser diagnostic | 18 | raw LLM diagnostic | minimal one-vehicle input | 1 | 1 | live | parser compatibility diagnosis | provider request success, response format, parser success, parser failure reason | `results/diagnostics/llm_parser_diagnostic/live_summary.json` | ENGINEERING_EVIDENCE_ONLY |
| Canonical pilot after parser compatibility fix | 18 | rule_based / raw_llm / hybrid / hybrid_safety | low pilot scenario | 4 | 1 | live | execution readiness and pilot revalidation | completion rate, throughput, waiting time, speed, collision count, live request count, parser success, fallback count, safety override count | `results/pilot/dissertation_pilot_v1/pilot_summary.json` | ENGINEERING_EVIDENCE_ONLY |
| Canonical prompt development batch | 18 | raw LLM / P1 / P2 / P3 | prompt-development scenario | 4 | 101/202/303 | live | prompt selection | provider success rate, parser success rate, fallback rate, action distribution, completion rate, mean waiting time, mean latency | `results/prompt_development/canonical_prompt_selection_v1/` | ENGINEERING_EVIDENCE_ONLY |
| Canonical prompt final revalidation v2 | 18 | raw LLM / P1 / P2 / P3 | prompt-development scenario | 4 | 404/505/606 | live | canonical prompt freeze confirmation | provider success rate, parser success given provider success, fallback rate, action distribution, response length, completion tokens, finish_reason, latency | `results/prompt_development/canonical_prompt_final_revalidation_v2/` | ENGINEERING_EVIDENCE_ONLY |
| Frozen Groq request configuration | 18 | raw LLM / hybrid / hybrid+safety | live Groq request path | 4 | 1 | live | request reproducibility freeze | max_completion_tokens, reasoning_effort, timeout, max_retries | `docs/research/llm_request_configuration_specification.md` | ENGINEERING_EVIDENCE_ONLY |
| Formal experiment infrastructure freeze | 18 | rule_based / raw_llm / hybrid / hybrid_safety | formal matrix scheduler | 4 / 8 | 1 / 2 / 3 | dry-run | execution-control validation | planned run count, batch order, unique run IDs, resume support, non-overwrite copy path | `results/formal_experiment/dissertation_formal_v1/` | ENGINEERING_EVIDENCE_ONLY |
| Fresh formal v2 sweep | 18 | rule_based / raw_llm / hybrid / hybrid_safety | formal low 4V/8V | 4 / 8 | 1 / 2 / 3 | live | dissertation formal results | completion rate, throughput, waiting time, speed, episode duration, collision count, live request count, parser success, fallback count, finish_reason, truncation, latency, postprocessor intervention, safety override | `results/formal_experiment/dissertation_formal_v2/` | YES |
| Eight-vehicle live smoke | 18 | raw_llm | formal low v8 seed1 | 8 | 1 | live | end-to-end execution smoke | provider success, parser success, finish_reason, completion_tokens, reasoning_tokens, completion rate, TraCI cleanup | `results/diagnostics/eight_vehicle_live_smoke_v1/` and `results/raw/SMOKE_8V_RAW_V2_v8_seed1_real/` | ENGINEERING_EVIDENCE_ONLY |
| Historical baseline 4V run | historical | baseline | debug four-vehicle | 4 | 1 | mock | baseline reference | completion, arrival, collisions | `results/raw/E01_BASELINE_4V_S1_seed1` | PRELIMINARY_ONLY |
| Historical cooperative 4V run | historical | cooperative | debug four-vehicle | 4 | 1 | mock | cooperative reference | completion, arrival, collisions | `results/raw/E02_COOPERATIVE_4V_S1_seed1` | PRELIMINARY_ONLY |
| Historical mock LLM 4V run | historical | raw LLM / mock | low 4V | 4 | 1 | mock | LLM engineering reference | completion, arrival, collisions | `results/raw/E03_LLM_MOCK_4V_S1_seed1` | ENGINEERING_EVIDENCE_ONLY |
| Historical mock LLM 8V run | historical | raw LLM / mock | low 8V | 8 | 1 | mock | LLM engineering reference | completion, arrival, collisions | `results/raw/E03_LLM_4V_S1_v8_seed1_mock` | PRELIMINARY_ONLY |
| Historical live LLM 8V run | historical | raw LLM / real | low 8V | 8 | 1 | live | historical live provider evidence | completion, arrival, collisions | `results/raw/E03_LLM_4V_S1_v8_seed1_real` | ENGINEERING_EVIDENCE_ONLY |
| Historical live LLM 16V run | historical | raw LLM / real | low 16V | 16 | 1 | live | historical live provider evidence | completion, arrival, collisions | `results/raw/E03_LLM_4V_S1_v16_seed1_real` | ENGINEERING_EVIDENCE_ONLY |
| Historical baseline 8V run with incomplete completion | historical | baseline | low 8V | 8 | 1 | mock | deprecated reference | arrival inconsistency, completion shortfall | `results/raw/E01_BASELINE_4V_S1_v8_seed1` | NO |
| Historical cooperative 16V run with metadata inconsistency | historical | cooperative | low 16V | 16 | 1 | mock | deprecated reference | departed/arrived mismatch in metadata | `results/raw/E02_COOPERATIVE_4V_S1_v16_seed1` | NO |

## Notes on Eligibility

- The historical live LLM runs are evidence that live provider calls were previously possible, but they are not the same as the current Phase 18 live revalidation.
- The Phase 18 smoke result is useful for engineering and pipeline checks, but it should not be presented as a formal experiment.
- The Phase 18 live revalidation is evidence of end-to-end execution, not a full statistical comparison.
- The Phase 18 live parser diagnostic is evidence of a parser compatibility gap on top-level JSON list responses, but it is still an engineering diagnostic rather than a formal experiment.
- The canonical pilot after the parser compatibility fix is execution-readiness evidence, not a formal dissertation sweep.
- The older fallback-dominated pilot record is superseded by the latest canonical pilot run and should be kept only for provenance.
- The canonical prompt development batch and final revalidation batches are engineering evidence for prompt selection, not a formal experiment.
- The fresh formal v2 sweep is the dissertation-grade experimental dataset and should be used for results tables after aggregation.

## Pilot Plan Status

- Pilot entry point: `scripts/run_dissertation_pilot.py`
- Pilot target: one fixed 4-vehicle, 1-seed, four-controller run
- Pilot output root: `results/pilot/dissertation_pilot_v1/`
- Current status: completed successfully after parser compatibility revalidation
- Current session runtime note: recovered bundle at `C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe` (`Python 3.12.13`)
- Canonical `Python 3.10` interpreter path from the runbook was not executable in this session
- Pilot data exists: yes
- Pilot evidence class: engineering evidence only

## Prompt Development Status

- Prompt development batches: completed
- Canonical prompt: selected and frozen
- Prompt-selection evidence class: engineering evidence only

## Data Boundary

When writing the dissertation:

- use `ENGINEERING_EVIDENCE_ONLY` entries to support implementation claims,
- use `PRELIMINARY_ONLY` entries only as supporting context,
- use `YES` entries for final experimental claims,
- exclude `NO` entries from results tables.
