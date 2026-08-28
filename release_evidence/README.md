# Compact Frozen Evidence Package

This directory is a compact, supervisor-facing subset of evidence already produced by the dissertation project. It is not a new experiment, and creating it did not call an external provider or change any scientific result. The substantially larger local raw `results/` tree remains excluded from normal Git tracking.

## Evidence boundaries

Phase 1 retains exactly 24 runs: the 12 valid 4V runs from `dissertation_formal_v2` and the 12 corrected 8V runs from `dissertation_formal_v4`. The nominal 8V records in `dissertation_formal_v2` observed only four vehicles and are excluded from retained traffic evidence. The copied `dissertation_corrected_v1_summary.json` documents that exclusion explicitly; its invalid nominal 8V section is boundary-audit evidence, not retained experiment evidence.

Phase 2 retains 36 independent closed-loop episodes across six scenario-scale conditions, three seeds, and two planners, forming 18 matched pairs. The compact matrix summaries and all four disagreement records are copied verbatim from the frozen formal result tree.

Provider reliability uses logical provider requests. These are not replicated vehicle-level trace rows: one provider response can appear in several vehicle records for the same simulation step. `phase1/logical_provider_reliability.csv` is derived from the retained per-run request counters, while `phase1/action_trace_projection.csv` projects only the fields needed to check executed-action equality.

## Inspecting the principal claims

- `phase1/retained_runs.json` lists all 24 retained runs and their traffic, provider, fallback, post-processing, and safety fields.
- `phase1/logical_provider_reliability.csv` contains the six controller-scale logical-request rows used by the dissertation reliability table.
- `phase1/action_trace_projection.csv` and `phase1/action_trace_verification.json` support the claim that Raw LLM, Hybrid, and Hybrid + Safety had identical effective actions in every retained scale-seed condition.
- `phase1/source/dissertation_corrected_v1_summary.json` preserves the source boundary audit and detailed source records.
- `phase2/complete_matrix_summary/complete_matrix_summary.json` contains the headline Phase 2 counts.
- `phase2/complete_matrix_summary/all_run_summaries.json` and `all_paired_comparisons.json` expose all 36 episode summaries and 18 matched comparisons.
- `phase2/complete_matrix_summary/all_disagreements.json` contains all four disagreements, including the three S3 12V records.
- `CLAIM_TRACEABILITY.md` maps each principal claim to packaged records.

## Frozen presentation replay

The presentation subset contains the S3 12V seed-1 route, generation provenance, deterministic and Gemini decision records, and portable SUMO configurations. The repository command remains:

```powershell
python scripts/run_phase2_presentation.py --planner gemini-replay
```

The script prefers `release_evidence/presentation/` and falls back to the original local evidence paths when the package is absent. Replay performs zero external provider requests. Prompt-hash equality, candidate ordering, legal-candidate membership, paired candidate-set equality, expected disagreement group sizes, and complete epoch consumption remain fail-closed checks.

## Provenance

Files copied from `results/`, `simulation/generated_routes/`, `config/presentation/`, `scripts/`, or `docs/research/` are verbatim and have equal original and packaged SHA-256 values in `manifest.json`. The following files are newly generated indexes or portable metadata, not experimental outputs:

- `phase1/retained_runs.json`
- `phase1/logical_provider_reliability.csv`
- `phase1/action_trace_projection.csv`
- `phase1/action_trace_verification.json`
- `presentation/generated_route/portable_simulation.sumocfg`
- `presentation/config/s3_v12_seed1_presentation.sumocfg`
- `README.md`
- `CLAIM_TRACEABILITY.md`
- `manifest.json`
- `SHA256SUMS.txt`

`manifest.json` records source paths, purposes, copy status, hashes, and sizes. `SHA256SUMS.txt` covers every package file except itself.
