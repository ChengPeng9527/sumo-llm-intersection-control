# Offline Phase 2 Disagreement Analysis

## Scope and Boundary

This analysis reads the 18 retained Gemini planner `decision_records.jsonl`
files under `results/phase2_formal/`. Each record contains Gemini's saved
selection and the deterministic selection over the same recorded candidate set.
No SUMO episode or provider request was made. This is new descriptive analysis,
not a modification of frozen Phase 1/Phase 2 evidence and not a manifest-listed
release-evidence artefact.

There are 93 recorded Gemini decisions: 89 agreements and 4 disagreements.
The comparison is valid within each recorded Gemini decision state. It does not
treat later states from independent deterministic and Gemini closed-loop
episodes as shared counterfactual states after a divergence.

## All Disagreements

| Condition | Epoch time | Legal candidates | Deterministic selection | Gemini selection | Gemini rank | Recorded waiting evidence | ETA evidence |
| --- | ---: | ---: | --- | --- | ---: | --- | --- |
| S2 8V, seed 1 | 11 s | 10 | 2 LEFT vehicles; aggregate/max wait 3/2 s | 2 LEFT vehicles; aggregate/max wait 0/0 s | 3 | State waiting range 0--2 s | Gemini candidate minimum ETA 2.91 s; deterministic minimum ETA is non-finite/unrecorded |
| S3 12V, seed 1 | 21 s | 18 | unique 4 RIGHT group; aggregate/max wait 8/5 s | 2 STRAIGHT group; aggregate/max wait 20/10 s | 3 | State waiting range 0--10 s | Deterministic minimum ETA 74.21 s; Gemini value non-finite/unrecorded |
| S3 12V, seed 2 | 23 s | 18 | unique 4 RIGHT group; aggregate/max wait 18/7 s | 2 STRAIGHT group; aggregate/max wait 24/13 s | 3 | State waiting range 2--13 s | Both selected minimum-ETA values non-finite/unrecorded |
| S3 12V, seed 3 | 20 s | 18 | unique 4 RIGHT group; aggregate/max wait 4/4 s | 2 STRAIGHT group; aggregate/max wait 19/10 s | 3 | State waiting range 0--10 s | Deterministic minimum ETA 3.76 s; Gemini value non-finite/unrecorded |

`Gemini rank` is recomputed from the deterministic comparator ordering:
group size, aggregate waiting, maximum waiting, minimum ETA, then candidate ID.
The deterministic selected candidate is rank 1 in every record by construction.

## Descriptive Comparison

| Feature | Agreements (n=89) | Disagreements (n=4) |
| --- | ---: | ---: |
| Legal candidate count | mean 5.84; range 1--28 | mean 16.00; range 10--18 |
| Maximum legal group size | mean 1.93; range 1--4 | mean 3.50; range 2--4 |
| Deterministic selected group size | mean 1.93 | mean 3.50 |
| Gemini selected group size | mean 1.93 | exactly 2.00 |
| Gemini selected rank | exactly 1 | exactly 3 |
| State waiting range | mean 3.37 s; range 0--14 s | mean 8.25 s; range 2--11 s |

Candidate richness is associated with the four recorded disagreements, but it
is not sufficient: agreement records include up to 28 legal candidates and
maximum legal group size 4. The deterministic rank difference is descriptive of
the selection rule, not independent proof of a Gemini preference mechanism.

## Pattern Interpretation

### Recurring S3 12V Pattern

All three S3 12V seeds diverged once. Each state had 18 legal candidates and a
unique legal four-vehicle RIGHT-turn group selected by the size-first
deterministic comparator. Gemini selected a legal two-vehicle opposite-straight
group ranked third by that comparator. The Gemini-selected group had higher
aggregate and maximum waiting in all three records. This is a repeated,
scenario-specific selection pattern, not evidence of a general planner effect.

### Single S2 8V Disagreement

The S2 event is structurally different: ten legal candidates, three groups of
maximum size two, and both planners selected two-vehicle LEFT-turn groups.
Gemini selected a third-ranked group with lower recorded waiting than the
deterministic choice. It does not reproduce the S3 group-size or turn-composition
pattern.

### Features That Do and Do Not Distinguish the Records

- Descriptively distinguishing: high candidate counts, stronger group-size
  competition, Gemini rank 3 rather than rank 1, and the repeated S3 12V
  RIGHT-four versus STRAIGHT-two contrast.
- Not consistently distinguishing: route/turn composition across all four
  records, waiting direction across S2 versus S3, and ETA. Many selected ETA
  values are non-finite/unrecorded, so the saved records do not support an ETA
  explanation.

## Limitations and Follow-up

With four disagreements, this analysis supports no inferential statistic, ML
classifier, causal explanation, superiority claim, or shared-trajectory
counterfactual. If separately authorized as a new extension, the narrowest
replication target is S3 12V with two new seeds and both planners: four new
closed-loop episodes. That would test recurrence only; it would not establish
generalisation.
