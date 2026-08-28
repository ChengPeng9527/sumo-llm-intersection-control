# Claim Traceability

`DIRECT` means a copied frozen artefact contains the stated field or record. `DERIVED_FROM_PACKAGED_EVIDENCE` means the package includes the selected records and a transparent projection or aggregation. No claim below depends on a newly executed experiment.

| Claim | Evidence file(s) | Relevant fields/records | Status |
| --- | --- | --- | --- |
| Phase 1 contains 24 retained formal runs | `phase1/retained_runs.json`; `phase1/source/dissertation_corrected_v1_summary.json` | `run_count`; selection rule; `formal_v2_4v_validity`; `formal_v4_8v_validity` | DERIVED_FROM_PACKAGED_EVIDENCE |
| Phase 1 uses four controllers, 4V and corrected 8V, and seeds 1--3 | `phase1/retained_runs.json` | `controller`, `vehicle_count`, and `seed` across 24 records | DERIVED_FROM_PACKAGED_EVIDENCE |
| Invalid nominal v2 8V evidence is excluded | `phase1/source/dissertation_corrected_v1_summary.json`; `phase1/retained_runs.json` | `formal_v2_8v_invalidity`; `excluded_boundary`; selection rule | DIRECT |
| Phase 1 completion is 100% with zero recorded collisions | `phase1/retained_runs.json` | all `completion_rate = 1.0`; all `collision_count = 0` | DERIVED_FROM_PACKAGED_EVIDENCE |
| Phase 1 operational waiting and mean speed | `phase1/retained_runs.json`; `phase1/source/dissertation_corrected_v1_summary.json` | per-run `mean_waiting_time` and `mean_speed`; source aggregates | DIRECT |
| Phase 1 logical provider requests, provider/parser successes, and fallback counts | `phase1/logical_provider_reliability.csv`; `phase1/retained_runs.json` | six controller-scale rows; per-run counters | DERIVED_FROM_PACKAGED_EVIDENCE |
| Phase 1 provider population is logical requests, not replicated vehicle rows | `README.md`; `phase1/logical_provider_reliability.csv` | `population`; evidence-boundary explanation | DERIVED_FROM_PACKAGED_EVIDENCE |
| Phase 1 cooperative interventions and safety overrides are zero | `phase1/retained_runs.json` | all `cooperative_interventions = 0`; all `safety_overrides = 0` | DERIVED_FROM_PACKAGED_EVIDENCE |
| Three Phase 1 assisted configurations have identical effective action traces in every retained scale-seed condition | `phase1/action_trace_projection.csv`; `phase1/action_trace_verification.json` | six `identical_effective_action_trace = true` comparisons; normalized hashes; 1,372 rows per controller | DERIVED_FROM_PACKAGED_EVIDENCE |
| Phase 2 has six conditions: S1--S4 8V, S3 12V, and S4 16V, with three seeds and two planners | `phase2/complete_matrix_summary/all_run_summaries.json`; `phase2/reports/phase2_formal_experiment_report.md` | scenario class, vehicle count, seed, planner; matrix table | DIRECT |
| Phase 2 contains 36 independent episodes and 18 matched pairs | `phase2/complete_matrix_summary/complete_matrix_summary.json`; `all_paired_comparisons.json` | `formal_run_count = 36`; `paired_condition_count = 18`; 18 comparison records | DIRECT |
| All 18 Phase 2 paired initial-demand signatures match | `phase2/complete_matrix_summary/all_paired_comparisons.json` | paired signature fields and validation status | DIRECT |
| Gemini made 93 logical requests with 93 provider successes, 93 parser successes, and zero fallback | `phase2/complete_matrix_summary/complete_matrix_summary.json`; `gemini_decision_summaries.json` | request, provider, parser, and fallback totals | DIRECT |
| Planner decisions comprise 89 agreements and four disagreements | `phase2/complete_matrix_summary/complete_matrix_summary.json`; `all_disagreements.json` | agreement/disagreement totals; four full records | DIRECT |
| Three repeated disagreements occurred in S3 12V | `phase2/complete_matrix_summary/all_disagreements.json` | S3 12V seed 1 at t=21, seed 2 at t=23, seed 3 at t=20 | DIRECT |
| S3 12V comparator chose a legal four-vehicle group and Gemini a legal two-vehicle opposite-straight group | `phase2/complete_matrix_summary/all_disagreements.json` | candidate lists/features and both selected candidate IDs for all three seeds | DIRECT |
| Phase 2 recorded zero collisions, safety interventions, and grant timeouts | `phase2/complete_matrix_summary/complete_matrix_summary.json`; `all_run_summaries.json` | three zero headline counts and per-run fields | DIRECT |
| Frozen S3 12V seed-1 replay uses five Gemini decisions without an external request | `presentation/replay/gemini/decision_records.jsonl`; `presentation/run_phase2_presentation.py` | five prompt hashes and candidate sets; `FrozenGeminiReplay` provider callable | DIRECT |
| Presentation disagreement validation fails closed on state, candidate, legality, or evidence mismatch | `presentation/run_phase2_presentation.py`; both replay `decision_records.jsonl` files | prompt hash, candidate-list equality, selected membership, paired-set and group-feature checks | DIRECT |
