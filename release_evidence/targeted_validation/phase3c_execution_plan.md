# Phase 3C Closed-Loop Execution Plan

## Preconditions

1. Preserve the current worktree and create no output in existing Phase 1, Phase 2, Phase 3B1, R1, or R2 paths.
2. Implement and test only the derived Phase 3C measurement observer described in `phase3c_measurement_gap.md`; do not change controller, prompt, parser, candidate, comparator, safety, route semantics, model, or timeout semantics.
3. Create a new Phase 3C scenario-definition/configuration namespace that encodes the two preregistered demand schedules. This future configuration change is a scenario input, not a runtime state edit.
4. Use the verified manual PowerShell/proxy environment. Run at most one bounded connectivity gate before experimental episodes; a failed gate means all planned Gemini episodes are `NOT_RUN` and no experiment begins.
5. Record repository HEAD, branch, config hashes, generated route/departure files, initial-demand signatures, provider/model, and the strict-mode setting before execution.

## Run order and output isolation

Output root: `results/phase3c_closed_loop_waiting_divergence/`.

For each condition and seed, generate demand once, then run its deterministic and Gemini episodes as independent processes using that exact initial-demand signature. The Gemini run uses `STRICT_LLM_MODE=true`. Suggested order is paired execution by condition and seed:

1. `MODERATE_WAITING_PRESSURE`, seeds 1--3: deterministic then Gemini.
2. `HIGH_WAITING_PRESSURE`, seeds 1--3: deterministic then Gemini.

Do not alter later demand schedules in response to earlier agreement, divergence, traffic metrics, or failures. Do not repeat a valid episode. A strict Gemini failure is retained as invalid/excluded evidence and stops that episode; it does not become a deterministic fallback result.

## Per-episode checks

- Validate paired initial-demand signatures before comparing planners.
- Deterministic: confirm normal completion/provenance and retain records even if no eligible trade-off epoch occurs.
- Gemini: require `llm_valid_decisions >= 1`, `llm_failed_decisions == 0`, `fallback_decisions == 0`, and `llm_episode_valid == true` for LLM-effectiveness inclusion.
- For every run, retain `summary.json`, `run_metadata.json`, `events.jsonl`, `decision_records.jsonl`, `step_records.csv`, and the derived Phase 3C observer output.
- Stop the remaining matrix only for a predeclared environment/integrity blocker: failed connectivity gate, duplicate output target, missing paired demand signature, invalid scenario generation, or an unexpected request-volume anomaly. Preserve the manifest and failure reason.

## Analysis sequence

1. **State emergence:** count runs with at least one eligible R4/S2 trade-off epoch; report the first epoch/time and naturally observed waiting contrast separately for each independent planner trajectory.
2. **Planner divergence:** for valid Gemini epochs, compare Gemini and deterministic selections/ranks only at the recorded same-state decision. Report the R4-vs-S2 structure, candidate legality, and provider/parser/fallback status.
3. **System consequence:** report descriptive paired traffic and safety outcomes only for completed independent episodes. Never use post-divergence Gemini and deterministic states as if they were shared counterfactuals.
4. **Validity:** report total, valid, invalid, and excluded Gemini episodes. Do not aggregate invalid Gemini episodes into LLM-effectiveness results.

## 12 versus 6 episodes

The 12-episode matrix is the scientific minimum for the preregistered comparison because it includes both moderate and high pressure conditions across three seeds. It is recommended **only after** the manual connectivity gate passes and the team accepts roughly 30 Gemini logical requests.

The six-episode `HIGH_WAITING_PRESSURE` alternative halves the expected request count to about 15 and reduces exposure to current provider/network risk. It is appropriate only as a labelled feasibility pilot: it cannot assess whether higher pressure is associated with a greater divergence probability because it has no moderate-pressure comparator.

## Reporting language

Permitted: "Under the preregistered S3 12V demand schedules, an eligible state was/was not observed, and valid Gemini selections agreed/disagreed with the deterministic comparator at the recorded epochs."

Not permitted: claims of Gemini superiority, deterministic inferiority, fairness optimisation, internal threshold discovery, statistical significance, broad generalisation, or real-world safety/deployment readiness.
