# Phase 8 Report

## Objective

Aggregate raw run artifacts into analyzable summaries and figures.

## Files Changed

- `src/analysis/aggregate_results.py`
- `src/analysis/statistical_analysis.py`
- `src/analysis/generate_figures.py`
- `analyze_metrics.py`

## Validation

- Added raw-run and summary-run aggregation helpers.
- Added controller comparison statistics and export support.
- Added figure generation for controller-level metric comparison.

## Notes

- The analysis path prefers per-run `step_records.csv` files under `results/raw/`.
- The summary script now separates summary rows from raw step records before plotting.

## Acceptance Status

PASS

