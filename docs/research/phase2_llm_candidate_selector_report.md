# Phase 2 Step 5 LLM Candidate Selector Report

## Purpose

Step 5 adds an experimental high-level LLM selector for the safe passage groups produced by Step 3. It establishes attribution machinery for later experiments; it is not a formal experiment and makes no performance claim.

## Architecture and fair comparison

Both planners receive the same traffic-state snapshot and the exact same `candidate_groups` value. The LLM prompt preserves the deterministic Step 3 candidate order, while Step 4 ranking is recorded separately. Candidate features are derived once from the Step 4 scoring representation. The deterministic branch applies the frozen Step 4 lexicographic rule, while the LLM branch may select exactly one supplied candidate ID. Neither branch generates a separate candidate universe.

The selected candidate is converted through the existing `PROCEED / WAIT / FREE` interface. The existing deterministic safety verifier remains downstream and retains final authority.

## Privacy-minimised input contract

The LLM prompt includes only current local vehicle ID, incoming and outgoing edge, intended movement, waiting time, speed, time to intersection, and control-zone status. Candidate descriptions include candidate ID, vehicle IDs, movement summary, group size, aggregate and maximum waiting time, and minimum time to intersection.

The prompt excludes route IDs, origins, destinations, route history, and unrelated downstream navigation information.

## Output and fallback contract

The required output is exactly:

```json
{"selected_candidate_id":"<candidate_id>"}
```

Additional keys, malformed JSON, non-string or multiple selections, and unknown candidate IDs are rejected. Provider or parser failure uses the Step 4 deterministic comparator over the same candidate set. No additional fallback policy was introduced.

## Provenance

The existing decision trace and step-record schema now preserve the raw redacted LLM output, LLM candidate, deterministic candidate, agreement/disagreement, fallback candidate and reason, final candidate, selection source, candidate features, pre-safety actions, safety intervention, and final actions. Existing provider/model, success, parser, timing, and token diagnostics remain in use.

## Validation

- Focused Step 5 pytest: 10 passed.
- Directly affected regression pytest: 73 passed.
- Full pytest: 134 passed.

## Mock mechanisms

- M1 agreement: LLM and comparator selected `a|b`; no fallback.
- M2 legal disagreement: LLM selected `c`, comparator selected `a|b`; no fallback.
- M3 illegal candidate: rejected and replaced by comparator choice `a|b`.
- M4 provider failure: comparator fallback selected `a|b`.
- M5 safety intervention: LLM provenance remained `LLM_CANDIDATE`; a deterministic test guard changed `c` from `PROCEED` to `WAIT`, recorded separately as a safety intervention.

Across the two comparable mock LLM decisions there was one agreement and one disagreement, for an agreement rate of 0.5. Fallback outcomes were excluded from the comparable denominator.

## Live-provider smoke

Two minimal Groq requests were attempted with the existing fixed-provider configuration and model `openai/gpt-oss-20b`. The first established deterministic fallback behavior; the second printed only redacted diagnostic fields to classify the failure. Both were rejected by Cloudflare with HTTP 403, Error 1010 (`browser_signature_banned`). The provider explicitly marked the response non-retryable. No credentials or raw secret values were printed.

The selector recorded provider and parser failure, selected the Step 4 fallback candidate `a|b`, passed its actions through the safety verifier, and produced final actions `a=PROCEED`, `b=PROCEED`, `c=WAIT`. Therefore the live-provider request itself is blocked by the current execution environment, while failure handling and downstream execution were demonstrated.

## Limitations and deferred work

- The route conflict model remains intentionally conservative and route-based.
- No prompt tuning was performed to manufacture disagreement.
- No live model decision was available because the provider request was blocked before inference.
- Formal 8/12/16-vehicle experiments, statistical analysis, lane-level geometry, fairness extensions, and dissertation updates remain deferred.
