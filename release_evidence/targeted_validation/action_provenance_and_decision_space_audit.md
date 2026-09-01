# Action Provenance and Planner Decision-Space Audit

## Scope and evidence boundary

This read-and-trace audit describes the current formal Phase 2 candidate-selection path. It does not alter frozen Phase 1, Phase 2, Phase 3B1-R2, or Phase 3B evidence. No provider request or SUMO run was made for this audit.

The relevant retained behavioural evidence is: 93 valid Phase 2 Gemini decisions (89 agreements and 4 disagreements), the repeated S3-12V R4/S2 disagreement structure, and the fixed-state Phase 3B repeatability result. Phase 3B observed `R4` in all five W08 replicates and `S2` in all five W19, W20, and W24 replicates; it is therefore evidence about legal candidate selection under controlled state information, not direct action selection.

## Formal Phase 2 path

The production/formal control chain is:

`TraCI observation -> build_traffic_state -> CandidateGrantController.update -> build_safe_candidate_groups -> candidate-selection context/prompt -> Gemini or deterministic selection -> parser/fallback -> build_decisions_from_selection -> apply_interface_rule -> verify_decisions -> ActivePassageGrant lifecycle -> executed action trace`.

Key implementation points are:

| Stage | Code and fields | Role |
| --- | --- | --- |
| Local state | `src/controllers/decision_pipeline.py`, `build_traffic_state` | Supplies route and local traffic fields including `route_id`, `incoming_edge`, `outgoing_edge`, `movement`, `speed`, `distance_to_intersection`, `time_to_intersection`, `waiting_time`, and `inside_control_zone`. |
| Safe candidate construction | `src/controllers/candidate_runtime.py`, `CandidateGrantController`; route-conflict utilities | Produces only legal compatible candidate groups before either planner selects. |
| Prompt context | `src/llm/candidate_selector.py`, `build_candidate_selection_context` and `_candidate_feature` | Serializes privacy-minimised vehicle state and candidate features: IDs, group size, aggregate/max waiting, minimum ETA, and movement summary. |
| Formal Gemini request | `src/llm/candidate_selector.py`, `run_live_candidate_request`; `src/llm/prompt_builder.py`, `build_candidate_selection_prompt` | Requests exactly one supplied candidate ID. |
| Parse and fallback | `src/llm/response_parser.py`, `parse_candidate_selection_response`; `src/llm/candidate_selector.py`, `select_candidate_with_llm` | Accepts only a legal `selected_candidate_id`; provider/parser failure is recorded and uses the deterministic candidate as robustness fallback. |
| Comparator | `src/safety/cooperative_comparator.py`, `rank_candidate_groups` and `select_candidate_group` | Ranks candidates by group size, aggregate waiting, maximum waiting, minimum ETA, then ID, and selects rank 1. |
| Vehicle action mapping | `src/safety/cooperative_comparator.py`, `build_decisions_from_selection` | Maps selected in-zone vehicles to `PROCEED`, other in-zone vehicles to `WAIT`, and out-of-zone vehicles to `FREE`. |
| Interface and safety | `src/llm/postprocessor.py`, `apply_interface_rule`; `src/safety/safety_verifier.py`, `verify_decisions` | Deterministically enforces out-of-zone `FREE`; the final verifier can downgrade unsafe simultaneous `PROCEED` actions. |
| Grant and execution provenance | `src/controllers/candidate_runtime.py`, `ActivePassageGrant`, `_record_execution`, `_finish_active_grant` | Retains an active selected group until clearance or timeout and records intended/final actions and safety intervention state. |

`execute_llm_candidate_selector_pipeline` in `src/controllers/decision_pipeline.py` connects the formal selector to action construction, the interface rule, and final safety verification. The deterministic formal path uses the same later action/safety stages after comparator selection.

## Actual decision spaces

| Decision space | Definition | Who determines it |
| --- | --- | --- |
| LLM output space | One JSON object: `{"selected_candidate_id":"<candidate_id>"}`. | Gemini, after a valid provider response and parser result. |
| Legal candidate space | The supplied safe compatible candidate groups. | Deterministic route-conflict/compatibility and candidate-generation code. |
| Planner selection space | One legal candidate: Gemini selection when valid; deterministic rank-1 selection for comparator or fallback. | Gemini or deterministic comparator. |
| Final vehicle action space | Per vehicle `FREE`, `WAIT`, or `PROCEED` after mapping, interface rule, safety verification, and grant state. | Primarily deterministic execution and safety logic; Gemini is only an indirect influence through a valid selected candidate. |

The formal candidate prompt and `parse_candidate_selection_response` do **not** expose `FREE`, `WAIT`, or `PROCEED` as direct Gemini output vocabulary. Legacy/raw-action interfaces elsewhere in the repository do not change the provenance of the formal Phase 2 candidate-selection experiments.

## Final action provenance

| Final action | Direct LLM choice? | Indirect LLM influence? | Deterministic source | Safety influence | Grant influence |
| --- | --- | --- | --- | --- | --- |
| `FREE` | No | Only indirectly through the selected group; an out-of-zone vehicle remains `FREE` regardless. | `build_decisions_from_selection` assigns `FREE` outside the control zone; `apply_interface_rule` enforces it. | `verify_decisions` converts out-of-zone `PROCEED` to `FREE`. | Continues for out-of-zone vehicles while a grant is active. |
| `WAIT` | No | Yes. In-zone vehicles omitted from the valid selected group become `WAIT`. | Non-selected in-zone vehicles, no active grant/no candidate, and the post-timeout all-wait step. Deterministic fallback also selects a comparator group, leaving others waiting. | Can downgrade a requested `PROCEED` to `WAIT` when the final conflict/ETA check rejects coexistence. | Remains the default for non-granted in-zone vehicles during an active grant; timeout clears the grant before a new selection. |
| `PROCEED` | No | Yes. A valid selected candidate identifies all of its in-zone vehicles. | `build_decisions_from_selection` maps every selected group member to `PROCEED`. | Final authority: may downgrade unsafe simultaneous `PROCEED` to `WAIT`. | An `ActivePassageGrant` re-applies the selected group across control steps until its vehicles clear scope or the grant times out. |

Thus a candidate can contain multiple vehicles. At one decision epoch, its selected in-zone members receive intended `PROCEED`; legal vehicles belonging to another, unselected candidate receive `WAIT` unless they are outside the control zone, when they receive `FREE`. The final trace preserves `postprocessed_decision`, `final_decision`, and safety-intervention provenance, so intended candidate selection is distinguishable from executed action.

## Meaning of R4 and S2

In the retained S3-12V fixed decision-state template:

| Candidate | Candidate structure | Deterministic rank | Vehicle-action consequence at the epoch |
| --- | --- | --- |
| `R4` | A legal four-vehicle all-`RIGHT` candidate group. | Rank 1. | Its four in-zone members are intended to `PROCEED`; other in-zone vehicles are intended to `WAIT`, subject to final safety verification. |
| `S2` | A legal two-vehicle opposite-`STRAIGHT` candidate group. | Rank 3 in the retained template. | Its two in-zone members are intended to `PROCEED`; other in-zone vehicles are intended to `WAIT`, subject to final safety verification. |

`R4` and `S2` are labels for legal passage groups, not direct `PROCEED`/`WAIT` commands and not semantic claims about fairness or model reasoning.

## What Phase 3B tested

Phase 3B manipulated controlled waiting information in a fixed legal candidate state and observed the Gemini-selected candidate/group. Its independent variable was waiting information, and its dependent variable was legal candidate selection (`R4`, `S2`, or another legal candidate). The controlled structure retained the same candidate set while manipulating the equal waiting values of the two `S2` vehicles.

Accordingly, Phase 3B is a **`PROCEED` candidate-selection preference experiment**, not a direct `WAIT` action experiment. The repeatability result is `REPEATABLE_ORDERED_SHIFT`: W08 selected R4 in 5/5 valid replicates, while W19/W20/W24 selected S2 in 5/5 valid replicates. It supports behavioural sensitivity to this controlled waiting-state manipulation, but does not identify an internal threshold, fairness objective, or closed-loop benefit.

## Candidate factors audit

| Factor | Present in Gemini context? | Varied in historical disagreement? | Can isolate offline? | Scientific value | Main confound or limitation | Recommended test? |
| --- | --- | --- | --- | --- | --- |
| Aggregate waiting | Yes, per candidate. | Yes. | Yes. | High | Earlier one-shot R2 differed at W19; Phase 3B repeatability now establishes a distributional pattern, not an exact threshold. | No additional API calls now: `WAITING_SUFFICIENT`. |
| Individual waiting distribution | Yes, in local vehicle state; candidate features expose aggregate and maximum waiting. | Unknown as an independently isolated factor. | Yes. | High | Aggregate and maximum waiting are currently coupled in many naturally observed states. | Yes, next low-risk fixed-state factor. |
| Group size | Yes. | Yes: R4 has four vehicles and S2 two. | Only with a newly constructed matched legal template. | Medium-high | Strongly confounded with turn composition and the specific vehicles/routes in R4/S2. | Later, after a matched template is preregistered. |
| Turn composition | Yes, through movement summaries and local routes. | Yes. | Only with a symmetric matched legal template. | Medium-high | Confounded with group size, approach direction, and candidate legality. | Later. |
| ETA / arrival timing | Yes, as local `time_to_intersection` and candidate minimum ETA. | Mixed/uncertain. | Technically yes. | Low now | Historical records contain non-finite or incomplete ETA information; a clean manipulation is not yet established. | No. |
| Route/direction | Yes, via incoming/outgoing edge and movement. | Mixed. | Technically yes. | Medium | Direction, symmetry, and turn composition are entangled. | Later, only in a symmetric template. |
| Candidate rank/order | Rank is not a direct prompt field. Candidate list order is visible, but comparator rank is derived deterministically. | Yes in outcomes (R4 rank 1, S2 rank 3). | Not independently without changing visible candidate features/order. | Low | Rank is a derived comparator property, not an independently stated Gemini feature. | No standalone test. |
| Candidate count/richness | Yes, through the supplied list of candidate groups. | Yes: disagreements were richer on average, but agreements also occurred in rich states. | Yes, but changes the decision context. | Medium | Candidate count changes the prompt context and often legal structure together. | Later, if a matched template can be built. |
| Symmetry | Implicitly, through routes/movements/group composition. | Unknown as isolated factor. | Difficult. | Low-medium | No explicit symmetry field; changes usually also alter directions and legality. | No initial test. |
| Conflict structure | Indirectly: only pre-filtered legal groups and their movement/route summaries are supplied. | Yes across scenarios, not isolated. | Difficult. | Medium | Altering it changes legal candidate space, not merely a contextual feature. | No initial test. |

The Phase 2 offline audit also showed that the four disagreements had more legal candidates on average and selected rank-3 Gemini groups, but candidate richness alone did not distinguish them: agreeing decisions could also have up to 28 legal candidates. Repeated S3 disagreements associated higher aggregate and maximum waiting with Gemini's S2 choice, whereas the single S2-8V disagreement did not provide a common route/turn or waiting-direction explanation. These are descriptive constraints, not causal mechanism evidence.

## Decision and limitation

The next factor should be **individual waiting distribution at a fixed aggregate waiting value**. It preserves the existing S3-12V fixed-state template and directly tests whether the observed selection change tracks total candidate waiting, the maximum/imbalance seen in vehicle-level context, or both. A preregistered design must hold candidate legality, group size, route/turn composition, candidate list, generation configuration, and aggregate waiting constant while changing only the two S2 vehicles' distribution. It should retain all invalid requests without replacement.

No existing document was changed if its wording differed from the code; this audit is the provenance record for any later correction.
