# Formal Experiment V2 Execution Report

## Scope

This report records the fresh `dissertation_formal_v2` formal matrix execution after the execution freeze was refreshed and the stale pre-rerun evidence was archived.

## Freeze Provenance

- Repository: `D:\Sumo\sumo_train`
- Branch: `phase-18-decision-pipeline-separation`
- Freeze commit: `7b363fa8add58ac83775eb26dd6ff0b68bea022e`
- Freeze tag: `v0.9.1-formal-experiment-freeze`
- Canonical prompt: `P1_BASELINE`
- Prompt hash: `EA435588BE1CAFC099D02685060CF00223852D8834CDFCF4DAFE66233C474ECD`
- Provider: `Groq`
- Base URL: `https://api.groq.com/openai/v1`
- Model: `openai/gpt-oss-20b`
- Request config: `max_completion_tokens=256`, `reasoning_effort=low`, `timeout=30.0`, `max_retries=0`

## Audit Summary

- Planned runs: `24`
- Completed runs: `24`
- Skipped completed runs: `0`
- Missing runs: `0`
- Duplicate runs: `0`
- Technical reruns: `0`
- Valid runs: `24`
- Invalid technical runs: `0`

## Matrix Coverage

- Controllers: `rule_based`, `raw_llm`, `hybrid`, `hybrid_safety`
- Vehicle scales: `4`, `8`
- Seeds: `1`, `2`, `3`
- Coverage: all controller x scale x seed combinations are present

## Controller-Level Summary

| Controller | Scale | Runs | Completion | Provider Attempts | Provider Successes | Parser Successes | Fallbacks | Finish Reason | Truncations | Mean Latency (ms) | Collisions |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Rule-based | 4 | 3 | 100% | 0 | 0 | 0 | 0 | N/A | 0 | N/A | 0 |
| Rule-based | 8 | 3 | 100% | 0 | 0 | 0 | 0 | N/A | 0 | N/A | 0 |
| Raw LLM | 4 | 3 | 100% | 444 | 26 | 26 | 418 | stop | 0 | 456.37 | 0 |
| Raw LLM | 8 | 3 | 100% | 444 | 3 | 3 | 441 | stop | 0 | 766.23 | 0 |
| Hybrid | 4 | 3 | 100% | 444 | 22 | 22 | 422 | stop | 0 | 451.61 | 0 |
| Hybrid | 8 | 3 | 100% | 444 | 18 | 18 | 426 | stop | 0 | 447.77 | 0 |
| Hybrid + Safety | 4 | 3 | 100% | 444 | 22 | 22 | 422 | stop | 0 | 356.22 | 0 |
| Hybrid + Safety | 8 | 3 | 100% | 444 | 18 | 18 | 426 | stop | 0 | 342.59 | 0 |

## Aggregate Provider Evidence

- Total provider attempts: `2664`
- Total provider successes: `109`
- Total provider failures: `2555`
- Total parser successes: `109`
- Total fallbacks: `2555`
- Finish reason distribution: `stop=109`
- Truncations: `0`
- Mean latency: `423.52 ms`
- Median latency: `389.13 ms`

## Traffic Summary

- All 24 runs completed successfully.
- All runs reached `departed = arrived`.
- Completion rate: `100%` for every run.
- Collision count: `0` across all runs.

## Lifecycle Summary

- TraCI cleanup: passed
- Residual owned SUMO processes after validation: `[]`
- Fresh formal matrix finished without hanging shutdowns

## Interpretation

- The formal v2 sweep is ready for dissertation aggregation.
- Rule-based runs remain the slowest baseline in this low-density setup.
- LLM-assisted controllers preserve completion and collision-free operation.
- Raw LLM shows weaker provider reliability at 8 vehicles than hybrid and hybrid+safety.
- Hybrid and hybrid+safety have similar traffic outcomes in this sweep, with no safety override events recorded.

## Evidence Locations

- Manifest: `results/formal_experiment/dissertation_formal_v2/run_manifest.json`
- Summary: `results/formal_experiment/dissertation_formal_v2/formal_experiment_summary.json`
- Formal run outputs: `results/formal_experiment/dissertation_formal_v2/runs/`
- Archived pre-rerun evidence: `results/archive/formal_v2_superseded_20260813/`
