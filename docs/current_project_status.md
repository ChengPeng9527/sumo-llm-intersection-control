# Current Project Status

> **AUTHORITATIVE CURRENT-STATE RECORD**
>
> This is the sole authoritative project-state record for this repository.
> It describes the current repository, research, evidence, and dissertation
> boundary. It does not replace frozen experiment reports or raw evidence.
> Historical status documents are retained for provenance and are listed below.

## Identity

- **PROJECT_ID:** `SUMO-LLM-INTERSECTION-CONTROL`
- **STATUS_AS_OF:** `2026-09-02`
- **CANONICAL_REPOSITORY:** `D:\Sumo\sumo_train`
- **BRANCH:** `phase-2-complexity-experiments`
- **VERIFIED_HEAD:** the commit containing this record; verify the checkout with
  `git rev-parse HEAD` and the supervisor-review snapshot with
  `git rev-list -n 1 v0.9-supervisor-review`
- **FORMAL_RELEASE_BASELINE:** annotated tag
  `v1.0-dissertation-supervisor-release`, which resolves to
  `9e3369bf4a02802178638e4656a8073c081ffc47` (`Prepare dissertation supervisor
  release`)
- **SUPERVISOR_REVIEW_RELEASE:** annotated tag `v0.9-supervisor-review`; it
  identifies this attribution-aware supplementary research snapshot after
  publication

## Project Goal

Evaluate an attribution-aware LLM-assisted controller for unsignalised SUMO
intersection control. The architecture constrains high-level model selection
with deterministic candidate construction, fallback, safety verification, and
provenance so that complete-pipeline traffic outcomes are not confused with an
independently demonstrated model contribution.

## Current Stage

The formal Phase 1 and Phase 2 studies are complete and frozen. The bounded
post-hoc supplementary programme is also complete and has the recorded stop
decision `STOP_ALL_SUPPLEMENTARY_EXPERIMENTS`. Current work is
human review of the separately retained dissertation candidate and its AI-use
declaration, not further experiment execution or method tuning.

## Completed

- Phase 1 retained formal traffic comparison: 24 runs, comprising valid 4V
  evidence and corrected 8V evidence, each across four controller pipelines
  and seeds 1--3.
- Phase 2 controlled attribution experiment: 36 valid independent SUMO
  episodes forming 18 matched planner pairs across S1--S4 8V, S3 12V, and S4
  16V.
- Phase 2 Gemini evidence: 93 logical requests, 93 provider successes, 93
  parser successes, zero fallback, 89 agreements, and four legal
  disagreements with the deterministic comparator.
- Full 93-decision provenance and planner-divergence audit.
- Fixed-state aggregate-waiting repeatability: W08 selected R4 in 5/5
  requests; W19, W20, and W24 selected S2 in 15/15 requests.
- Negative or limited supplementary probes for individual waiting
  distribution, matched turn composition, and group-size-by-waiting effects.
- Deterministic replay-equivalence validation at the frozen absolute tolerance
  `1e-6`, enabling the same-state branches.
- Same-state counterfactual across three historical S3-12V checkpoints: a
  one-time S2 intervention increased total waiting by a descriptive matched
  mean of 20.0 s relative to R4 under the same deterministic continuation.
- Directional 16V service-imbalance stress: three strict-valid matched pairs;
  Gemini served S2 18 s earlier, reduced total waiting by a descriptive mean
  of 9.6667 s and duration by 4.3333 s, but worsened approach-level
  imbalance. Frozen classification: `EFFICIENCY_ONLY_BENEFIT`.
- Strict LLM validity engineering: a valid decision requires provider success,
  parser success, and no fallback; invalid LLM episodes are retained but
  excluded from LLM-effectiveness aggregates.
- Reconstructed supervisor-facing dissertation candidate with static source,
  citation, label, and figure checks.
- Curated supervisor-review Git snapshot containing strict-validity code,
  supplementary infrastructure, compact evidence, and claim traceability;
  raw trajectories and the dissertation candidate remain local by policy.
- Current local validation: `255 passed` with Python 3.10.11 and pytest 9.1.1
  on 2026-09-02. The tagged release baseline separately recorded 164 tests.

## Final Research Question Answers

### RQ1: Attribution

Live-LLM contribution can be distinguished only when provider, parser,
fallback, candidate, intervention, and outcome provenance remain separate.
System completion is not LLM validity. Phase 1 supports pipeline-level
comparison; Phase 2 provides strict-valid attribution evidence.

### RQ2: Distinct Selection Conditions

Gemini produced different legal choices in bounded candidate-rich states with
competing group-size and waiting characteristics. In one fixed S3 template,
selection distribution changed repeatably with aggregate waiting: R4 at W08
and S2 at W19/W20/W24. This does not establish an internal waiting threshold,
fairness preference, general group-size rule, or model reasoning mechanism.

### RQ3: Closed-Loop Consequences

Consequences are conditional. A single historical S2 intervention was locally
less efficient than R4 in all three same-state branches. In a separately
preregistered directional stress, the complete Gemini policy produced a
bounded efficiency-only benefit in all three matched seeds while worsening
approach-level balance. Neither result establishes general planner superiority.

## In Progress

- No formal or supplementary experiment is running.
- The dissertation candidate is intentionally outside this GitHub snapshot.
- Human review of the candidate's AI-use declaration remains in progress.

## Blockers

- A current dissertation PDF has been compiled separately but is not part of
  this repository release.
- The AI-use declaration requires author confirmation against the applicable
  programme and submission policy before a dissertation release is published.

## Frozen Decisions

- Phase 1 traffic evidence retains 24 runs; nominal `formal_v2` 8V records
  are excluded because they did not provide valid eight-vehicle evidence.
- Phase 1 provider reliability uses logical provider requests, not replicated
  vehicle-level trace rows.
- Phase 1 reports complete-pipeline performance only; low provider success and
  deterministic fallback prevent independent attribution of traffic gains to
  successful live-LLM reasoning.
- Phase 2 uses deterministic mixed-turn conflict logic, safe candidate groups,
  a strong deterministic cooperative comparator, deterministic fallback, and
  final deterministic safety authority.
- The Phase 2 provider/model is frozen as Google Gemini / `gemini-3.6-flash`.
- A valid LLM decision requires provider success, parser success, and no
  fallback. Traffic completion cannot repair invalid LLM provenance.
- Phase 2 results are descriptive, bounded to the retained scenarios, scales,
  seeds, topology, and synchronous provider implementation. They do not prove
  planner superiority, equivalence, statistical significance, fairness
  improvement, general scalability, deployment readiness, or real-world
  safety.
- Supplementary evidence is post-hoc and is not merged into the formal matrix
  or used for formal statistical inference.
- The same-state study estimates one legal intervention followed by a shared
  deterministic policy; it is not a full-policy comparison.
- The directional result is `EFFICIENCY_ONLY_BENEFIT`; it is not a fairness
  or multi-domain benefit.
- The supplementary programme is stopped. Any new experiment requires a new
  explicit design, authorization, and evidence namespace.
- The release baseline tag is immutable unless the user explicitly directs a
  separate release process.

## Open Decisions

- Whether and when the current dissertation candidate is approved for a
  separate supervisor/submission release.
- Whether the AI-use declaration satisfies the current programme policy.

## Evidence Index

- `release_evidence/README.md`: compact evidence boundary and inspection guide.
- `release_evidence/CLAIM_TRACEABILITY.md`: principal-claim-to-record mapping.
- `release_evidence/manifest.json` and `release_evidence/SHA256SUMS.txt`:
  package inventory and integrity data. The 2026-08-30 inspection verified all
  40 manifest entries against their packaged SHA-256 values.
- `release_evidence/phase1/retained_runs.json` and
  `release_evidence/phase1/logical_provider_reliability.csv`: retained Phase 1
  traffic and logical-request evidence.
- `release_evidence/phase2/complete_matrix_summary/`: Phase 2 summaries,
  matched comparisons, decision summaries, and disagreement records.
- `docs/research/phase2_formal_experiment_report.md`: frozen Phase 2 matrix
  interpretation and limitations.
- `docs/research/formal_experiment_v2_execution_report.md`: historical Phase 1
  execution-source report; use together with the retained-evidence boundary,
  not as the sole current summary.
- `release_evidence/targeted_validation/final_supplementary_q2_q3_synthesis.md`:
  bounded post-hoc Q2/Q3 synthesis and final stop decision.
- `release_evidence/targeted_validation/phase3b_repeatability_postrun_audit.md`:
  fixed-state aggregate-waiting repeatability.
- `release_evidence/targeted_validation/same_state_counterfactual_postrun_audit.md`:
  three-seed same-state local consequence.
- `release_evidence/targeted_validation/phase3_directional_service_imbalance_postrun_audit.md`:
  three-seed strict-valid full-policy stress result.

## Authoritative Sources

- **Current project/research state:** this file,
  `docs/current_project_status.md`.
- **Repository orientation and supported local commands:** `README.md`.
- **Principal frozen evidence and claim provenance:** `release_evidence/`.
- **Formal release baseline:** Git commit
  `9e3369bf4a02802178638e4656a8073c081ffc47` and annotated tag
  `v1.0-dissertation-supervisor-release`.
- **Current supervisor-review research snapshot:** annotated tag
  `v0.9-supervisor-review` on this documentation and supplementary release.

## Historical Sources

- `docs/phases/phase_00_report.md` through `docs/phases/phase_18/`: historical
  development and validation reports.
- `docs/research/phase2_*` and related formal-experiment reports: frozen method,
  execution, pilot, and analysis records. They remain evidence at their stated
  scope; they are not current-state records.
- Earlier dissertation drafts, audits, and writing packages under
  `docs/dissertation/`: historical manuscript artefacts unless explicitly
  identified by the dissertation boundary below.

## Superseded Status Documents

The following records are preserved, but their branches, HEADs, test counts,
research questions, readiness conclusions, or recovery assumptions predate the
current Phase 1/Phase 2 evidence and release baseline. They must not be used to
infer current status:

- `docs/research/current_research_status.md`
- `docs/research/research_readiness_review.md`
- `docs/research/research_traceability_matrix.md`
- `docs/dissertation/writing_status.md`
- `docs/dissertation/submission_readiness_audit_v1.md`
- `docs/dissertation/supervisor_readiness_audit_v1.md`
- `docs/dissertation/final_presentation_audit_v1.md`
- `docs/research/repository_recovery_plan.md`

## Dissertation Source Boundary

- **User-supplied authoritative reconstruction export:**
  `docs/dissertation/SumoControl.zip`.
- **Verified extraction of that export:**
  `docs/dissertation/_old_report_extract/`; this is an immutable historical
  recovery baseline and should remain local.
- **Latest integrated local candidate:**
  `docs/dissertation/final_submission_candidate/root.tex` with its candidate
  assets and validation files.
- **Candidate publication status:** static validation passed and a current PDF
  was compiled separately, but neither the candidate nor that PDF is included
  in the supervisor-review GitHub snapshot while AI-use declaration review is
  unresolved.
- `docs/dissertation/final_submission_latex_v6/` and earlier versions are
  historical Git-resident manuscript states, not the latest candidate.

## Overleaf / Git Boundary

The local workspace contains the user-supplied source export and a reconstructed
candidate, but the live Overleaf workspace is not accessible or automatically
synchronised. Git can recover the formal baseline and the published compact
supervisor-review research snapshot; it cannot recover the excluded candidate
or any later Overleaf edits. Those dissertation states remain external to this
release.

## Known Limitations

- All traffic evidence is SUMO-based and uses one intersection topology.
- Formal and supplementary samples are small and primarily descriptive.
- Fixed-state probes do not reveal Gemini's internal reasoning or a universal
  decision function.
- Same-state counterfactual evidence covers three historical checkpoints and
  one forced legal action per branch.
- The directional result covers one post-hoc stress condition and three seeds;
  provider latency/cost and external availability remain deployment barriers.
- Zero recorded collisions do not establish general or real-world safety.
- The full raw results tree is intentionally not normal Git-tracked content;
  `release_evidence/` is a compact retained package, not a substitute for every
  local raw artefact.
- Local working-tree changes are not release-baseline evidence until reviewed
  and explicitly incorporated through a separate user-authorized process.

## Next Action

**Obtain author/programme-policy confirmation of the dissertation AI-use
declaration, then review and publish the final dissertation as a separate
release without altering the frozen research evidence.**

## Last Verification

- Repository root: `D:/Sumo/sumo_train`
- Branch: `phase-2-complexity-experiments`
- Pre-release formal baseline: `9e3369bf4a02802178638e4656a8073c081ffc47`
- Supervisor-review release identity: `v0.9-supervisor-review` on the commit
  containing this record; verify its exact SHA with Git.
- Current local test result: `255 passed` with Python 3.10.11 / pytest 9.1.1.
- Excluded local material may remain in the working tree, including the
  dissertation candidate, raw results, historical reconstruction artefacts,
  and diagnostic files. It is not part of this release.
- Provider/API calls: zero.
- SUMO runs: zero.
