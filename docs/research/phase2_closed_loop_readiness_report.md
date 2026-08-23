# Phase 2 Step 8 Closed-Loop Readiness Report

## Status and scope

Status: `STEP8_READY_WITH_LIMITATIONS`

Step 8 converts the Phase 2 foundation into an explicit two-layer evaluation method without changing the Step 2-6 route, conflict, candidate, comparator, Gemini, fallback, or safety definitions. It does not execute the formal matrix and does not make a planner-superiority claim.

## Two-layer methodology

Layer 1 is Offline Paired Decision Analysis. The deterministic comparator and Gemini receive the same recorded privacy-minimised traffic state and same safe candidate set. Valid comparisons are candidate preference, agreement/disagreement, fallback, parser/provider reliability, counterfactual safety intervention, latency, and token usage. Observer-trajectory completion, throughput, waiting, speed, and duration are not planner outcomes.

Layer 2 is Closed-Loop Paired Controller Evaluation. The same scenario, vehicle count, seed, routes, departures, vehicle parameters, and network initialize two independent SUMO episodes. Each planner's selected candidate is converted to `PROCEED/WAIT/FREE`, verified by safety, and applied to its own episode. Subsequent trajectories may diverge and must not be shared.

## Closed-loop runtime

The existing `run_pipeline_controller` remains the single TraCI episode loop. Step 8 adds two explicit modes:

- `DETERMINISTIC_CANDIDATE`
- `GEMINI_CANDIDATE`

Both modes share state extraction, route semantics, conflict compatibility, candidate generation, candidate-to-action conversion, dynamic safety verification, action application, metrics, events, and artifacts. They differ only in Step 4 comparator versus frozen Step 5/6 Gemini candidate selection.

The native static traffic signal is held at all green during candidate-controlled episodes so it does not remain an unreported third controller. Non-selected controlled vehicles are stopped through the existing `WAIT` action. Vehicles outside control scope remain `FREE`. The frozen safety verifier retains final authority.

## Grant lifecycle

A decision epoch occurs only when no grant is active and at least one safe candidate exists. The selected candidate becomes an active passage grant. Its vehicles retain `PROCEED`; competing controlled vehicles retain `WAIT`; and no planner call occurs on intervening simulation updates.

Clearance is deterministic: a grant ends when every granted vehicle has either left the existing circular intersection control scope or left the simulation. All selected vehicles are inside that scope when the candidate is created, so the rule directly observes passage completion rather than using elapsed time as the primary condition.

The fixed failsafe timeout is 45 simulation seconds. A timed-out grant is closed with `GRANT_TIMEOUT`, one all-WAIT controlled update occurs, and replanning becomes eligible on the next update. The timeout is not adaptive and does not modify comparator priority.

Safety is reapplied on every controlled update, including while a grant is active. A safety downgrade to `WAIT` does not erase grant provenance or automatically cancel the grant; clearance or timeout still determines its lifecycle.

## Latency, fallback, and provider parameters

Gemini is invoked synchronously once per new grant. SUMO does not call `simulationStep` while the request is pending, so API wall-clock latency does not advance simulation time. Each decision record stores simulation time, provider timestamps, provider latency, and total planner wall latency.

Provider/model remain `Google Gemini / gemini-3.6-flash`. The request records the configured JSON response contract, `max_completion_tokens=512`, `reasoning_effort=low`, 60-second timeout, and four provider retries. `temperature`, `top_p`, and provider seed are not explicitly set; they are recorded as provider defaults rather than assigned invented values.

Provider failure, timeout, malformed JSON, or illegal candidate falls back to the unchanged Step 4 comparator over the same candidate set. The fallback candidate receives a normal grant. `selection_source`, `fallback_reason`, and `grant_source` remain distinct.

## Canonical decision provenance

Each decision epoch produces one JSONL record under its run's existing raw-results directory. It contains:

- run/scenario/vehicle-count/seed/planner and decision epoch
- simulation step/time and privacy-minimised local vehicle inputs
- candidate set, candidate features, deterministic and Gemini selections
- agreement/disagreement, redacted raw response, parser/provider status
- fallback status/reason, final selection, selection/grant source
- grant vehicles, start/end, duration, clearance reason, and timeout status
- intended/final actions for every active-grant update and safety interventions
- provider/model, explicit request parameters, provider-default markers
- latency, token usage, prompt hash, and canonical prompt reconstruction inputs

Persisted local input fields are vehicle ID, incoming/outgoing edge, movement, speed, distance, ETA, waiting time, and control-zone state. Origin, destination, complete route, and route history are excluded.

The per-vehicle CSV schema now also includes `waiting_time`; JSONL is the canonical epoch-level attribution record.

## S2 correction

Future S2 representative-state selection uses TTI spread only when at least two finite ETAs exist. Otherwise `eta_simultaneity_available=false` and `arrival_tti_spread=null`. Scenario-level simultaneity evidence remains the explicit clustered departure design rather than an artificial zero ETA spread. The historical Step 7 JSON is retained as pilot evidence and its zero-spread limitation is documented rather than rewritten.

## Seed validity

Targeted route assignment is fixed for every scenario and does not change by seed.

- S1 and S3: seed controls the configured zero-to-one-second departure jitter and SUMO's Krauss car-following imperfection (`sigma=0.5`).
- S2 and S4: routes and departure offsets remain exact by design; seed controls only SUMO's Krauss car-following stochasticity (`sigma=0.5`).

Generation records these semantics and a SHA-256 initial-demand signature. Same scenario/seed generation is reproducible. S2/S4 seeds are stochastic trajectory replicates with identical demand schedules, not independently redrawn demands.

## Validation

Canonical Python: `C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe`

- Focused Step 8 tests: `16 passed`
- Directly affected regression tests: `44 passed`
- Full suite after core implementation: `157 passed`

Focused coverage includes planner-mode initialization, grant persistence, no per-step replanning, clearance, timeout, post-clearance epoch creation, one provider call per grant, fallback grants, dynamic safety, canonical provenance, waiting-time persistence, finite-ETA S2 handling, reproducible generation, and paired demand records.

## Deterministic S3 8V smoke

Scenario `S3_COOPERATIVE_OPPORTUNITY`, vehicle count 8, seed 7:

- independent SUMO run completed `8/8`
- completion rate `1.0`, throughput `8`
- decision epochs/grants `4/4`
- grant durations `7, 8, 9, 9` seconds; mean `8.25`, maximum `9`
- all four grants cleared by `ALL_GRANTED_VEHICLES_LEFT_CONTROL_SCOPE`
- timeout `0`, collision `0`, safety intervention `0`, controller crash `0`
- mean waiting `7.75` seconds, maximum waiting `16.0` seconds
- mean speed `7.8423 m/s`, episode duration `44.0` seconds
- provider requests/tokens `0/0`

The vehicles responded to grants, no per-step oscillation occurred, and decision JSONL reconstructs every grant.

## Gemini S3 8V smoke

The authorized independent Gemini episode used the same scenario and seed, with a hard maximum of eight requests. It completed with four requests:

- completed `8/8`; completion rate `1.0`, throughput `8`
- decision epochs/grants/provider requests `4/4/4`
- provider success `4/4`, parser success `4/4`, fallback `0/4`
- comparator agreement `4/4`, safety intervention `0`, collision `0`, timeout `0`
- grant durations `7, 8, 9, 9` seconds; all cleared by control-scope exit
- prompt tokens `7213`, completion tokens `208`, total tokens `7421`
- per-request total tokens `487, 3739, 2071, 1124`
- per-request latency `17228.36, 9311.69, 18767.17, 1223.34 ms`; mean `11632.64 ms`
- mean waiting `7.75` seconds, maximum waiting `16.0` seconds
- mean speed `7.8423 m/s`, episode duration `44.0` seconds

All four candidate choices agreed in this smoke, so the two trajectories happened to remain identical. This is pipeline and closed-loop operability evidence, not policy-equivalence evidence.

## Paired initial conditions

Both smoke episodes used the same generated SUMO configuration, scenario ID, eight vehicles, seed 7, route sequence, departure sequence, movement sequence, network, and car-following parameters. Their initial-demand signatures both equal `E456CDC788A0A190D3D92B07836D025DAC58BF46DC07B7139CA2A2E29BCEF7A7`. They were separate TraCI/SUMO processes and did not share trajectory state.

## Traffic metric validity

Completion rate, throughput, mean/maximum waiting time, mean speed, episode duration, and collision count now describe planner-controlled closed-loop outcomes. Decision epochs, grants, grant duration, fallback, safety interventions, latency, requests, and tokens are also recorded. The one smoke pair is validation evidence only and must not be interpreted as a performance comparison.

## Formal matrix reassessment

The six conditions remain justified: S1-S4 at 8V, S3 at 12V, and S4 at 16V. With three seeds and two planners, the closed-loop matrix remains 36 independent runs: 18 scenario-seed pairs, each with one comparator and one Gemini episode. No formal run was executed in Step 8.

The S3 8V smoke used four grants for eight vehicles. A proportional planning estimate gives four grants for each 8V condition, six for S3 12V, and eight for S4 16V: 30 Gemini grants per seed or approximately 90 closed-loop requests across three seeds. A conservative singleton-grant upper planning bound is 180 requests. Actual counts will be trajectory-dependent.

At the observed Step 8 average of 1803.25 prompt, 52 completion, and 1855.25 total tokens per request:

- 90 requests: approximately 162293 prompt, 4680 completion, 166973 total tokens
- 180 requests: approximately 324585 prompt, 9360 completion, 333945 total tokens

Combining the observed per-request extremes with the 90-180 request range yields a broad evidence-based total-token envelope of approximately 43830 to 673020. Larger 12V/16V prompts remain the main uncertainty.

The old `822 requests / 2.43M tokens` estimate represented dense observer-time-step calls and is not the closed-loop budget. If Layer 1 also calls Gemini on every persisted grant state, budget that offline layer separately; do not silently merge it with the 36-run closed-loop matrix.

## Statistical claim boundary

Three seeds support a small-sample comparative/descriptive evaluation only. Means, paired differences, and per-run traces may be reported, but statistical significance or broad generalization must not be claimed without later sample-size justification. S2/S4 retain identical demand schedules across seeds, so results must state that their stochastic variation comes from car-following rather than demand resampling.

## Remaining threats and deferred improvements

- The route-level conflict model is intentionally conservative and repeated same-route vehicles can enlarge groups.
- The single smoke pair had complete planner agreement and does not test divergent trajectories.
- Gemini latency was high and variable; synchronous pausing preserves simulation semantics but affects experiment wall time.
- Larger-scale request counts and prompt sizes are projections until measured.
- Hand-crafted scenarios and three seeds constrain external and inferential validity.

Deferred because Step 8 does not require them: reservation systems, asynchronous API calls, queue schedulers, adaptive timeouts, new optimizers, new safety layers, new candidate geometry, databases, networks, scenario families, providers, prompt tuning, and dissertation changes.

`docs/dissertation/` remains untouched.
