# Research Traceability Matrix

> **HISTORICAL / SUPERSEDED RESEARCH-PLANNING STATUS RECORD**
>
> This five-RQ Phase 18 planning matrix predates the completed attribution-aware
> research framing and Phase 2 formal matrix. It is not the
> current claim/evidence mapping. Use
> [`docs/current_project_status.md`](../current_project_status.md) for current
> state and `release_evidence/CLAIM_TRACEABILITY.md` for the retained principal
> evidence map. The original planning record is preserved unchanged below.

| RQ | Hypothesis | Experiment | Metrics | Evidence | Expected Figure/Table | Results Section | Discussion Section |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RQ1 | Raw LLM is usable, but not reliable enough alone | Experiment A | completion rate, throughput, mean waiting time, parser success rate, decision latency | historical live LLM runs, Phase 18 smoke, Phase 18 live revalidation | controller comparison table, raw action distribution figure | Results: raw-vs-baseline comparison | Discussion: whether LLM output is usable without extra layers |
| RQ2 | Cooperative post-processing improves raw LLM behavior | Experiment B | postprocessor intervention rate, mean waiting time, raw-to-final agreement, final action distribution | Phase 18 pipeline tests, Phase 18 smoke, trace records | raw-vs-hybrid comparison table, decision-flow table | Results: cooperative effect | Discussion: whether cooperation reduces unnecessary waiting |
| RQ3 | Safety verification reduces risk but may add conservatism | Experiment C | safety override count/rate, collision count, TTC conflict count, waiting time | Phase 18 hybrid+safety code path, smoke evidence, trace records | safety override table, safety flow figure | Results: hybrid vs hybrid+safety | Discussion: safety-efficiency trade-off |
| RQ4 | Higher traffic complexity increases intervention pressure | Experiment D | throughput, completion rate, mean waiting time, intervention rates | 4/8/16 vehicle result sets, smoke evidence, scenario generator | scalability table, trend plot by vehicle count | Results: scaling analysis | Discussion: sensitivity to traffic load |
| RQ5 | Final decisions are altered by validation, cooperation, and safety | Experiment E | raw-to-final agreement, validated-to-postprocessed change rate, postprocessed-to-final change rate, deterministic intervention rate | decision traces, live revalidation trace, smoke traces | decision-flow Sankey or transition table | Results: decision-flow analysis | Discussion: where the LLM still matters |

## Coverage Notes

- Each RQ has at least one experiment family and at least one core metric.
- The matrix distinguishes current Phase 18 evidence from historical evidence.
- Formal experiments are still pending; the matrix is a specification, not a results claim.

## Evidence Placement Notes

### Historical Evidence

- Phase 17 contains historical real LLM evidence.
- The repository also contains historical 8-vehicle and 16-vehicle result directories under `results/raw/`.

### Current Phase 18 Evidence

- Phase 18 smoke validation.
- Phase 18 live revalidation with Groq.
- Phase 18 pipeline unit tests.

## Results / Discussion Mapping

- Results sections should report only the metrics actually observed.
- Discussion sections should explain why the observed changes occurred, with explicit references to raw, validated, postprocessed, and final decisions.
- Do not use a Discussion section to introduce unsupported novelty claims.
