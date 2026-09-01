# Counterfactual Replay-Equivalence Specification

## Paths

For one representative deterministic S3-12V replay state:

- Path A: replay to checkpoint and continue uninterrupted with the deterministic comparator.
- Path B: replay to the same checkpoint, save SUMO/Python state, terminate/reload, restore both states, then continue with the same deterministic comparator.

No forced R4/S2 action is permitted during equivalence validation.

The implemented representative state is the frozen Phase 2
`S3_COOPERATIVE_OPPORTUNITY` 12V seed 1 state immediately before decision
epoch 3 at simulation time 21.0 s. The runner requires the live candidate set
to match the frozen 18-candidate set and its derived SHA-256 before either path
may continue.

## Gate

`REPLAY_EQUIVALENT` requires exact equality for decision sequence, selected candidate IDs, arrived vehicle IDs, completion, grant events, collision count, safety-intervention count, and termination reason.

Step/trajectory numerical structures, waiting-by-vehicle, speed-by-vehicle, and duration must have identical structure and differ by no more than the preregistered absolute tolerance `1e-6`. Missing fields, any discrete mismatch, or any numerical excess is `REPLAY_NOT_EQUIVALENT` and invalidates the checkpoint for scientific branching.

The technical runner writes only under
`results/counterfactual_validation/replay_equivalence_attempt2/`. Attempt 1 is
retained unchanged under `results/counterfactual_validation/replay_equivalence/`
as infrastructure-error evidence. The runner refuses an
existing output root. Path B preserves the pending simulation step: after
`loadState`, Python/controller state is restored and that state is processed
without a second `simulationStep()` or duplicate metric accumulation.

SUMO is started with `--save-state.precision 15` so save/load does not apply
the default two-decimal quantisation that invalidated attempt 1 under the
pre-registered `1e-6` comparison tolerance. `--save-state.rng true` preserves
the stochastic simulator state required by the deterministic continuation.
Neither option changes planner, candidate, controller, or safety semantics.

The local command is:

```powershell
& "C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe" scripts/run_counterfactual_replay_equivalence.py
```

The command performs two logical technical paths (one uninterrupted reference
and one checkpoint/restore replay). Path B necessarily closes the
pre-checkpoint TraCI session and starts a fresh SUMO session for `loadState`.
It performs no provider request and contains no forced candidate choice.

## Evidence and limits

Retain both continuation outcome structures, all checkpoint files, config hashes, candidate-set hash, and gate report. A successful technical replay check demonstrates only that restore did not change this deterministic continuation; it does not establish a planner effect, a traffic benefit, or real-world safety.
