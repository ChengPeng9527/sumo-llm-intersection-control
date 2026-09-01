# Phase 3 Directional Service-Imbalance Execution Plan

## Scope

This plan implements the preregistration without changing network geometry,
formal prompt/parser, deterministic comparator, candidate legality, grant
semantics or safety logic. Output is isolated under:

`results/phase3_directional_service_imbalance/`

Every `run_id` contains condition, planner and seed. Existing evidence must
never be overwritten.

## Stage 1

Run locally from the repository root:

```powershell
& "C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe" scripts/run_phase3_directional_service_imbalance.py --stage deterministic-feasibility
```

The command generates three deterministic scenarios, executes one episode per
seed, copies canonical run artefacts, writes a derived observer per run, and
creates `stage1_feasibility_report.json`. It cannot enter the Gemini planner.

The observer records candidate sets, candidate sizes/waiting/approaches/
movements, target eligibility, deterministic/Gemini IDs where applicable,
agreement, non-service history, provider/parser/fallback fields, latency and
grant lifecycle. Episode metrics include all preregistered efficiency,
service-distribution and safety fields.

## Mandatory review boundary

After Stage 1, stop. Audit all three raw runs and the feasibility report. If
the gate fails, record `STOP_SUPPLEMENTARY_EXPERIMENTS`; do not alter demand or
run Gemini.

If the gate passes, Stage 2 still remains unauthorized until a new human
instruction is received. The runner enforces both the persisted passing report
and an explicit Stage 2 flag. No Stage 2 command is provided in this plan.

## Future Stage 2, if separately authorized

Stage 2 runs exactly three strict Gemini episodes for seeds 1--3, verifies
matched initial-demand signatures, retains invalid evidence without replacement,
and excludes invalid LLM episodes from the descriptive benefit classification.
No connectivity, retry, tuning or exploratory condition is added automatically.

## Stop rule

This is the final planned Q3 extension. Stage 1 failure stops it. A Stage 2
result, whether benefit, trade-off, deterministic advantage, no observed
benefit or inconclusive, also stops supplementary experiment creation.
