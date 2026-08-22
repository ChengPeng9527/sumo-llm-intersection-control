# Live LLM Runtime Cost Audit

## 1. Expected Provider Calls in 4V

Evidence:
- `src/controllers/decision_pipeline.py` calls `llm_provider(...)` when `step % llm_decision_interval == 0 or not cached_trace`.
- `scripts/run_formal_experiment_matrix.py` sets `LLM_DECISION_INTERVAL = "1"` for formal runs.

Observed mock 4V episode:
- Run: `results/raw/AUDIT_RAW_LLM_RUNTIME_v4_seed1_runtimeaudit4v_mock`
- `simulation_step` range: `0..52`
- Unique decision steps: `53`
- Vehicle rows: `132`
- Max active vehicles in a single step: `4`
- Step row distribution: `1:6; 2:25; 3:12; 4:10`

Conclusion:
- `expected_provider_requests_per_episode` for `formal_low_v4_seed1` is `53`.
- `duplicate request opportunities` if request logic were accidentally per-row instead of per-step: `132 - 53 = 79`.

## 2. Estimated 4V Live Runtime

Provider smoke baseline:
- Mean total tokens/request: `1069.2`
- Safe interval: `8.019 s`
- Mean latency: `6.328292 s`
- p95 latency: `50.67142 s`

Runtime estimate for `53` requests:
- Minimum: `53 * 8.019 = 425.01 s` `(~7.08 min)`
- Likely: `~425.01 s` because mean latency is below the pacing floor
- Worst-case tail estimate: `53 * 50.67142 = 2685.59 s` `(~44.76 min)`

## 3. Expected Provider Calls in 8V

Observed mock 8V episode:
- Run: `results/raw/AUDIT_RAW_LLM_RUNTIME_v8_seed1_runtimeaudit8v400_mock`
- `simulation_step` range: `0..105`
- Unique decision steps: `106`
- Vehicle rows: `290`
- Max active vehicles in a single step: `5`
- Step row distribution: `1:8; 2:56; 3:10; 4:20; 5:12`

Conclusion:
- `expected_provider_requests_per_episode` for `formal_low_v8_seed1` is `106` for the scenario duration used by the mock run.
- `duplicate request opportunities` if request logic were accidentally per-row instead of per-step: `290 - 106 = 184`.

## 4. Estimated 8V Live Runtime

Runtime estimate for `106` requests:
- Minimum: `106 * 8.019 = 850.01 s` `(~14.17 min)`
- Likely: `~850.01 s` because mean latency is below the pacing floor
- Worst-case tail estimate: `106 * 50.67142 = 5371.17 s` `(~89.52 min)`

## 5. Slow or Hung

The available evidence does not point to a controller-loop hang in the 4V mock episode:
- The mock 4V run completed cleanly.
- `results/raw/E04_RAW_LLM_4V_S1_v4_seed1_recheck3_real/run_metadata.json` also shows `status = completed`, `departed_count = 4`, `arrived_count = 4`, and the corresponding events log reaches final arrivals at simulation step `53`.

The more important finding is a lifecycle mismatch in the formal 8V path:
- `simulation/generated_routes/formal_low_v8_seed1/generation_config.json` sets `simulation_duration_seconds = 400`.
- `scripts/run_formal_experiment_matrix.py` overrides 8V runs to `SIMULATION_STEPS = max(duration, 1200)`, so the formal 8V launcher asks the controller to step beyond the SUMO horizon.
- A direct 8V mock run with `SIMULATION_STEPS = 1200` fails with `traci.exceptions.FatalTraCIError: Connection closed by SUMO.` at `traci.simulationStep()`.

Verdict on the observed blocker:
- This is a runtime/lifecycle bug, not just a slow provider path.

## 6. Dominant Runtime Cost

The dominant cost is serialized request pacing, not parsing.

Why:
- Safe interval is `8.019 s`.
- Mean provider latency is only `6.328 s`.
- That means the pace guard dominates the start-to-start interval for typical requests.

## 7. Current LLM Decision Frequency Semantics

Current semantics are step-based, not state-change-based:
- One LLM decision opportunity per simulation step when `LLM_DECISION_INTERVAL = 1`.
- The prompt is rebuilt from the full current `traffic_state` list each time.
- There is no cache keyed on unchanged traffic state.
- The same vehicle state can therefore be re-evaluated on consecutive steps if it remains present.
- A single prompt aggregates all relevant vehicles at that step; it is not a per-vehicle request loop.

Practical consequence:
- The controller is semantically `one provider call per simulation step`, not `one provider call per new information event`.

## 8. Practicality for Full Formal Experiments

As written, the design is not ready for the full formal matrix.

Reason 1, runtime:
- 4V raw runs are roughly `7.1 min` minimum wall-clock per episode.
- 8V raw runs are roughly `14.2 min` minimum wall-clock per episode.
- Tail latency can push either case much higher.

Reason 2, lifecycle:
- The formal 8V launcher currently overshoots the SUMO duration and can abort with `Connection closed by SUMO`.

This means the current blocker is not provider reliability anymore; it is the experiment orchestration / simulation horizon mismatch.

## 9. Final Verdict

`LIVE_LLM_RUNTIME_BUG_FOUND`

