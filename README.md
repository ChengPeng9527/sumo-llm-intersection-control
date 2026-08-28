# SUMO Dissertation Project

This repository contains a structured LLM-assisted decision pipeline for unsignalised intersection control in SUMO. It separates state extraction, constrained planning, parsing, deterministic fallback, cooperative processing, safety verification, action execution, and decision provenance so that traffic outcomes and model-specific contribution can be assessed separately.

## Experimental Scope

Phase 1 is a complete-pipeline comparison of Rule-Based, Raw LLM, Hybrid, and Hybrid + Safety controllers. It retains 24 formal runs: 4V and corrected 8V conditions, three seeds each, and all four controllers. The LLM-assisted pipelines produced different pipeline-level traffic outcomes from the Rule-Based baseline, but provider failure and deterministic fallback prevent those outcomes from being independently attributed to successful LLM reasoning.

Phase 2 is a controlled attribution experiment. A deterministic cooperative comparator and Gemini receive identical deterministic safe and legal candidate groups. The frozen matrix covers S1--S4 at 8V, S3 at 12V, and S4 at 16V: 18 matched pairs and 36 independent episodes. Gemini made 93 logical decisions with 93/93 provider success, 93/93 parser success, zero fallback, 89/93 planner agreement, and four legal disagreements. These results do not establish general Gemini superiority over the deterministic planner.

## Repository Guide

- `src/` contains controllers, safety logic, LLM interfaces, analysis, and experiment code.
- `scripts/` contains supported utilities, including the presentation runner.
- `config/` contains project, scenario, prompt, and presentation configuration.
- `tests/` contains the pytest suite.
- `docs/` contains dissertation and research documentation.
- `release_evidence/` is the compact, supervisor-facing frozen evidence package for the principal dissertation claims.
- `results/` is the larger local raw-results tree and is intentionally excluded from normal Git tracking.

## Environment

The validated release environment used Python 3.10.11 and SUMO 1.27.0. Install the declared Python packages with:

```powershell
python -m pip install -r requirements.txt
```

Set `SUMO_HOME` to the root of a local SUMO installation before running SUMO-backed commands. The configuration loader uses `SUMO_HOME/bin/sumo.exe` and `SUMO_HOME/bin/sumo-gui.exe` when it is set; otherwise it preserves the local configured fallback.

```powershell
$env:SUMO_HOME = 'C:\path\to\sumo'
```

`requirements.txt` declares the runtime and test dependencies. `requirements-test.txt` retains the minimal pytest requirement. The release validation result was `164 passed`; it is a recorded baseline, not a promise for every machine.

## Credentials

Credentials are not included in this repository. Live provider experiments require the relevant environment variable, such as `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `CEREBRAS_API_KEY`; optional model settings are read from the corresponding provider/model configuration.

Supervisors do not need credentials or paid provider access to inspect the dissertation evidence. In particular, the frozen Gemini decision replay below makes zero external provider requests.

## Quick Validation

```powershell
python -m pytest
```

## Supported Local Commands

The following presentation commands require a local SUMO installation but no live provider credential.

```powershell
# Deterministic Phase 2 presentation.
python scripts/run_phase2_presentation.py --planner deterministic

# Frozen Gemini decision replay: zero external requests; not a new experiment.
python scripts/run_phase2_presentation.py --planner gemini-replay

# Offline provenance check for the retained S3 12V seed-1 disagreement.
python scripts/run_phase2_presentation.py --verify-disagreement

# Deterministic normal-versus-presentation integrity comparison.
python scripts/run_phase2_presentation.py --integrity-check
```

`gemini-replay` replays retained Phase 2 evidence rather than contacting Gemini. Before replaying, it validates frozen prompt hashes, candidate ordering, selected-candidate legality, paired candidate sets, and disagreement features. Any mismatch fails closed.

## Evidence and Reproducibility

The principal dissertation evidence can be inspected without rerunning live-provider formal experiments:

- [Evidence package guide](release_evidence/README.md) explains the retained Phase 1 and Phase 2 boundaries.
- [Claim traceability](release_evidence/CLAIM_TRACEABILITY.md) maps major claims to records.
- [Manifest](release_evidence/manifest.json) records source paths, copy status, hashes, and sizes.
- [Checksums](release_evidence/SHA256SUMS.txt) supports independent integrity verification.

Phase 1 traffic, logical-request provider, and action-trace evidence is under `release_evidence/phase1/`. Phase 2 matched-planner evidence is under `release_evidence/phase2/`. Frozen visualization route and replay assets are under `release_evidence/presentation/`.

The presentation layer is separate from formal experiments: its styling does not modify frozen network or controller semantics. Its deterministic normal-versus-presentation integrity validation recorded identical simulation behaviour. Frozen Gemini replay is a visualization of retained evidence, not additional experimental evidence.

## Limitations

`release_evidence/` is a compact frozen subset; the full local raw results are substantially larger and not all tracked in Git. Re-running live provider experiments depends on external credentials and services. Remote inference latency limits deployment interpretation, and local environment differences may require `SUMO_HOME` configuration.
