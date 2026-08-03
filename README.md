# SUMO Dissertation Project

Design and Evaluation of a Safety-Constrained LLM-based Cooperative Decision Framework for Autonomous Intersection Management.

## Current Scope

- SUMO-based unsignalized four-way intersection.
- Deterministic baseline controller.
- Cooperative rule controller.
- LLM controller with mock and real modes.
- Deterministic safety verification layer.

## Status

This repository is currently organized for Milestone A:

- backup and audit
- configuration and security cleanup
- route compatibility correction
- unified logging and metrics
- safety verifier redesign
- reproducible scenario generation
- experiment runner scaffolding
- aggregation and evidence templates
- phase-by-phase traceability notes under `docs/phases/`
- evidence templates under `docs/evidence/`
- expandable 4/8/16-vehicle scenario generation
- optional LLM dry-run and real API testing

Real LLM API experiments are only enabled when `LLM_MODE=real` and the API key is configured.

## Requirements

- Windows
- SUMO installed under `D:/Sumo`
- Python environment with the packages listed in `requirements.txt`

## Configuration

Edit files in `config/`:

- `project_config.yaml`
- `experiment_matrix.yaml`
- `route_conflicts.yaml`
- `prompt_config.yaml`

Use `.env.example` as the template for local secrets.

## Smoke Tests

Run the baseline and cooperative debug scripts after configuration is complete.

## Notes

- Legacy scripts are kept for traceability.
- Generated results should be written under `results/`.
- Archived snapshots are stored under `archive/original_snapshot/`.
