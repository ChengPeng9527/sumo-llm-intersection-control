# Attribution-Aware LLM Intersection Control in SUMO

This repository contains a structured LLM-assisted decision pipeline for unsignalised intersection control in SUMO. It separates state extraction, constrained planning, parsing, deterministic fallback, cooperative processing, safety verification, action execution, and decision provenance so that traffic outcomes and model-specific contribution can be assessed separately.

The central research problem is attribution: traffic produced by an
LLM-enabled pipeline must not be treated as evidence of LLM reasoning when
provider failure, parsing failure, deterministic fallback, candidate
filtering, or downstream safety logic may have produced the action.

## Headline Evidence

- **Formal Phase 1:** 24 retained exploratory pipeline-comparison runs. The
  LLM-enabled pipelines differed from the Rule-Based baseline, but low
  live-provider success and extensive fallback prevent independent attribution
  of those traffic differences to successful LLM reasoning.
- **Formal Phase 2:** 36 valid independent SUMO episodes in 18 matched planner
  pairs. Gemini produced 93/93 provider-successful and parser-successful
  decisions with zero fallback, 89 agreements with the deterministic
  comparator, and four different legal choices.
- **Fixed-state repeatability (post-hoc):** W08 selected the deterministic
  four-vehicle all-RIGHT group in 5/5 requests; W19, W20, and W24 selected the
  two-vehicle opposite-STRAIGHT group in 15/15 requests. This is a bounded
  aggregate-waiting association, not an internal threshold.
- **Same-state counterfactual (post-hoc):** in three historical S3-12V
  checkpoints, forcing the observed opposite-STRAIGHT choice once increased
  total waiting by a descriptive mean of 20.0 s relative to the four-vehicle
  all-RIGHT choice under the same deterministic continuation.
- **Directional stress (post-hoc):** three strict-valid matched pairs showed a
  conditional full-policy efficiency benefit. Gemini reduced total waiting by
  a descriptive mean of 9.6667 s and duration by 4.3333 s, while
  approach-level waiting imbalance worsened. The frozen classification is
  `EFFICIENCY_ONLY_BENEFIT`, not a fairness result.

These small-sample, simulation-specific findings do not establish general
Gemini superiority, a universal planner rule, statistical significance,
fairness optimisation, deployment readiness, or real-world safety.

## Experimental Scope

Phase 1 is a complete-pipeline comparison of Rule-Based, Raw LLM, Hybrid, and Hybrid + Safety controllers. It retains 24 formal runs: 4V and corrected 8V conditions, three seeds each, and all four controllers. The LLM-assisted pipelines produced different pipeline-level traffic outcomes from the Rule-Based baseline, but provider failure and deterministic fallback prevent those outcomes from being independently attributed to successful LLM reasoning.

Phase 2 is a controlled attribution experiment. A deterministic cooperative comparator and Gemini receive identical deterministic safe and legal candidate groups. The frozen matrix covers S1--S4 at 8V, S3 at 12V, and S4 at 16V: 18 matched pairs and 36 independent episodes. Gemini made 93 logical decisions with 93/93 provider success, 93/93 parser success, zero fallback, 89/93 planner agreement, and four legal disagreements. These results do not establish general Gemini superiority over the deterministic planner.

The separately labelled supplementary work refines two bounded questions:
when a strict-valid Gemini choice differs from the comparator, and what local
or full-policy consequence follows in the tested state. It does not enlarge or
replace the frozen formal matrix.

## Research Questions

1. How can live-LLM contribution be separated from fallback and downstream
   deterministic control?
2. Under what tested decision conditions does reliable Gemini selection differ
   from a deterministic legal-candidate comparator?
3. What closed-loop consequences follow from LLM-specific candidate choices,
   and when do the tested choices produce benefit or cost?

Current answers and evidence boundaries are maintained in
[`docs/current_project_status.md`](docs/current_project_status.md).

## Supervisor Quick Map

| Need | Start here |
|---|---|
| Current project and dissertation state | [Current project status](docs/current_project_status.md) |
| Architecture and formal method | [Phase 2 formal report](docs/research/phase2_formal_experiment_report.md) |
| Formal frozen evidence | [Evidence package guide](release_evidence/README.md) |
| Formal claim provenance | [Claim traceability](release_evidence/CLAIM_TRACEABILITY.md) |
| Supplementary Q2/Q3 synthesis | [Final supplementary synthesis](release_evidence/targeted_validation/final_supplementary_q2_q3_synthesis.md) |
| Decision/action provenance | [Action provenance audit](release_evidence/targeted_validation/action_provenance_and_decision_space_audit.md) |
| Fixed-state repeatability | [Repeatability audit](release_evidence/targeted_validation/phase3b_repeatability_postrun_audit.md) |
| Same-state counterfactual | [Counterfactual audit](release_evidence/targeted_validation/same_state_counterfactual_postrun_audit.md) |
| Directional stress | [Directional stress audit](release_evidence/targeted_validation/phase3_directional_service_imbalance_postrun_audit.md) |

## Repository Guide

- `src/` contains controllers, safety logic, LLM interfaces, analysis, and experiment code.
- `scripts/` contains supported utilities, including the presentation runner.
- `config/` contains project, scenario, prompt, and presentation configuration.
- `tests/` contains the pytest suite.
- `docs/` contains dissertation and research documentation.
- `release_evidence/` is the compact, supervisor-facing frozen evidence package for the principal dissertation claims.
- `results/` is the larger local raw-results tree and is intentionally excluded from normal Git tracking.

## Environment

The currently validated local environment uses Python 3.10.11, pytest 9.1.1,
and SUMO 1.27.0. Install the declared Python packages with:

```powershell
python -m pip install -r requirements.txt
```

Set `SUMO_HOME` to the root of a local SUMO installation before running SUMO-backed commands. The configuration loader uses `SUMO_HOME/bin/sumo.exe` and `SUMO_HOME/bin/sumo-gui.exe` when it is set; otherwise it preserves the local configured fallback.

```powershell
$env:SUMO_HOME = 'C:\path\to\sumo'
```

`requirements.txt` declares the runtime and test dependencies.
`requirements-test.txt` retains the minimal pytest requirement. The current
local validation result is `255 passed` (2026-09-02); it is not a promise for
every machine. The tagged supervisor-release baseline separately recorded
`164 passed`.

## Credentials

Credentials are not included in this repository. Live provider experiments require the relevant environment variable, such as `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `CEREBRAS_API_KEY`; optional model settings are read from the corresponding provider/model configuration.

Supervisors do not need credentials or paid provider access to inspect the dissertation evidence. In particular, the frozen Gemini decision replay below makes zero external provider requests.

## Quick Validation

```powershell
python -m pytest
```

## Supported Local Commands

Read-only or offline checks require no SUMO process and no provider request:

```powershell
# Full repository validation.
python -m pytest

# Validate the fixed-state repeatability request plan without contacting Gemini.
python scripts/run_phase3b_repeatability.py --validate-only

# Verify provenance for the retained S3 12V seed-1 disagreement.
python scripts/run_phase2_presentation.py --verify-disagreement
```

The following commands require a local SUMO installation but no live provider
credential:

```powershell
# Deterministic Phase 2 presentation.
python scripts/run_phase2_presentation.py --planner deterministic

# Frozen Gemini decision replay: zero external requests; not a new experiment.
python scripts/run_phase2_presentation.py --planner gemini-replay

# Deterministic normal-versus-presentation integrity comparison.
python scripts/run_phase2_presentation.py --integrity-check

# Technical checkpoint/restore equivalence validation.
python scripts/run_counterfactual_replay_equivalence.py

# Deterministic feasibility stage for the directional stress protocol.
python scripts/run_phase3_directional_service_imbalance.py --stage deterministic-feasibility
```

`gemini-replay` replays retained Phase 2 evidence rather than contacting
Gemini. Before replaying, it validates frozen prompt hashes, candidate
ordering, selected-candidate legality, paired candidate sets, and disagreement
features. Any mismatch fails closed.

The following research runners require `GEMINI_API_KEY`, explicit external-data
authorization, a reviewed protocol, and a new non-conflicting evidence
namespace. They must not be used to overwrite or silently replace frozen
evidence:

```powershell
# Frozen formal-matrix entrypoint; existing output causes a fail-closed stop.
python scripts/run_phase2_formal_matrix.py

# Twenty-request fixed-state repeatability protocol.
python scripts/run_phase3b_repeatability.py

# Strict-valid Gemini stage after a separately reviewed Stage 1 gate.
python scripts/run_phase3_directional_service_imbalance.py --stage gemini-evaluation --authorize-stage2
```

## Evidence and Reproducibility

The principal dissertation evidence can be inspected without rerunning live-provider formal experiments:

- [Evidence package guide](release_evidence/README.md) explains the retained Phase 1 and Phase 2 boundaries.
- [Claim traceability](release_evidence/CLAIM_TRACEABILITY.md) maps major claims to records.
- [Manifest](release_evidence/manifest.json) records source paths, copy status, hashes, and sizes.
- [Checksums](release_evidence/SHA256SUMS.txt) supports independent integrity verification.

Phase 1 traffic, logical-request provider, and action-trace evidence is under `release_evidence/phase1/`. Phase 2 matched-planner evidence is under `release_evidence/phase2/`. Frozen visualization route and replay assets are under `release_evidence/presentation/`.

The presentation layer is separate from formal experiments: its styling does not modify frozen network or controller semantics. Its deterministic normal-versus-presentation integrity validation recorded identical simulation behaviour. Frozen Gemini replay is a visualization of retained evidence, not additional experimental evidence.

Post-hoc supplementary preregistrations, compact CSV summaries, and post-run
audits are under `release_evidence/targeted_validation/`. Large raw SUMO
traces remain local under ignored `results/`; they must not be silently
replaced by summaries.

## Dissertation Status

The latest integrated dissertation candidate remains local and is deliberately
excluded from this supervisor-review GitHub snapshot. A current PDF has been
compiled separately, but its AI-use declaration still requires author and
programme-policy confirmation. Historical PDFs, extracted drafts, and ZIP
archives are not the current dissertation and are not published by this
release.

## Release Boundary

The formal supervisor baseline remains the immutable annotated tag
`v1.0-dissertation-supervisor-release`. The separately tagged
`v0.9-supervisor-review` snapshot adds strict-validity engineering,
supplementary infrastructure, and compact post-hoc evidence without changing
the frozen Phase 1 or Phase 2 evidence. It excludes the dissertation candidate,
raw `results/`, debug logs, credentials, temporary ZIP archives, and extracted
historical dissertation copies.

## Limitations

`release_evidence/` is a compact frozen subset; the full local raw results are substantially larger and not all tracked in Git. Re-running live provider experiments depends on external credentials and services. Remote inference latency limits deployment interpretation, and local environment differences may require `SUMO_HOME` configuration.
