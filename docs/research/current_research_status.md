# Current Research Status

## Dissertation Goal

Evaluate whether an LLM-assisted hybrid decision framework can improve cooperative decision making at an unsignalized intersection while preserving deterministic safety.

## Current Method

The current method is a separated decision pipeline:

1. prompt builder
2. live or mock provider
3. response parser
4. validation
5. cooperative post-processing
6. deterministic safety verification
7. logging and trace output

## Frozen Research Position

- Research Design: frozen
- Method: frozen
- Decision space: `PROCEED / WAIT / FREE`
- Ambiguity policy: `MUST_FALLBACK`
- Canonical prompt: selected and frozen
- Model: unchanged
- Controller strategies: unchanged
- LLM request configuration: frozen at `max_completion_tokens = 256` for the canonical Groq path

## Formal Experiment Status

- Formal v2 execution freeze: created
- Formal v2 sweep: completed
- Formal v2 valid runs: `24 / 24`
- Formal v2 invalid technical runs: `0`
- Formal v2 missing runs: `0`
- Formal v2 duplicate runs: `0`
- Formal v2 controller coverage: `rule_based`, `raw_llm`, `hybrid`, `hybrid_safety`
- Formal v2 vehicle coverage: `4` and `8`
- Formal v2 seed coverage: `1`, `2`, `3`
- Formal v1 status: `INVALID_FORMAL_EXECUTION_TECHNICAL_FAILURE` and preserved as historical evidence
- Current dissertation-grade dataset: `results/formal_experiment/dissertation_formal_v2/`

## Completed Work

- Phase 18 decision pipeline separation is implemented.
- Raw, hybrid, and hybrid+safety controller paths exist.
- Structured prompt building is implemented.
- Response parsing is implemented.
- Cooperative post-processing is implemented.
- Safety verification is implemented.
- Unified logging and trace fields are implemented.
- Pipeline unit tests pass.
- Mock SUMO smoke validation passed.
- Minimal live Groq parser diagnostic completed successfully.
- Parser compatibility patch was live revalidated successfully.
- Canonical four-controller pilot revalidated successfully.
- Canonical prompt development and selection completed.
- Canonical prompt final revalidation v2 completed under the frozen 256-token request budget; `P1_BASELINE` remained selected.
- 8-vehicle live smoke completed successfully on the frozen Groq path.
- LLM request configuration specification updated for reproducibility freeze.
- Formal experiment matrix infrastructure is implemented with seed-aware run IDs, counterbalanced execution batches, and skip-completed resume behavior, plus freeze provenance fields in the run manifest.
- Fresh formal v2 execution completed after archiving stale pre-rerun evidence and re-running the full 24-run matrix under the new freeze commit and tag.

## Engineering Validation

The repository currently has:

- `pytest`: 74 passed
- SUMO smoke: passed
- live parser diagnostic: passed (`3/3` parser success, `0` fallback)
- canonical pilot: passed (`rule_based`, `raw_llm`, `hybrid`, `hybrid_safety`)
- canonical prompt final revalidation v2: passed (`P1_BASELINE` remained selected)
- formal v2 matrix: passed (`24 / 24 completed`, `0 missing`, `0 invalid technical runs`)

Current session note:

- recovered Python runtime: `C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
- recovered runtime version: `Python 3.12.13`
- the canonical `Python 3.10` interpreter path listed in the runbook was not executable in this session

This is engineering validation and pilot readiness evidence, not a dissertation-scale statistical experiment.

## Current Evidence

Current phase 18 evidence:

- smoke summary under `results/phase18_smoke/phase18_sumo_smoke/`
- live revalidation under `results/phase18_live_revalidation/`
- live parser diagnostic under `results/diagnostics/llm_parser_diagnostic/`
- canonical pilot under `results/pilot/dissertation_pilot_v1/`
- canonical prompt selection under `results/prompt_development/canonical_prompt_selection_v1/`
- canonical prompt final revalidation under `results/prompt_development/canonical_prompt_final_revalidation_v2/`
- request configuration specification under `docs/research/llm_request_configuration_specification.md`
- phase 18 report and metadata under `docs/phases/phase_18/`
- parser compatibility notes under `docs/research/llm_parser_compatibility_specification.md`
- parser patch and diagnostic reports under `docs/research/parser_compatibility_patch_report.md` and `docs/research/llm_parser_diagnostic_report.md`
- canonical prompt specification under `docs/research/canonical_prompt_specification.md`
- canonical prompt selection report under `docs/research/canonical_prompt_selection_report.md`
- canonical prompt final revalidation report under `docs/research/canonical_prompt_final_revalidation_v2_report.md`
- formal experiment v2 execution report under `docs/research/formal_experiment_v2_execution_report.md`
- formal experiment v2 outputs under `results/formal_experiment/dissertation_formal_v2/`
- pilot runner under `scripts/run_dissertation_pilot.py`

Historical evidence:

- phase 17 live LLM results
- historical 4V, 8V, and 16V run directories under `results/raw/`

## Formal Experiment Status

Formal experiments are now complete at the dissertation-provenance level.

The repository now has:

- frozen method and prompt assumptions
- a live parser compatibility revalidation
- a canonical pilot execution revalidation
- a selected canonical prompt frozen for formal experiment use
- a final prompt-selection revalidation under the frozen 256-token request budget
- an 8-vehicle live smoke passing on the frozen Groq path
- a formal experiment matrix scheduler with seed-aware run IDs, freeze provenance fields, and non-overwriting resume support
- a completed formal v2 sweep with 24 / 24 valid runs

The remaining work is dissertation analysis, narrative write-up, and result interpretation, not method redesign.

## Primary Research Risks

1. Overstating engineering validation or pilot readiness as formal evaluation.
2. Mixing historical live LLM evidence with current Phase 18 revalidation.
3. Using incomplete historical result directories as if they were dissertation-grade evidence.
4. Treating a single-seed pilot as proof of comparative superiority.
5. Treating safety and cooperation as performance improvements without reporting their trade-offs.

## Current Blockers

- Some historical result directories have metadata inconsistencies and should not be used directly as final evidence.
- The current live parser diagnostic is a minimal engineering check rather than a formal experiment sweep.
- No execution blocker is currently known for formal v2.
