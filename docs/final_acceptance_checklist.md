# Final Acceptance Checklist

## Reproducibility

- [ ] Scenario generation is deterministic for a fixed seed.
- [ ] Raw run artifacts are stored under `results/raw/<run_id>/`.
- [ ] Summary artifacts are stored under `results/summaries/`.

## Safety

- [ ] Safety verifier returns conflict flags and conflict types.
- [ ] Priority vehicle selection is deterministic and conservative.

## Analysis

- [ ] Aggregation reads raw run artifacts.
- [ ] Statistical summaries can be exported.
- [ ] Figures can be generated from summary rows.

## Traceability

- [ ] Phase reports are preserved under `docs/phases/`.
- [ ] Evidence templates are preserved under `docs/evidence/`.
- [ ] Legacy snapshot remains available under `archive/original_snapshot/`.

