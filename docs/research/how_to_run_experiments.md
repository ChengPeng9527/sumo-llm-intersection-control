# How to Run Experiments

## Environment

Use the explicit project interpreter:

```powershell
C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe
```

Use the project root:

```powershell
D:\Sumo\sumo_train
```

Use the SUMO installation:

```powershell
D:\Sumo
```

## 1. Unit Tests

```powershell
cd D:\Sumo\sumo_train
C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe -m pytest
```

Expected outcome:

- 30 collected tests
- 30 passed

## 2. Syntax Check

```powershell
cd D:\Sumo\sumo_train
C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe -m py_compile `
  src\common\config.py `
  src\controllers\decision_pipeline.py `
  src\controllers\decision_rules.py `
  src\controllers\raw_llm_controller.py `
  src\controllers\hybrid_llm_controller.py `
  src\controllers\hybrid_llm_safety_controller.py `
  src\llm\postprocessor.py `
  src\llm\response_parser.py `
  src\common\logging_schema.py `
  src\common\metrics.py
```

## 3. Mock SUMO Smoke Test

```powershell
cd D:\Sumo\sumo_train
C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe scripts\phase18_sumo_smoke.py
```

This validates the raw, hybrid, and hybrid+safety controller paths with the mock LLM mode.

## 4. Live LLM Revalidation

Prerequisite:

- `GROQ_API_KEY` must be present in the current PowerShell session.

The live revalidation should reuse the current prompt builder, parser, cooperative postprocessor, and safety layer. It should be treated as a single engineering validation request, not a full experiment sweep.

## 5. Pilot Experiment

Pilot entry point:

```powershell
cd D:\Sumo\sumo_train
C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe scripts\run_dissertation_pilot.py
```

Pilot requirements:

- `GROQ_API_KEY` must be present in the current PowerShell session.
- The pilot uses one fixed low-density 4-vehicle scenario.
- The pilot uses one fixed seed.
- The pilot runs four controllers once each.
- The pilot keeps the prompt, model, controller behavior, and decision interval frozen.

Current pilot status:

- blocked in this session because `GROQ_API_KEY` is missing

## 6. Result Aggregation

After a run, aggregate the CSV files under `results/raw/` and summarize them into tables or figures.

Suggested checks:

```powershell
cd D:\Sumo\sumo_train
Get-ChildItem results\raw -Directory
Get-ChildItem results\phase18_smoke\phase18_sumo_smoke
Get-ChildItem results\phase18_live_revalidation
Get-ChildItem results\pilot\dissertation_pilot_v1
```

## 7. Figure Generation

Use the stored `step_records.csv` files to build:

- completion rate comparisons,
- waiting-time comparisons,
- decision-flow charts,
- safety override counts,
- action-distribution plots.

## 8. Clean-Up

After a run:

- keep raw artifacts under `results/raw/`,
- keep smoke evidence under `results/phase18_smoke/`,
- keep live revalidation evidence under `results/phase18_live_revalidation/`,
- keep pilot evidence under `results/pilot/dissertation_pilot_v1/`,
- do not overwrite historical evidence without a clear reason.

## 9. Check Residual SUMO Processes

If a run fails or hangs, verify that no stray SUMO process remains before starting again.

## 9. Mock vs Live Distinction

- `mock` means the provider is replaced by a local fallback or stub.
- `live` means the request was actually sent to the configured provider.

Do not compare mock output as if it were live provider evidence.

## 10. Practical Testing Order

Recommended order:

1. `pytest`
2. smoke test
3. pilot
4. live revalidation
5. aggregation
6. figure generation

This order keeps the cheapest checks first and the most expensive check last.
