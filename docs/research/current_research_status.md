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

## Engineering Validation

The repository currently has:

- `pytest`: 67 passed
- SUMO smoke: passed
- live parser diagnostic: passed (`3/3` parser success, `0` fallback)
- canonical pilot: passed (`rule_based`, `raw_llm`, `hybrid`, `hybrid_safety`)
- canonical prompt final revalidation v2: passed (`P1_BASELINE` remained selected)

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
- pilot runner under `scripts/run_dissertation_pilot.py`

Historical evidence:

- phase 17 live LLM results
- historical 4V, 8V, and 16V run directories under `results/raw/`

## Formal Experiment Status

Formal experiments are not yet complete.

The repository now has:

- frozen method and prompt assumptions
- a live parser compatibility revalidation
- a canonical pilot execution revalidation
- a selected canonical prompt frozen for formal experiment use
- a final prompt-selection revalidation under the frozen 256-token request budget
- an 8-vehicle live smoke passing on the frozen Groq path
- a formal experiment matrix scheduler with seed-aware run IDs, freeze provenance fields, and non-overwriting resume support

The remaining work is formal experimental sweeps and dissertation-grade analysis, not method redesign.

## Primary Research Risks

1. Overstating engineering validation or pilot readiness as formal evaluation.
2. Mixing historical live LLM evidence with current Phase 18 revalidation.
3. Using incomplete historical result directories as if they were dissertation-grade evidence.
4. Treating a single-seed pilot as proof of comparative superiority.
5. Treating safety and cooperation as performance improvements without reporting their trade-offs.

## Current Blockers

- Formal experiment sweep is still pending.
- Some historical result directories have metadata inconsistencies and should not be used directly as final evidence.
- The current live parser diagnostic is a minimal engineering check rather than a formal experiment sweep.
- The canonical pilot is a readiness check, not the final comparative study.
- The canonical prompt is now frozen and should be used for all LLM-bearing formal experiment runs.
- The canonical request configuration is now frozen and should be used for all LLM-bearing formal experiment runs.
- The canonical prompt revalidation batch is engineering evidence for freeze confirmation, not a formal experiment.

## Next Unique Task

Prepare the formal experiment matrix and dissertation reporting plan using the frozen method and the validated canonical pilot evidence.

## Gate Audit Note

An offline controller live-provider gate audit has been added at:

- `docs/research/controller_live_provider_gate_audit.md`

Current interpretation:

- provider probe is valid
- controller live-provider gate still needs explicit revalidation
- prompt comparison should not be resumed until the gate diagnostics are verified

## Status Statement

Research design is frozen; engineering validation is complete; the parser compatibility patch has been live revalidated; the canonical pilot has been revalidated and completed successfully; the canonical prompt has been revalidated and frozen under the 256-token request budget; the 8-vehicle live smoke has passed; the formal experiment matrix infrastructure is now frozen; formal experimental evaluation is still pending.
The canonical prompt has now been selected and frozen after the prompt-development batch and the final revalidation batch.
