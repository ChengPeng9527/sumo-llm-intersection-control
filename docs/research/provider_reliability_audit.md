# Provider Reliability Audit

## 1. Objective

Audit the reliability of live provider calls in the canonical dissertation pilot, with a focus on:

- total live provider requests
- successful and failed provider calls
- failure distribution
- temporal failure pattern
- controller-to-controller comparison
- possible systematic provider bias
- whether the current evidence is sufficient for a fair formal experiment

This audit is based only on repository artifacts from:

- `results/pilot/dissertation_pilot_v1/`
- `results/diagnostics/`
- controller logs and trace fields embedded in the pilot artifacts

No code, prompt, model, controller, postprocessor, safety rule, or fallback policy was modified for this audit.

## 2. Evidence Sources

Primary evidence:

- `results/pilot/dissertation_pilot_v1/pilot_summary.json`
- `results/pilot/dissertation_pilot_v1/pilot_summary.csv`
- `results/pilot/dissertation_pilot_v1/request_cost_summary.json`
- `results/pilot/dissertation_pilot_v1/pilot_verification.json`
- `results/pilot/dissertation_pilot_v1/decision_flow_summary.csv`
- `results/pilot/dissertation_pilot_v1/raw_llm/E04_RAW_LLM_4V_S1_v4_seed1_real/step_records.csv`
- `results/pilot/dissertation_pilot_v1/hybrid/E05_HYBRID_LLM_4V_S1_v4_seed1_real/step_records.csv`
- `results/pilot/dissertation_pilot_v1/hybrid_safety/E06_HYBRID_LLM_SAFETY_4V_S1_v4_seed1_real/step_records.csv`
- `results/pilot/dissertation_pilot_v1/raw_llm/E04_RAW_LLM_4V_S1_v4_seed1_real/events.jsonl`
- `results/pilot/dissertation_pilot_v1/hybrid/E05_HYBRID_LLM_4V_S1_v4_seed1_real/events.jsonl`
- `results/pilot/dissertation_pilot_v1/hybrid_safety/E06_HYBRID_LLM_SAFETY_4V_S1_v4_seed1_real/events.jsonl`
- `results/diagnostics/llm_parser_diagnostic/live_summary.json`
- `results/diagnostics/llm_parser_diagnostic/trace.json`

Important limitation:

- the pilot artifacts do not preserve per-request HTTP status, provider error body, or exception type/message for failed live calls
- therefore, the exact low-level failure cause cannot be reconstructed with full certainty from the current saved evidence

## 3. Failure Distribution

### 3.1 Aggregate counts

Live provider-bearing controllers in the canonical pilot:

| Controller | Live requests | Successful requests | Failed requests | Parser success | Fallback |
| --- | ---: | ---: | ---: | ---: | ---: |
| Raw LLM | 53 | 7 | 46 | 7 | 46 |
| Hybrid | 53 | 0 | 53 | 0 | 53 |
| Hybrid + Safety | 53 | 0 | 53 | 0 | 53 |

Aggregate across live provider-bearing controllers:

- total live provider requests: `159`
- successful requests: `7`
- failed requests: `152`
- overall success rate: `4.40%`
- overall failure rate: `95.60%`

### 3.2 Failure classification table

Because the current artifacts do not retain HTTP status or exception details for failed calls, the only defensible classification is `Unknown` for the failed live requests.

| Classification | Count | Share |
| --- | ---: | ---: |
| Unknown | 152 | 100.00% |

No evidence in the saved artifacts supports a more specific split such as:

- `401`
- `403`
- `404`
- `408`
- `429`
- `500`
- `503`
- `Timeout`
- `Connection Error`
- `SSL`
- `DNS`
- `JSON Decode`
- `Provider Payload`
- `Parser Failure`

Those categories remain plausible hypotheses, but they are not provable from the preserved evidence.

## 4. Timeline

### 4.1 Raw LLM

Observed sequence:

- the first failure onset appears at simulation step `7`
- before that onset, the controller recorded `7` successful requests
- after that onset, the remaining `46` live requests failed and fell back

Interpretation:

- raw LLM did not fail immediately
- raw LLM had an early successful window, then became failure-dominant

### 4.2 Hybrid

Observed sequence:

- the first failure onset appears at simulation step `5`
- all `53` live requests ended in failure/fallback

Interpretation:

- hybrid never achieved a recorded successful live provider call in the pilot

### 4.3 Hybrid + Safety

Observed sequence:

- the first failure onset appears at simulation step `5`
- all `53` live requests ended in failure/fallback

Interpretation:

- hybrid + safety never achieved a recorded successful live provider call in the pilot

### 4.4 Temporal pattern summary

The failure pattern is not random noise in the pilot artifacts:

- raw LLM shows an early success window followed by sustained failure
- hybrid and hybrid + safety show failure from the first live-provider-bearing step
- the later controllers are strictly worse than the earlier controller in success rate

This is a strong indication of order/time-related provider reliability degradation or a shared runtime/provider instability that became more visible later in the pilot.

## 5. Cross-Controller Comparison

| Controller | Success rate | Failure rate | Observed behavior |
| --- | ---: | ---: | --- |
| Raw LLM | 13.21% | 86.79% | some early live successes, then failure-dominant |
| Hybrid | 0.00% | 100.00% | all live requests failed |
| Hybrid + Safety | 0.00% | 100.00% | all live requests failed |

Key comparison:

- `raw_llm` consumed part of the live-provider window successfully
- `hybrid` and `hybrid_safety` did not obtain any recorded successful live provider calls in this pilot
- the difference is consistent with a temporal or order confound

## 6. Research Bias Assessment

### Systematic Provider Bias

**Yes**

Reason:

- controller execution is sequential rather than randomized
- the earlier controller obtained some successful provider calls
- the later controllers obtained none
- the failure pattern is strongly time/order dependent in the saved artifacts

Important nuance:

- this does not prove that the provider itself is intrinsically biased against a specific controller
- it does show that the current execution order creates a real fairness risk for controller comparison

### Bias Interpretation

The most defensible interpretation is:

- there is a systematic reliability bias in the execution sequence
- the pilot order likely confounds controller comparison
- later controllers are disadvantaged if provider reliability degrades during the run

## 7. Threats To Validity

1. The artifacts do not preserve per-request HTTP status, provider error body, or exception type/message for the failed calls.
2. The pilot runs controllers sequentially, so time/order is confounded with controller identity.
3. The pilot uses a single scenario and a single seed.
4. The pilot is a readiness check, not a full statistical experiment.
5. Aggregate controller summaries hide call-by-call root causes.
6. The current logging schema is not sufficient to distinguish provider transport failure from payload/parse failure on failed calls.
7. Deterministic interface-rule decisions outside the control zone reduce the number of live provider interactions visible in the trace.
8. No retry policy is active in the pilot, so transient provider instability appears as hard failure.

## 8. Experiment Design Recommendation

Do not change the dissertation method yet.

For a fair formal experiment, the execution design should be improved in a non-behavioral way:

1. Randomize controller order across runs.
2. Interleave controllers across repeated batches instead of executing all requests for one controller before the next.
3. Repeat the pilot on multiple days or sessions to test time stability.
4. Record per-request provider status, exception type, and redacted error body in the artifacts.
5. Keep the same prompt, model, decision space, safety policy, and postprocessor logic.
6. Separate reliability diagnosis from performance comparison.

These changes would improve fairness and traceability without altering the research method itself.

## 9. Formal Experiment Readiness

### Can the formal experiment start now?

**Conditionally no**

Reason:

- the pilot evidence shows a strong order/time confound
- the saved artifacts are not detailed enough to diagnose failed provider calls at HTTP/exception level
- the current reliability pattern is uneven across controllers

### What is already ready

- the canonical pilot runner works
- the parser compatibility patch has been live revalidated
- the canonical pilot completed successfully
- the repository has usable engineering evidence

### What still needs improvement before a fairness-sensitive formal experiment

- randomized execution order
- better failure logging
- stronger separation between provider reliability diagnosis and dissertation evaluation

## 10. Final Summary

- total provider requests: `159`
- successful requests: `7`
- failed requests: `152`
- failure classification: `Unknown` for all failed calls, due insufficient per-request evidence
- failure timeline: early success window in `raw_llm`, then failure-dominant behavior; `hybrid` and `hybrid_safety` failed from the first live-provider-bearing step
- controller comparison: `raw_llm` outperformed the later controllers only in reliability, not in any formal dissertation metric
- systematic bias: `Yes`
- root cause confidence: `Low`

## 11. Evidence Path

- `results/pilot/dissertation_pilot_v1/`
- `results/diagnostics/llm_parser_diagnostic/`

