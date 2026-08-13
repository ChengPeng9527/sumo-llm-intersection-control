# Canonical Prompt Selection Report

## 1. Objective

Design and compare three candidate prompts, then select one canonical prompt for the formal experiment.

This is a prompt-development task, not the formal experiment itself.

## 2. Prompt Development Principles

The prompt selection was constrained by the frozen dissertation method:

- LLM role: high-level cooperative decision recommendation only
- decision space: `PROCEED / WAIT / FREE`
- research objective: safe cooperative progress with reduced unnecessary waiting
- state-based reasoning only
- no leakage of rule-based answers, postprocessor outputs, or safety-verifier outputs

## 3. Candidate Prompts

### P1_BASELINE

Baseline prompt with minimal formatting and the frozen output contract.

### P2_STRUCTURED

Structured prompt with explicit sections for vehicle state, conflict information, policy hints, and output contract.

### P3_COOPERATIVE_OBJECTIVE

Structured prompt plus a high-level cooperative objective sentence.

## 4. Development Dataset

- `4` vehicles
- development seeds: `101`, `202`, `303`
- prompt-selection runs: `9`

The development batch used a counterbalanced order so that each prompt appeared in early, middle, and late positions across the three seeds.

### Counterbalanced order used

- Seed `101`: `P1_BASELINE -> P2_STRUCTURED -> P3_COOPERATIVE_OBJECTIVE`
- Seed `202`: `P2_STRUCTURED -> P3_COOPERATIVE_OBJECTIVE -> P1_BASELINE`
- Seed `303`: `P3_COOPERATIVE_OBJECTIVE -> P1_BASELINE -> P2_STRUCTURED`

## 5. Counterbalanced Execution

Each run was executed as an independent raw-LVM development run.

The run set was designed to avoid controller identity being confounded with provider time/order.

## 6. Evaluation Metrics

Prompt selection used four metric layers:

1. Contract reliability
2. Decision behaviour
3. System behaviour
4. Efficiency / cost

## 7. Reliability Results

| Prompt | Live requests | Success | Failure | Provider success rate | Parser success rate | Fallback rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P1_BASELINE | 198 | 2 | 196 | 1.0101% | 1.0101% | 98.9899% |
| P2_STRUCTURED | 198 | 0 | 198 | 0% | 0% | 100% |
| P3_COOPERATIVE_OBJECTIVE | 198 | 0 | 198 | 0% | 0% | 100% |

## 8. Decision Behaviour

| Prompt | PROCEED | WAIT | FREE | Comment |
| --- | ---: | ---: | ---: | --- |
| P1_BASELINE | 156 | 42 | 156 | Non-zero live decisions and stable overall distribution |
| P2_STRUCTURED | 156 | 42 | 156 | Fallback-dominant live behavior |
| P3_COOPERATIVE_OBJECTIVE | 156 | 42 | 156 | Fallback-dominant live behavior |

Interpretation:

- all prompts produced the same overall final action distribution in the development batch
- `P1_BASELINE` was the only prompt with non-zero live-provider success and parser success

## 9. System Behaviour

All three prompts achieved:

- `100%` completion rate
- identical mean waiting time of `7.25` steps

This means the selection was **not** driven by throughput alone.

## 10. Leakage Assessment

| Prompt | Leakage assessment |
| --- | --- |
| P1_BASELINE | No disallowed leakage detected |
| P2_STRUCTURED | No disallowed leakage detected |
| P3_COOPERATIVE_OBJECTIVE | No disallowed leakage detected |

The prompts differ only in instruction organization and objective wording.

## 11. Selection

**Selected canonical prompt: `P1_BASELINE`**

### Why

`P1_BASELINE` was selected because it was the only candidate with:

- non-zero live-provider success
- non-zero parser success
- identical completion and waiting-time performance relative to the other candidates
- the simplest reliable instruction structure

## 12. Rejected Alternatives

### P2_STRUCTURED

Rejected because it produced fallback-only live behavior in the development batch.

### P3_COOPERATIVE_OBJECTIVE

Rejected because it also produced fallback-only live behavior in the development batch.

## 13. Canonical Prompt

The canonical prompt is the frozen `P1_BASELINE` prompt documented in:

- `docs/research/canonical_prompt_specification.md`

## 14. Freeze Statement

The canonical prompt is now frozen for the formal experiment.

Any later prompt change requires rerunning all LLM-bearing formal experiment runs.

## 15. Threats to Validity

1. Development evidence is not a substitute for the formal experiment.
2. Provider reliability varied during the development batch.
3. The prompt selection result should not be interpreted as a traffic-performance claim.
4. The selected prompt is chosen for frozen-contract suitability, not for post-hoc tuning.

## 16. Final Verdict

**CANONICAL_PROMPT_SELECTED_AND_READY_TO_FREEZE**

## 17. Evidence Paths

- `results/prompt_development/canonical_prompt_selection_v1/`
- `docs/research/canonical_prompt_specification.md`
- `docs/research/formal_prompt_audit.md`

