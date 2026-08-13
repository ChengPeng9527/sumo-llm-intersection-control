# Formal Experiment Infrastructure Freeze

## Objective

Audit whether the repository is ready to execute the dissertation formal experiment matrix without changing the frozen method, prompt, controller semantics, or safety policy.

## Repository State

- Repository root: `D:\Sumo\sumo_train`
- Branch: `phase-18-decision-pipeline-separation`
- Frozen provider path: Groq / `https://api.groq.com/openai/v1` / `openai/gpt-oss-20b`
- Frozen request config: `max_completion_tokens = 256`, `reasoning_effort = low`, `timeout = 30.0`, `max_retries = 0`
- Canonical prompt: `P1_BASELINE`
- Decision space: `PROCEED / WAIT / FREE`
- Controllers: `rule_based`, `raw_llm`, `hybrid`, `hybrid_safety`

## What Was Verified

### Runtime and tests

- `pytest`: `69 passed`
- `py_compile`: passed on the formal matrix infrastructure files
- `scripts/run_formal_experiment_matrix.py --dry-run`: generated a 24-run plan successfully
- 8-vehicle live smoke: passed on the frozen Groq path with the canonical 256-token budget

### Formal matrix support

The repository now includes a dedicated formal matrix scheduler that provides:

- 4 controllers
- 2 vehicle counts: 4 and 8
- 3 seeds
- 24 planned runs total
- counterbalanced controller order across seeds
- seed-aware run IDs
- skip-completed resume behavior
- freeze provenance fields in the run manifest
- non-overwriting formal result copies under `results/formal_experiment/dissertation_formal_v1/`

### Infrastructure changes made

- The baseline controller now reads `SEED` and `EXPERIMENT_ID` from the environment.
- The raw, hybrid, and hybrid+safety controller wrappers now read `SEED` and `EXPERIMENT_ID` from the environment.
- A new formal matrix planner was added at `src/experiments/formal_experiment_matrix.py`.
- A new formal matrix runner was added at `scripts/run_formal_experiment_matrix.py`.
- Unit tests were added for the formal matrix plan.

## What Was Not Changed

- Prompt text and prompt contract
- Decision space
- Controller semantics
- Cooperative postprocessing logic
- Safety verification logic
- Live provider model selection
- Frozen request configuration

## Remaining Limitation

The formal matrix is now schedulable and resumable, and the 8-vehicle live smoke has already verified the frozen live path. The 24-run live SUMO sweep itself has not yet been executed in this session, so dissertation formal results are still pending.

## Evidence Paths

- `results/formal_experiment/dissertation_formal_v1/run_manifest.json`
- `results/formal_experiment/dissertation_formal_v1/dry_run_plan.json`
- `results/formal_experiment/dissertation_formal_v1/formal_experiment_summary.json`
- `src/experiments/formal_experiment_matrix.py`
- `scripts/run_formal_experiment_matrix.py`

## Verdict

**EXPERIMENT_INFRASTRUCTURE_READY_TO_FREEZE**

The repository now has the minimum execution-control layer needed for the 24-run formal experiment matrix, while keeping the dissertation method frozen.
