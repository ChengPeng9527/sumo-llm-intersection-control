# Research Readiness Review

## Executive Summary

The repository is **pilot-ready** and the method is effectively frozen for formal experimentation, but the project is **not yet dissertation-evaluation complete**.

Evidence base at this point:

- `pytest`: 30 passed
- SUMO smoke test: passed
- Live Groq revalidation: passed
- Decision pipeline separation: implemented and traceable
- Formal experimental sweep: not yet run

Conclusion in one sentence: the codebase can support a controlled pilot and then a formal experimental campaign, but the current evidence is still a mix of engineering validation, preliminary smoke evidence, historical evidence, and one live revalidation, so the final dissertation results have not yet been collected.

## Current Status

### Repository Audit

- Current branch: `phase-18-decision-pipeline-separation`
- Current repository status: uncommitted research documentation under `docs/research/`
- Latest commits:
  - `dc47d62` Document Phase 18 live revalidation
  - `2b7c090` Document Phase 18 blocked Groq validation
  - `e9d712b` Freeze Phase 18 decision pipeline
  - `269a976` Document Phase 18 decision pipeline separation
  - `24a339f` Separate raw, hybrid and safety decision stages
- Current `pytest` result: 30 passed

### Current Engineering Validation

The repository currently demonstrates:

- separated raw / hybrid / hybrid+safety decision paths
- structured prompt building
- response parsing and normalization
- cooperative post-processing
- deterministic safety verification
- unified step-record logging and trace fields
- mock SUMO smoke execution
- one live Groq revalidation request through the current pipeline

### Current Evidence

Current evidence is split into three classes:

- Engineering evidence: unit tests, smoke test, live revalidation
- Preliminary evidence: smoke output and historical runs
- Dissertation evidence: not yet complete because the formal experiment matrix has not been executed

### Current Documentation

The repository already contains the research-design package under `docs/research/`:

- research design
- experimental protocol
- evaluation specification
- traceability matrix
- simulation assumptions
- data catalog
- simplified method explanation
- how-to-run guide
- current research status

## Method Freeze

### Frozen Components

The following are effectively frozen for Phase 18:

- Prompt structure
- LLM model choice
- Controller interfaces
- Decision pipeline order
- Validation layer
- Cooperative postprocessor
- Safety verifier
- Logging schema
- Output artifacts
- Experiment runner entry points

### What Is Still Experimental

The method itself is not being redesigned, but the following remain experimental only in the sense that they still need formal evaluation:

- comparative performance claims
- effect-size claims
- scalability claims
- dissertation conclusions

### Freeze Verdict

**METHOD_READY_FOR_FORMAL_EXPERIMENT**

## Experiment Readiness

### Are all four controllers executable?

Yes.

- Rule-based controller: executable
- Raw LLM controller: executable
- Hybrid controller: executable
- Hybrid + Safety controller: executable

### Can they be run from one experiment interface?

Yes. `src/experiments/experiment_runner.py` dispatches the controller scripts from a common interface.

### Can they produce identical output schema?

Yes. The common logging schema is shared through `FIELDNAMES`, and the controllers write the same core record structure with stage-specific fields.

### Can all logs be compared?

Yes, with one caveat: the historical directories contain some metadata inconsistencies and should be treated as historical evidence only, not as final dissertation runs.

### Experiment Readiness Verdict

**READY_WITH_LIMITATIONS**

## Simulation Audit

### What SUMO controls

SUMO still controls:

- vehicle dynamics
- car-following behavior
- lane geometry
- internal junction movement
- collision avoidance when control is handed back to SUMO
- native right-of-way behavior in the network

### What the project controller controls

The project controls:

- whether a vehicle gets `WAIT`, `PROCEED`, or `FREE`
- whether a vehicle is treated as inside or outside the control zone
- cooperative promotion of compatible waiting vehicles
- deterministic safety downgrades
- logging of raw, validated, postprocessed, and final decisions

### Direct answers

- Does SUMO native right-of-way dominate vehicle behaviour? **Yes, partially.** The project does not replace SUMO motion logic; it overlays decision commands on top of the simulator.
- Does SUMO collision avoidance override controller decisions? **Yes, potentially.** The controller can set high-level commands, but SUMO still governs vehicle motion and safety at the simulation level.
- Does TraCI have full control of the decision stage? **No.** TraCI is used to apply speed-level actions, but SUMO still executes the vehicle dynamics.
- Could SUMO invalidate the experiment conclusions? **It could invalidate any claim that the controller alone fully determines motion.** It does **not** invalidate the intended system-level evaluation, as long as the dissertation frames the result as a SUMO-based controller evaluation.

### Simulation Audit Conclusion

**READY_WITH_LIMITATIONS**

## Metric Audit

| Metric | Available? | Current log fields | Calculation | Suitable for dissertation? | Status |
| --- | --- | --- | --- | --- | --- |
| Completion Rate | Yes | `departed`, `arrived`, `departed_count`, `arrived_count` | `arrived / departed` | Yes | READY |
| Throughput | Yes | `arrived`, `arrived_count` | arrived count | Yes | READY |
| Mean Waiting Time | Yes | `speed_after_action`, `stop_speed` | stop-like steps per vehicle | Yes, with caveats | READY_WITH_LIMITATIONS |
| Mean Speed | Yes | `speed_after_action` | mean speed across records | Yes | READY |
| Episode Duration | Yes | `simulation_time_seconds`, `simulation_step` | max minus min or final step duration | Yes | READY |
| Collision Count | Yes | `collision`, `collision_count` | count collisions | Yes | READY |
| TTC (if available) | Proxy only | `time_to_intersection`, `conflict_detected`, `tti_threshold_seconds` | threshold-based proxy / conflict count | Yes, with caveats | READY_WITH_LIMITATIONS |
| Parser Success | Yes | `json_parse_success` | successful parses / requests | Yes | READY |
| Fallback Rate | Yes | `fallback_used` | fallback count / requests | Yes | READY |
| Latency | Yes | `llm_response_time_ms` | average latency | Yes | READY |
| Safety Override | Yes | `safety_override`, `safety_reason` | override count / eligible rows | Yes | READY |
| Decision Distribution | Yes | `llm_raw_decision`, `validated_llm_decision`, `postprocessed_decision`, `final_decision` | action counts by stage | Yes | READY |
| Postprocessor Intervention | Yes | `postprocess_applied`, `postprocess_reason` | intervention count / eligible rows | Yes | READY |
| Decision Agreement | Yes | raw / validated / postprocessed / final fields | agreement and change rates | Yes | READY |
| Decision Flow | Yes | stage-specific decision fields and source fields | stage-to-stage transitions | Yes | READY |

### Metrics Missing or Not Exact

- Exact pairwise TTC is not directly logged as a full pairwise metric.
- Native SUMO override frequency is not directly logged as a separate simulator-side metric.
- Classical queueing-theory delay is not directly logged.

## Evidence Audit

| Evidence Type | Engineering Evidence | Preliminary Evidence | Dissertation Evidence | Not Usable |
| --- | --- | --- | --- | --- |
| Unit Tests | Yes | No | No | No |
| Smoke Tests | Yes | Yes | No | No |
| Live Revalidation | Yes | Yes | No | No |
| Historical Experiments | Yes | Yes | Limited | Some old directories are not clean enough for final claims |
| Formal Experiments | No | No | No | Not yet run |

### Evidence Verdict

- Unit tests: engineering evidence only
- Smoke tests: preliminary evidence only
- Live revalidation: engineering evidence and limited preliminary evidence
- Historical experiments: useful context, but some result directories have metadata inconsistencies and should not be treated as final dissertation evidence
- Formal experiments: not yet available

## Risk Review

### Critical

- LLM provider updates or API instability can change output behavior.
- Insufficient repetitions would weaken any dissertation claim.
- Metric validity risk exists if waiting time or TTC proxies are interpreted too strongly.
- Decision trace integrity must remain consistent across raw, validated, postprocessed, and final fields.

### Medium

- Prompt drift if the prompt builder changes after freeze.
- Scenario bias if only one density or one seed is used.
- SUMO version differences across machines or reinstallations.
- Log completeness if a run fails mid-episode.

### Low

- Random-seed implementation risk is already controlled by the scenario generator.
- File-path differences are manageable as long as the repository root is fixed.

## Pilot Recommendation

### Minimum Pilot

Recommended pilot:

- 4 controllers
- 4 vehicles
- 1 seed
- 1 live run

Purpose:

- validate the full experiment pipeline end to end
- confirm that the live provider path, parser, cooperative stage, safety stage, logging, and traces all work together
- do **not** use the pilot to draw dissertation conclusions

### Pilot Verdict

The repository is ready for this pilot.

## Formal Experiment Recommendation

### Minimum Viable Dissertation Experiment

- Controllers: rule, raw, hybrid, hybrid + safety
- Vehicle counts: 4 and 8
- Seeds: 3
- Total runs: 24
- LLM-bearing runs: 18
- Approximate live LLM requests at the current default interval of 1: `18 * (240 + 400) / 2 = 11,520` requests
- Output triplets: 24 `step_records.csv`, 24 `run_metadata.json`, 24 `events.jsonl`
- Figures: 3 to 4
- Tables: 4 to 6

### Recommended Dissertation Experiment

- Controllers: rule, raw, hybrid, hybrid + safety
- Vehicle counts: 4, 8, 16
- Seeds: 5
- Total runs: 60
- LLM-bearing runs: 45
- Approximate live LLM requests at the current default interval of 1: `5 * (240 + 400 + 720) * 3 = 20,400` requests
- Output triplets: 60 `step_records.csv`, 60 `run_metadata.json`, 60 `events.jsonl`
- Figures: 5 to 8
- Tables: 6 to 10

### Extended Experiment

- Add density sensitivity runs or extra live confirmations for a subset of seeds
- Use this only after the recommended matrix is stable
- Estimated LLM requests: `30,000+` depending on density and repetition choices

### Runtime Estimate

- The live revalidation demonstrated a single-request latency of about 1.4 seconds.
- With the current default decision interval of 1, a live matrix would be hours-long rather than minutes-long.
- Exact wall-clock time is **INSUFFICIENT_EVIDENCE** because the repository does not yet contain a full benchmark sweep for all run sizes.

## Final Verdict

**READY_WITH_MINOR_FIXES**

### Why this verdict

- The method is frozen enough for formal evaluation.
- The controllers are executable from one interface.
- The logging schema is shared and comparable.
- The repository already has engineering validation and one live revalidation.
- However, the formal experiment sweep has not yet been run, and historical evidence contains some metadata inconsistencies that should be treated carefully before dissertation data collection.

### What this means in practice

- The project is ready for a pilot immediately.
- The project is close to formal experimentation readiness.
- The next safe step is to run the minimum pilot, then proceed to the formal matrix if the pilot confirms the pipeline remains stable.
