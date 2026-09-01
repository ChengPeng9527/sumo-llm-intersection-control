# Phase 3B Repeatability Post-Run Evidence Audit

## Scope

This is a read-only audit of the independently executed supplementary
fixed-state repeatability study.  It does not change the preregistration, raw
records, frozen Phase 1/2 evidence, or the classification criteria.

## Evidence integrity

- `run_metadata.json` records `COMPLETED`, four registered conditions, five
  replicates per condition, and 20 experimental logical requests.
- The connectivity gate is retained separately and passed (`HTTP 200`).
- `phase3b_repeatability_results.csv` has 20 unique request IDs; the raw
  namespace has exactly one JSON provenance record for each ID.
- Provider success: 20/20; parser success: 20/20; fallback: 0/20; legal
  selection: 20/20; invalid: 0/20; `request_attempt_count`: 1 for every row.
- All records have the same candidate-set hash
  `5659FB6B05D6A8A8F399147DAD5F02B4E452809990728EA5867C2139D4CAD98E`
  and one identical recorded generation-configuration object.  Sanitised raw
  model output is retained in all 20 records.

### Provenance limitation

All 20 persisted `prompt_hash` fields are empty.  The runner used the same
formal prompt-construction code and preserved candidate-set/generation
configuration consistency, but the raw evidence cannot independently verify
the exact prompt text by hash.  This is a logging/provenance limitation, not
a reason to alter or rerun the completed study.

## Exact selection sequence

| Condition | Replicate sequence | R4 | S2 | OTHER_LEGAL | INVALID | Valid |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `W08` | R4, R4, R4, R4, R4 | 5 | 0 | 0 | 0 | 5 |
| `W19` | S2, S2, S2, S2, S2 | 0 | 5 | 0 | 0 | 5 |
| `W20` | S2, S2, S2, S2, S2 | 0 | 5 | 0 | 0 | 5 |
| `W24` | S2, S2, S2, S2, S2 | 0 | 5 | 0 | 0 | 5 |

There were no mixed selections within a condition and no OTHER_LEGAL or
invalid outputs.  This is a descriptive 5/5 pattern per condition, not a
population estimate or a model-internal threshold estimate.

## Preregistered classification

**`REPEATABLE_ORDERED_SHIFT`**.  The lowest registered waiting condition was
entirely R4; each higher tested condition was entirely S2.  Thus, in this
fixed candidate state, the observed Gemini selection distribution changes in
an ordered direction with the controlled waiting manipulation.

## Comparison with Phase3B1-R2

The single R2 observations were `8 -> R4`, `19 -> R4`, `20 -> S2`, and
`24 -> S2`.  Phase 3B supports the original result at W08, W20, and W24.  It
does **not** reproduce the original single W19 R4 outcome: all five W19
replicates selected S2.  Consequently, the earlier apparent 19--20 transition
is not repeated as a narrow transition interval.  The new evidence instead
locates the observed switch somewhere between W08 and W19 under this fixed
template.  No within-condition stochastic/mixed selection was observed here,
but five observations per condition cannot establish absence of stochasticity.

## Claim boundary

### Supported

- Gemini does not simply reproduce the deterministic comparator in all tested
  controlled states.
- Gemini selection is behaviourally sensitive to the controlled waiting
  manipulation in this fixed candidate state.
- The broad R4-at-W08 / S2-at-W19-or-higher pattern was repeatable in this
  20-request supplementary sample.

### Not supported

- A Gemini internal 20-second fairness threshold.
- Fairness optimisation, general planner superiority, or a traffic-performance
  improvement from the different selection.
- Broad population inference, generalisation to other candidate sets, or a
  causal psychological account of model behaviour.

### Still unknown

- The exact selection transition interval inside 8--19 s.
- How selection frequencies behave in other state geometries or with provider
  parameters explicitly fixed.
- The downstream consequence of S2 versus R4 from one identical SUMO state.

## Counterfactual decision

**`CONDITIONAL_PROCEED`**.  The repeatability evidence establishes a stable,
legal planner-choice difference worth studying.  Before any continuation is
authorised, implement and validate snapshot equivalence, controller-state
restoration, and one-epoch forced legal candidate provenance.  The future
question is bounded to: *from the same pre-decision state, what downstream
consequence follows from forcing the observed Gemini legal S2 selection versus
the deterministic legal R4 selection?*
