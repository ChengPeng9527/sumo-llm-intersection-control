# Phase 3C Preregistration: Closed-Loop Validation of Waiting-Sensitive Planner Divergence

## Registration boundary

This document is a design and preregistration record created before any Phase 3C Gemini request or SUMO run. It does not alter the frozen Phase 1, Phase 2, or Phase 3B1 evidence. Phase 3C is a new, separately labelled targeted validation. It is not a rerun of the formal Phase 2 matrix.

## Research question

When a naturally evolving S3 12V SUMO state contains both (a) the unique compatible four-vehicle all-RIGHT group preferred by the deterministic size-first comparator and (b) a legal two-vehicle opposite-STRAIGHT group with higher accumulated waiting, does Gemini select the smaller STRAIGHT group more often under higher naturally occurring waiting pressure?

The registered, testable hypothesis is:

> Higher naturally occurring waiting pressure on the smaller opposite-STRAIGHT candidate group will be associated with a greater probability of Gemini diverging from the deterministic size-first comparator.

This is not a claim about an internal model threshold, fairness understanding, optimisation, superiority, or a traffic benefit.

## Prior evidence motivating the challenge

Frozen Phase 2 has three S3 12V disagreements (seeds 1--3): the comparator selected the unique four-vehicle all-RIGHT candidate at rank 1 while Gemini selected a legal two-vehicle opposite-STRAIGHT candidate at rank 3. The Phase 3B1-R2 fixed offline probe reproduced an ordered selection switch: Gemini selected the four-RIGHT group at aggregate two-STRAIGHT waiting values 4, 8, and 19 s, then selected the two-STRAIGHT group at 20 and 24 s. That probe establishes a fixed-template behavioural association only; Phase 3C tests whether a comparable trade-off can emerge in independent closed-loop SUMO episodes.

## Reused frozen components

- Network/topology: existing S3 `S3_COOPERATIVE_OPPORTUNITY` intersection and 12V route cycle.
- Route semantics, conflict model, candidate generation, deterministic comparator, prompt construction, Gemini provider/model (`Gemini / gemini-3.6-flash`), parser, safety verifier, grant lifecycle, and candidate-to-`PROCEED`/`WAIT`/`FREE` execution interface: unchanged.
- Seeds: 1, 2, and 3, paired within each Phase 3C condition.
- Gemini evaluation: `STRICT_LLM_MODE=true`; no provider/parser/fallback episode is a valid LLM-effectiveness episode.

## Natural waiting-pressure manipulation

Waiting values are never injected into a decision state. They remain SUMO-observed `waiting_time` values in the formal privacy-minimised state. The only planned intervention is the **demand release schedule** used by the existing targeted-scenario generator: route cycle and vehicle count remain S3 12V, while the relative timing between the early opposite-STRAIGHT pair and the later all-RIGHT wave is changed before simulation starts.

The generator already derives departures from `depart_offsets`, `wave_spacing_seconds`, seed jitter, and per-approach monotonicity. Thus any waiting pressure must arise through departures, vehicle motion, previous grants, and safety-constrained execution, not by writing 19/20 s values into planner input.

### Challenge conditions

| Condition | Demand schedule | Intended state contrast | Acceptance observation, not a forced target |
| --- | --- | --- | --- |
| `MODERATE_WAITING_PRESSURE` | Existing S3 12V route cycle, offsets `[0, 0, 1, 1, 3, 3, 5, 5]`, `wave_spacing_seconds=9`, and existing seed jitter (`1`). | Baseline natural competition between an earlier STRAIGHT pair and the later RIGHT wave. | A decision epoch with both the two-STRAIGHT and four-RIGHT groups legal. |
| `HIGH_WAITING_PRESSURE` | Same S3 route cycle, offsets, vehicle count, jitter, and vehicle parameters, with `wave_spacing_seconds=11`. | The later all-RIGHT wave is released two seconds later relative to the initial opposite-STRAIGHT pair, giving the pair more opportunity to accumulate SUMO waiting before the competing RIGHT group arrives. | The same legal competition with a larger two-STRAIGHT aggregate waiting value than the matched moderate run is expected but not guaranteed. |

`HIGH_WAITING_PRESSURE` is a demand-timing condition, not an artificial state edit. If an eligible competition state does not occur, that is a valid state-emergence result and must not be repaired by changing the condition after the run.

## Experimental matrix and stopping rules

Preferred confirmatory matrix: `2 conditions x 2 planners x 3 seeds = 12` independent episodes.

| Planner | Episodes | Validity rule |
| --- | ---: | --- |
| `DETERMINISTIC_CANDIDATE` | 6 | Normal system-completion validation; it is not subject to a zero-LLM-decision requirement. |
| `GEMINI_CANDIDATE` | 6 | `STRICT_LLM_MODE=true`; valid only if `llm_valid_decisions >= 1`, `llm_failed_decisions == 0`, `fallback_decisions == 0`, and `llm_episode_valid == true`. |

For each condition/seed pair, deterministic and Gemini episodes must use an identical generated route/departure sequence and matching initial-demand signature. Runs remain independent after initialisation. A Gemini provider/parser/fallback failure must fail fast, persist its provenance, mark the episode invalid, and exclude it from LLM-effectiveness aggregation. Invalid records remain retained; there is no condition-level retry or replacement.

The six-episode contingency is `1 condition x 2 planners x 3 seeds`, using `HIGH_WAITING_PRESSURE`. It can establish only whether the high-pressure challenge yields observable divergence. It cannot test the registered pressure contrast, so it is a feasibility pilot rather than a substitute confirmatory test of the primary hypothesis.

## Preregistered measurements and analysis

### Stage 1 state-emergence feasibility gate

Before any Gemini episode, Stage 1 uses only the six deterministic episodes. The gate passes only when (1) at least two of three deterministic episodes in **each** condition contain at least one eligible trade-off epoch, and (2) at least two matched seeds have a strictly larger first-eligible two-STRAIGHT-minus-four-RIGHT aggregate waiting contrast in `HIGH_WAITING_PRESSURE` than in `MODERATE_WAITING_PRESSURE`. No Gemini selection, traffic-performance comparison, or hypothetical model outcome is used by this gate. The gate has no fixed 19/20 s target.

### Level 1: state emergence

For every decision epoch, retain candidate count, candidate IDs, group size, group aggregate/max waiting, movement composition, and privacy-minimised vehicle waiting/ETA/distance. Define an **eligible trade-off epoch** as an epoch in which the candidate set includes both the unique four-vehicle all-RIGHT candidate and a legal two-vehicle opposite-STRAIGHT candidate. Record the first eligible epoch in each independent run and the observed waiting contrast there. Do not assume the state exists merely because it existed offline.

### Level 2: planner divergence

At an eligible epoch, report deterministic candidate/rank, Gemini candidate/rank, selected group sizes, movement composition, agreement/disagreement, provider/parser/fallback state, selection legality, and latency. The registered structural comparison is four-RIGHT rank 1 versus two-STRAIGHT rank 3. Later states after independent planners have diverged are not treated as shared counterfactual states.

### Level 3: system consequence

For each independent completed episode, report completion rate, departed/arrived, throughput, mean/maximum waiting, mean speed, duration, collisions, safety interventions, and grant timeouts. Where a valid paired condition contains a divergence, describe paired outcomes without causal or superiority claims. If state is absent, planners agree, or trajectories diverge but outcomes are similar, report that outcome directly.

No inferential statistics are preregistered for three seeds per condition. Results are descriptive paired evidence.

## Interpretation guardrails

| Observation | Permitted interpretation |
| --- | --- |
| Eligible state absent | The chosen demand schedule did not produce the intended observable trade-off in that episode. |
| Eligible state present, agreement | The state was available but did not yield a recorded selection divergence. |
| Eligible state present, divergence, similar traffic outcomes | A local legal preference difference was observed without a material descriptive system difference in this small sample. |
| Eligible state present, divergence, different traffic outcomes | A paired closed-loop outcome difference was observed under this condition; it is not evidence of general superiority, fairness improvement, or causal model mechanism. |

## Integrity and provider-risk controls

- No prompt, parser, comparator, candidate, safety, model, or controller-semantic change is permitted during Phase 3C execution.
- Output must be under a new `results/phase3c_closed_loop_waiting_divergence/` root and new targeted-validation evidence files. Frozen Phase 1/2/3B1 paths are read-only inputs.
- The current provider risk is non-trivial: prior Codex-environment requests had `WinError 10060`, while manual PowerShell R2 achieved 5/5 valid requests. Execute only from the verified manual environment after a bounded connectivity gate, and keep the connectivity call outside the experimental logical-request count.
- Frozen Phase 2 S3 12V averaged five Gemini decision epochs per Gemini episode. The 12-episode matrix therefore expects approximately 30 Gemini logical requests; the six-episode contingency expects approximately 15. Historical mean per-request latency was about 7.7 s (R2 about 7.2 s), implying roughly 3.6--3.9 minutes versus 1.8--1.9 minutes of serial provider latency alone, before SUMO/setup and any fail-fast termination.
