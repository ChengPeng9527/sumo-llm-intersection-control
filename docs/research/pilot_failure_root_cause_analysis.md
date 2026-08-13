# Pilot Failure Root Cause Analysis

## Status Note

This file preserves the earlier hybrid-safety failure analysis for provenance.

It is superseded by the later canonical pilot revalidation after the parser compatibility fix.

## Current Session Note

The previous `hybrid_safety` failure remains the current canonical pilot failure evidence.
In the present session, a bundled Python runtime was recovered and canonical `pytest`
passed again, but the live pilot still cannot be re-run because `GROQ_API_KEY` is
missing from the active PowerShell session.

## 1. Executive Summary

The pilot reached three successful controllers and then failed on `hybrid_safety` with `exit status 120`.

The strongest evidence points to a **pilot execution / SUMO lifecycle problem** rather than a method, prompt, or safety-logic change. However, the exact origin of `120` is not fully proved from repository evidence alone, because no stdout/stderr traceback was captured for the failing controller and the runner does not log that stream.

Current judgment:

- primary root-cause category: `SUMO_PROCESS_LIFECYCLE_FAILURE`
- secondary issue: `TRACI_CONNECTION_CLEANUP_FAILURE`
- exact low-level source of `120`: `INSUFFICIENT_EVIDENCE`
- method change required: **No**

## 2. Failure Context

Observed pilot status:

- `rule_based`: completed
- `raw_llm`: completed
- `hybrid`: completed
- `hybrid_safety`: failed

Repository evidence at the time of inspection:

- current branch: `phase-18-decision-pipeline-separation`
- working tree: one modified file, `scripts/run_dissertation_pilot.py`
- pilot artifacts existed for `rule_based`, `raw_llm`, and `hybrid`
- no `hybrid_safety` artifact directory was present
- `pilot_failures.json` recorded:
  - controller: `hybrid_safety`
  - run id: `E06_HYBRID_LLM_SAFETY_4V_S1_v4_seed1_real`
  - error: `subprocess.CalledProcessError` with return code `120`

## 3. Evidence Reviewed

Reviewed files and outputs:

- `git status --short`
- `git branch --show-current`
- `git log -8 --oneline`
- `scripts/run_dissertation_pilot.py`
- `src/controllers/hybrid_llm_safety_controller.py`
- `src/controllers/decision_pipeline.py`
- `ttc_safety.py`
- `src/safety/safety_verifier.py`
- `src/llm/postprocessor.py`
- `results/pilot/dissertation_pilot_v1/pilot_failures.json`
- `results/pilot/dissertation_pilot_v1/pilot_summary.csv`
- `results/pilot/dissertation_pilot_v1/rule_based/E01_BASELINE_4V_S1_v4_seed1/run_metadata.json`
- `results/pilot/dissertation_pilot_v1/raw_llm/E04_RAW_LLM_4V_S1_v4_seed1_real/run_metadata.json`
- `results/pilot/dissertation_pilot_v1/hybrid/E05_HYBRID_LLM_4V_S1_v4_seed1_real/run_metadata.json`
- `results/pilot/dissertation_pilot_v1/hybrid/E05_HYBRID_LLM_4V_S1_v4_seed1_real/step_records.csv`

Also checked:

- `git grep -n "120"`
- `git grep -n "sys.exit"`
- `git grep -n "CalledProcessError"`
- `git grep -n "timeout"`

Important negative evidence:

- no repository code path explicitly returns `120`
- no `sys.exit(120)` exists in the repository
- no additional `hybrid_safety` result directory was produced
- no traceback file or stderr capture exists in the pilot output

## 4. Last Known Good Event

The last confirmed successful event was the completion of the `hybrid` controller:

- `results/pilot/dissertation_pilot_v1/hybrid/E05_HYBRID_LLM_4V_S1_v4_seed1_real/run_metadata.json`
  - `status: completed`
  - `departed_count: 4`
  - `arrived_count: 4`
  - `collision_count: 0`

The `hybrid` step records also show a full run artifact was written.

## 5. First Known Failure Event

The first confirmed failure event is the pilot runner recording:

- controller: `hybrid_safety`
- run id: `E06_HYBRID_LLM_SAFETY_4V_S1_v4_seed1_real`
- error: `Command ... returned non-zero exit status 120`

No `hybrid_safety` run metadata or step records were created, so the failure happened before artifact finalization.

## 6. Exit Code 120 Origin

Based on repository evidence:

- not from a repository `sys.exit(120)` call
- not from an explicit `CalledProcessError` handler in the codebase
- not from the pilot runner's own hard-coded exit path

Therefore the exact origin of `120` is:

**INSUFFICIENT_EVIDENCE**

Most likely it came from the `hybrid_safety` controller process or its underlying SUMO/TraCI lifecycle, but the repository does not contain enough logs to prove the exact layer.

## 7. hybrid vs hybrid_safety Difference

The `hybrid_safety` path differs from `hybrid` only by adding a safety stage:

- `hybrid`:
  - prompt builder
  - live provider or fallback
  - response parser
  - deterministic validation
  - interface rule
  - cooperative postprocessor
  - logging

- `hybrid_safety`:
  - same as `hybrid`
  - plus safety guard via `ttc_safety.verify_decisions(...)`

The safety path adds:

- extra TraCI reads (`getRouteID`, `getSpeed`)
- safety verification via `src.safety.safety_verifier.verify_decisions`
- final-stage downgrade behavior if needed

There is no evidence in the repository that `hybrid_safety` introduces a new prompt, a new LLM model, or a new controller concept.

## 8. TraCI Lifecycle Analysis

From `src/controllers/decision_pipeline.py`:

- `traci.start(...)` is called inside a `try`
- `traci.close(False)` is called in `finally` when startup succeeded

This means the code intends to clean up TraCI even on failure.

However, the pilot left residual SUMO GUI instances during the failure investigation, which means cleanup did not fully complete in practice.

Conclusion:

- TraCI cleanup was intended
- TraCI cleanup did not fully succeed during the failed pilot
- the strongest evidence supports a lifecycle/cleanup failure, not a method redesign issue

## 9. SUMO Process Analysis

Observed during investigation:

- residual `sumo-gui` processes were seen after the failing run
- there was no completed `hybrid_safety` artifact directory

This suggests one of the following:

1. the `hybrid_safety` controller did not fully terminate its SUMO GUI instance
2. the pilot runner exited while a SUMO GUI child was still active
3. the controller subprocess was interrupted during shutdown

What can be proven:

- there was a SUMO process lifecycle problem

What cannot be proven from current evidence:

- whether the `120` came from Python, SUMO, the Windows subprocess wrapper, or a timeout event

## 10. Python Exception Analysis

Current evidence:

- `pilot_failures.json` records a `subprocess.CalledProcessError`
- no traceback file was written
- no stderr capture was written
- no repository code explicitly handles this specific failure path

So the exact primary exception inside the failing controller is:

**INSUFFICIENT_EVIDENCE**

The only reliable statement is that the pilot runner saw the child process exit non-zero.

## 11. Primary Root Cause

**Primary Cause: `SUMO_PROCESS_LIFECYCLE_FAILURE`**

Reason:

- the failure occurs only on the final controller
- the failure is associated with the controller subprocess exit
- residual SUMO GUI instances were observed during the investigation
- no method, prompt, or safety-rule change is implicated by the evidence

## 12. Secondary Issues

**Secondary Issue: `TRACI_CONNECTION_CLEANUP_FAILURE`**

Reason:

- the controller code relies on `traci.start(...)` / `traci.close(False)`
- the safety path adds extra TraCI reads
- the run did not finalize cleanly into a `hybrid_safety` artifact directory

Additional possible contributing issue:

- `WINDOWS_SUBPROCESS_FAILURE` or timeout-related wrapper behavior

But this remains unproved, so it should not be treated as the primary conclusion.

## 13. Research Impact

This failure does **not** indicate a method change is required.

It does indicate:

- the pilot execution chain is not yet fully reliable
- the `hybrid_safety` run needs lifecycle hardening before dissertation pilot evidence is considered complete
- previous successful controller runs remain valid as engineering evidence

Interpretation:

- not a method bug
- not a prompt bug
- not a safety-logic redesign issue
- most likely an execution / cleanup issue

## 14. Minimal Fix Plan

Minimal fix plan only, no implementation applied:

1. Add stdout/stderr capture to the pilot runner for each controller subprocess.
2. Write controller-specific failure logs before raising `CalledProcessError`.
3. Record controller start/end timestamps and exit code in the pilot summary.
4. Add explicit controller-scoped cleanup verification after each controller completes.
5. Add process ownership checks before moving to the next controller.
6. Add a safer subprocess timeout / shutdown path so hanging GUI instances cannot silently carry forward.

Behavioral impact:

- no change to controller logic
- no change to prompt
- no change to safety threshold
- no change to cooperative rule

Pilot rerun requirement:

- yes, the pilot as a whole should be rerun after lifecycle hardening
- previous successful controller runs remain valid as engineering evidence, but not as a complete pilot record

## 15. Required Revalidation

Required after any fix:

1. `pytest`
2. fixed pilot runner
3. one fixed 4-controller pilot
4. check that all four controllers complete
5. confirm no residual SUMO GUI processes remain
6. confirm the final pilot outputs include `hybrid_safety`

## 16. Final Verdict

**ROOT_CAUSE_PARTIALLY_IDENTIFIED**

Why not fully identified:

- the repository does not contain the missing traceback or stderr evidence needed to prove the exact origin of `120`

Why not method-change required:

- no evidence shows the safety algorithm itself is wrong
- the failure is concentrated in controller execution and process lifecycle handling
- the method freeze remains intact
