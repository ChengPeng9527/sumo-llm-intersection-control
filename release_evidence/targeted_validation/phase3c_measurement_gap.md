# Phase 3C Measurement and Logging Gap Assessment

## Audit scope

This assessment reads the current closed-loop runtime and frozen S3 12V artefacts only. It proposes no current code change and does not modify frozen evidence.

## Existing coverage

| Analysis layer | Existing retained data | Sufficiency |
| --- | --- | --- |
| State emergence | `decision_records.jsonl` contains simulation time/step, privacy-minimised vehicle inputs (waiting, speed, distance, ETA, movement), complete candidate set, and candidate features (group size, aggregate/max waiting, movement summary). | Sufficient to reconstruct whether a particular decision epoch contained the four-RIGHT versus two-STRAIGHT competition and its observed waiting contrast. |
| Planner divergence | The same record contains deterministic and Gemini candidate IDs, agreement/disagreement, raw model output, parser/provider/fallback provenance, selected candidate, prompt reconstruction data, latency, and grant source. | Sufficient for the decision-level comparison and strict-validity audit. |
| System consequence | `summary.json`, `run_metadata.json`, `events.jsonl`, `step_records.csv`, and completed grant records retain completion, throughput, mean/maximum waiting, speed, duration, collision, safety-intervention, and grant-timeout data. | Sufficient for existing aggregate closed-loop outcomes and grant lifecycle. |

## Gaps for a reproducible Phase 3C analysis

1. There is no explicit, standardised `eligible_tradeoff_epoch` flag or stored summary of the first epoch containing both target candidate classes. It can be reconstructed offline from candidate features, but adding a derived analysis row would reduce ambiguity.
2. The standard episode summary does not publish waiting standard deviation or per-approach waiting. `step_records.csv` contains per-step route/approach/wait fields, but a Phase 3C analysis would otherwise need to define its aggregation rule after data collection.
3. The standard summary does not publish a direct selected-versus-alternative waiting/size contrast for the target R4/S2 candidate pair. The underlying `decision_records.jsonl` does contain enough data to derive it.

## Minimum permitted measurement addition for future execution

Before any Phase 3C run, add a **derived observer/analysis output only**, without changing controller or scientific decision semantics. One JSONL/CSV row per decision epoch should contain:

- `eligible_tradeoff_epoch`
- `target_four_right_candidate_id`, `target_two_straight_candidate_id`
- group sizes, aggregate/max waiting, and movement compositions for both target groups
- selected candidate, deterministic rank, Gemini rank, agreement/disagreement, and strict-validity fields
- predeclared per-approach waiting aggregates and waiting sample SD, calculated from `step_records.csv` using a documented episode-level rule

The observer must read existing canonical records after execution. It must not alter the prompt, candidate set, planner decision, safety action, SUMO state, or frozen artefacts. This is a measurement/provenance addition, not a scientific-logic change.

## Decision

Current logging is sufficient for the three-layer question if analysis reconstructs state emergence from retained raw artefacts. The proposed observer is recommended before execution because it fixes the derivation and makes the first eligible trade-off and per-approach waiting summaries reproducible. It is not required to modify any Phase 1, Phase 2, or Phase 3B1 evidence.
