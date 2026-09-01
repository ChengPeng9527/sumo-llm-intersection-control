# Counterfactual Snapshot Protocol

## Boundary

This protocol implements only checkpoint/restore infrastructure. It does not run a scientific counterfactual, force R4/S2, call Gemini, or alter frozen evidence.

## Required state

SUMO/TraCI `saveState` captures simulation-internal time, vehicles, routes, lanes, speeds, positions, traffic-light state, and SUMO-owned runtime state. It does **not** capture Python objects. The checkpoint therefore also persists:

- `CandidateGrantController`: planner mode/configuration, active grant candidate/vehicle IDs/start/timeout, trace template, in-progress decision record, completed decision records, and decision epoch counter.
- Runner experiment state: current step/time, departed/arrived/all-seen IDs, maximum waiting map, speed total/count, collision count, events, step records, termination state, and any retained provenance/latency accumulators.
- Metadata: scenario, seed, simulation time, decision epoch, candidate-set hash, R4/S2 IDs, config hashes, and source frozen-decision reference.

The future branch runner must explicitly provide the runner experiment-state dictionary. Unknown mutable planner/safety state is not assumed to be serializable; it must be represented explicitly or the branch must fail closed.

## Checkpoint format

Each independent directory under `results/counterfactual_validation/checkpoints/` contains:

1. `sumo_state.xml`
2. `controller_state.json`
3. `experiment_state.json`
4. `checkpoint_metadata.json`

Existing checkpoint directories are rejected. Metadata and JSON state must validate before restore; config-hash mismatch, malformed JSON, missing files, or incomplete provenance rejects the checkpoint.

## Future branch protocol

After replay equivalence passes, reproduce each of the three historical S3 disagreement states, checkpoint immediately before the differing selection, then create two continuations from that same checkpoint: force legal R4 once or force legal S2 once. Resume the deterministic comparator after that single forced grant.

The prospective matrix is `3 states x 2 forced legal actions = 6` SUMO continuation runs, with `0` Gemini calls. It must be separately preregistered and authorized. Metrics are mean/max/sample-SD/per-approach waiting, mean speed, duration, completion/throughput, collisions, safety interventions, and grant timeouts.
