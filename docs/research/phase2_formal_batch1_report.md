# Phase 2 Step 9: First Formal Closed-Loop Batch

## Scope and frozen method

This report records the first formal Phase 2 closed-loop batch. The batch used the
frozen commit `951c8fec0dddccf88d0bb48f48261a517cded2db` on branch
`phase-2-complexity-experiments`, Google Gemini with model
`gemini-3.6-flash`, the existing candidate prompt, deterministic fallback,
deterministic safety verification, one planner request per decision epoch/grant,
grant persistence, and the 45-second grant timeout.

Exactly six independent SUMO episodes were run: deterministic and Gemini
episodes for S1, S3, and S4 at 8 vehicles and seed 1. No S2, additional seed,
12-vehicle, or 16-vehicle formal condition was run.

The repository was clean at the expected HEAD before the Step 9 orchestration
files were added. The formal output was isolated under
`results/phase2_formal/batch1_seed1/`; Step 7 pilot, Step 8 smoke, Phase 1, and
dissertation artifacts were not overwritten or modified.

## Formal run IDs and validity

1. `phase2_formal_batch1_s1_balanced_mixed_turn_v8_seed1_deterministic_candidate`
2. `phase2_formal_batch1_s1_balanced_mixed_turn_v8_seed1_gemini_candidate`
3. `phase2_formal_batch1_s3_cooperative_opportunity_v8_seed1_deterministic_candidate`
4. `phase2_formal_batch1_s3_cooperative_opportunity_v8_seed1_gemini_candidate`
5. `phase2_formal_batch1_s4_fairness_pressure_v8_seed1_deterministic_candidate`
6. `phase2_formal_batch1_s4_fairness_pressure_v8_seed1_gemini_candidate`

All six runs completed with 8 departed and 8 arrived vehicles. Every run has an
independent raw result directory and an independent formal copy. Hash comparison
of the five core raw and formal artifacts produced zero mismatches.

For each pair, both planners were passed the same generated demand object and
therefore the same scenario, routes, departures, seed-controlled variables,
SUMO configuration, network, and vehicle parameters. The recorded initial-demand
signatures match within all three pairs:

| Scenario | Deterministic/Gemini signature match |
| --- | --- |
| S1 Balanced Mixed-Turn | Yes |
| S3 Cooperative Opportunity | Yes |
| S4 Fairness Pressure | Yes |

The episodes were separate SUMO processes. Metrics in each row below came from
that planner's own closed-loop trajectory; no observer-run traffic metric is
used as causal planner evidence.

## Paired traffic and attribution results

Values are shown as deterministic / Gemini. Parenthesized deltas are Gemini
minus deterministic. Waiting and duration are seconds, and speed is metres per
second.

| Scenario | Completion | Throughput | Mean wait (delta) | Max wait | Mean speed (delta) | Duration (delta) | Collisions | Safety | Gemini fallback | Requests | Agree/disagree | Gemini tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| S1 | 1.00 / 1.00 | 8 / 8 | 10.500 / 10.500 (0.000) | 25.0 / 25.0 | 7.188 / 7.188 (0.000) | 74.0 / 74.0 (0.0) | 0 / 0 | 0 / 0 | 0 | 7 | 7 / 0 | 6,350 |
| S3 | 1.00 / 1.00 | 8 / 8 | 6.625 / 6.625 (0.000) | 14.0 / 14.0 | 7.803 / 7.803 (0.000) | 43.0 / 43.0 (0.0) | 0 / 0 | 0 / 0 | 0 | 4 | 4 / 0 | 7,087 |
| S4 | 1.00 / 1.00 | 8 / 8 | 5.750 / 5.750 (0.000) | 20.0 / 20.0 | 8.303 / 8.303 (0.000) | 43.0 / 43.0 (0.0) | 0 / 0 | 0 / 0 | 0 | 4 | 4 / 0 | 7,919 |

Completion-rate and throughput deltas were also zero for every pair. These equal
closed-loop metrics follow from complete candidate agreement in this batch; they
must not be interpreted as evidence that the planners are generally equivalent.

## Control and provider results

| Scenario | Decision epochs/grants per planner | Mean grant duration | Timeouts per planner | Gemini mean latency | Prompt/completion/total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| S1 | 7 / 7 | 8.714 / 8.714 s | 0 / 0 | 9,968.61 ms | 6,112 / 238 / 6,350 |
| S3 | 4 / 4 | 8.500 / 8.500 s | 0 / 0 | 1,779.46 ms | 6,885 / 202 / 7,087 |
| S4 | 4 / 4 | 8.750 / 8.750 s | 0 / 0 | 5,271.88 ms | 7,723 / 196 / 7,919 |

Across the three Gemini runs there were 15 requests, 15 provider successes, 15
parser successes, and zero fallbacks. Total usage was 20,720 prompt tokens, 636
completion tokens, and 21,356 tokens. Recorded request latency had a mean of
6,532.37 ms, a minimum of 1,176.11 ms, and a maximum of 18,356.98 ms.

There were zero collisions, zero deterministic safety interventions, and zero
grant timeouts in all six episodes. Fallback and safety fields remain separately
recorded even though neither mechanism activated in this batch.

## Decision disagreements

There were zero Gemini/comparator disagreements across all 15 Gemini decision
epochs. Consequently there are no disagreement cases to enumerate. No case was
filtered or cherry-picked; `disagreements.json` is an empty list.

## Provenance and reproducibility

All 15 Gemini decision records contain:

- privacy-minimised local vehicle inputs;
- candidate IDs and candidate features;
- deterministic comparator and Gemini selections;
- final selected candidate and selection source;
- non-empty Gemini response evidence and parser/fallback status;
- executed actions, safety outcome, and complete grant lifecycle;
- provider, model, request parameters, latency, and token counts; and
- prompt hash plus canonical prompt reconstruction data.

Provider/model validation was 15/15 for `Gemini` / `gemini-3.6-flash`.
Prompt hashes and non-empty reconstruction inputs were present for 15/15
decisions. The decisions can therefore be reconstructed from preserved evidence
without making another Gemini request. A credential-value scan of 76 Step 9
source and result files found zero matches; the API key was not printed, logged,
or persisted.

Structured batch evidence is stored in:

- `results/phase2_formal/batch1_seed1/run_manifest.json`
- `results/phase2_formal/batch1_seed1/run_summaries.json`
- `results/phase2_formal/batch1_seed1/run_summaries.csv`
- `results/phase2_formal/batch1_seed1/paired_comparison.json`
- `results/phase2_formal/batch1_seed1/paired_comparison.csv`
- `results/phase2_formal/batch1_seed1/disagreements.json`
- `results/phase2_formal/batch1_seed1/batch_summary.json`
- `results/phase2_formal/batch1_seed1/runs/`

## Retry and validation record

There were no invalidated or retried formal episodes. An initial process-launch
attempt was rejected by the execution approval boundary before Python started;
it made no provider request and created no result. After direct authorization,
the six-run batch was executed once. No valid result was rerun.

Preflight focused and directly affected tests passed: `26 passed`. Because Step 9
added source files, the complete suite was run once after all episodes and passed:
`161 passed`.

## First-batch gate

**Status: `FORMAL_BATCH_VALID`.**

All six episodes are methodologically valid, initial conditions match within
pairs, traffic metrics originate from independent planner-controlled episodes,
provenance is complete, all live requests and parses succeeded, no frozen-method
change was needed, and no overwrite or retry occurred.

Observed limitations are substantial but do not invalidate the pipeline:

- The batch contains one seed and three 8-vehicle conditions, so it cannot support
  significance testing or broad performance claims.
- Gemini agreed with the deterministic comparator on every decision. This batch
  validates the live closed-loop and attribution chain but supplies no evidence
  about behavior or performance when planner choices diverge.
- Provider latency was material and variable, although it did not cause a timeout
  or fallback in these runs.

Recommendation: proceed with the remaining preregistered matrix only after human
review of this gate. Do not change the prompt or weaken the deterministic
comparator merely to induce disagreement. The remaining seeds and targeted scale
conditions are needed to determine whether decision-discriminative cases occur;
the zero-disagreement result should be retained as formal evidence.
