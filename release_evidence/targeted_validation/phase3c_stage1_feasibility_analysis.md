# Phase 3C Stage 1 Final Feasibility Analysis

## Scope and evidence boundary

This is a read-only analysis of the completed deterministic Stage 1 evidence under `results/phase3c_closed_loop_waiting_divergence/`. No Gemini request, SUMO run, scenario change, seed addition, or raw-evidence change was made for this analysis. The preregistered gate remains unchanged.

## Simulation validity and retained evidence

All six copied Phase 3C run directories contain `summary.json`, `run_metadata.json`, `step_records.csv`, `events.jsonl`, `decision_records.jsonl`, and `phase3c_observer.json`. Each copied run records `departed=12`, `arrived=12`, `completion_rate=1.0`, `collision_count=0`, `safety_intervention_count=0`, `grant_timeout_count=0`, `status=completed`, and `termination_reason=ALL_VEHICLES_COMPLETED`.

The runtime's temporary `results/raw/` run ID did not encode the Phase 3C condition, leaving only three current raw directories for six condition/seed runs. The Phase 3C copied evidence directories are nevertheless distinct and each retain matching condition-specific `scenario_id`, route/departure metadata, decision records, and observer output. This temporary raw-directory collision is an engineering provenance limitation for any future extension, but it does not change the copied Stage 1 evidence or the gate calculation below. No repair is made in this read-only task.

## Preregistered state-emergence gate

Criterion A requires at least two eligible deterministic episodes in each condition. Criterion B requires at least two matched seeds for which the first eligible `HIGH_WAITING_PRESSURE` waiting contrast is strictly greater than the matched `MODERATE_WAITING_PRESSURE` contrast. An eligible epoch requires both a legal four-vehicle all-RIGHT candidate and a legal two-vehicle opposite-STRAIGHT candidate. The contrast is aggregate STRAIGHT waiting minus aggregate RIGHT waiting. Neither criterion uses traffic-performance values or Gemini outcomes.

| Condition | Seed 1 eligible / first contrast | Seed 2 eligible / first contrast | Seed 3 eligible / first contrast | Eligible count |
| --- | --- | --- | --- | ---: |
| `MODERATE_WAITING_PRESSURE` | yes / 12 s | yes / 6 s | yes / 15 s | 3 / 3 |
| `HIGH_WAITING_PRESSURE` | no / n.a. | yes / 19 s | no / n.a. | 1 / 3 |

| Matched seed | Moderate first contrast | High first contrast | `High > Moderate` |
| --- | ---: | ---: | --- |
| 1 | 12 s | n.a. | no comparable eligible pair |
| 2 | 6 s | 19 s | yes |
| 3 | 15 s | n.a. | no comparable eligible pair |

- Criterion A: **FAIL** (`HIGH_WAITING_PRESSURE` has 1/3, below 2/3).
- Criterion B: **FAIL** (one matched seed, below two).
- Overall `stage1_gate_passed`: **FALSE**.

## Waiting-pressure manipulation check (descriptive only)

These aggregate observer metrics are not substitutes for either preregistered gate condition. The observer computes waiting as each vehicle's maximum observed SUMO `waiting_time`, then reports per-episode mean, maximum, and sample SD.

| Condition / seed | Mean waiting (s) | Maximum waiting (s) | Waiting sample SD (s) |
| --- | ---: | ---: | ---: |
| Moderate 1 | 8.08 | 23 | 9.70 |
| Moderate 2 | 9.50 | 27 | 10.27 |
| Moderate 3 | 6.83 | 20 | 8.73 |
| High 1 | 8.58 | 23 | 7.76 |
| High 2 | 8.42 | 27 | 10.97 |
| High 3 | 7.42 | 21 | 7.13 |

Across seeds, mean waiting is 8.14 s in both conditions (rounded); mean episode maximum is 23.33 s for Moderate and 23.67 s for High. The direction is not consistent: High is larger for seeds 1 and 3 but smaller for seed 2 in mean waiting, while waiting SD is lower for High in seeds 1 and 3 and higher in seed 2. The manipulation check is therefore **MIXED**, not supported as a consistent waiting-pressure manipulation.

Per-approach mean waiting by seed is likewise mixed:

| Condition / seed | E | N | S | W |
| --- | ---: | ---: | ---: | ---: |
| Moderate 1 | 8.67 | 8.00 | 7.67 | 8.00 |
| Moderate 2 | 9.67 | 9.67 | 9.00 | 9.67 |
| Moderate 3 | 7.33 | 7.33 | 6.33 | 6.33 |
| High 1 | 10.33 | 7.33 | 6.67 | 10.00 |
| High 2 | 8.33 | 9.00 | 7.33 | 9.00 |
| High 3 | 9.00 | 7.00 | 5.67 | 8.00 |

## Interpretation and decision

Stage 1 demonstrates that all six deterministic simulations completed safely, but it does **not** demonstrate that the preregistered high-pressure release schedule reliably forms the required R4/S2 state or a consistent higher waiting contrast. The gate failure follows the preregistered state-emergence and manipulation-validity criteria, not any traffic-performance preference.

**Stage 2 authorisation: NO.** Gemini evaluation must not start. The Phase 3B1-R2 result remains a valid controlled offline behavioural probe: it had 5/5 valid Gemini decisions and an observed selection switch between 19 and 20 s in its fixed template. The Stage 1 failure does not overturn that result; it only shows that this particular closed-loop release-schedule manipulation did not reliably recreate the state needed to test it.

## Recommendation

**STOP_PHASE3_EXTENSION.** The current evidence does not justify outcome-driven tuning of departures, wave spacing, seeds, or scenarios. A future independent study would require a newly justified and separately preregistered manipulation based on a design-level mechanism, not a post hoc search for a Gemini divergence.
