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

## Pilot Plan Status

- Pilot entry point: `scripts/run_dissertation_pilot.py`
- Pilot target: one fixed 4-vehicle, 1-seed, four-controller run
- Pilot output root: `results/pilot/dissertation_pilot_v1/`
- Current status: blocked because `GROQ_API_KEY` is missing in the active PowerShell session
- Pilot data exists: no
- Pilot evidence class: not yet available

## Data Boundary

When writing the dissertation:

- use `ENGINEERING_EVIDENCE_ONLY` entries to support implementation claims,
- use `PRELIMINARY_ONLY` entries only as supporting context,
- use `YES` entries for final experimental claims once formal sweeps are complete,
- exclude `NO` entries from results tables.
