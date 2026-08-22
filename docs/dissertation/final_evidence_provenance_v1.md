# Final Evidence Provenance v1

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

## Final evidence sources

### Valid 4V evidence

- Source batch: `results/formal_experiment/dissertation_formal_v2/`
- Use in dissertation: final 4V controller-by-scale comparisons
- Why valid: the usable 4V runs are fully observed, fully departed, fully arrived, and collision-free.

### Valid 8V evidence

- Source batch: `results/formal_experiment/dissertation_formal_v4/`
- Use in dissertation: final 8V controller-by-scale comparisons
- Why valid: the corrected 8V batch contains 12/12 completed runs with 8 observed / departed / arrived vehicles in every run and zero collisions.

## Excluded batches

### `formal_v2` nominal 8V runs

- Excluded because trace auditing showed that the four-vehicle default SUMO configuration was loaded instead of the generated 8V scenario configuration.
- The resulting traces only showed 4 observed / departed / arrived vehicles.
- Therefore the nominal 8V `formal_v2` traces are execution-invalid for 8V claims.

### `formal_v3`

- Excluded because two rule-based 8V runs did not complete all 8 arrivals within the 400-step termination window.
- The batch is useful as intermediate debugging evidence, but not as final dissertation evidence.

## Final dissertation rule

All final controller-by-scale comparisons must use:

- 4V: `formal_v2`
- 8V: `formal_v4`

No `formal_v2` nominal 8V statistics and no `formal_v3` results may appear in the final dissertation result tables.
