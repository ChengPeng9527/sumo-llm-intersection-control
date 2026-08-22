# Final LaTeX Submission QA Report

## 1. Scope

This pass audited the LaTeX submission package in:

- `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_qa\root.tex`
- `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_qa\References.bib`
- `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_qa\figures\`

The goal was source-level submission QA and formatting integration only. No research claims, experimental values, controller semantics, or evidence boundaries were changed.

## 2. Files Changed

- `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_qa\root.tex`
- `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_qa\figures\figure_1_mean_waiting_time.png`
- `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_qa\figures\figure_2_mean_speed.png`
- `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_qa\figures\figure_3_provider_success_fallback.png`
- `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_qa\figures\figure_4_latency.png`

## 3. What Was Fixed

### 3.1 Content duplication and structure cleanup

- Removed literal `\n\n` artifacts from the related-work section.
- Removed a duplicated `Zhao et al.` paragraph.
- Removed a duplicated autonomous-driving LLM comparison sentence so it appears once only.
- Removed a duplicated `\section{Methodology}` heading.
- Normalized the figure references so the QA package uses the copied local figure assets.

### 3.2 Traceability wording

- Replaced the broken traceability sentence with a clean, grammatical version that preserves the evidence boundary:
  - request identity
  - provider attempt identity
  - provider success
  - parser success
  - fallback
  - intermediate decisions
  - final decisions

This keeps the post-hoc attribution interpretation separate from the retained formal evidence.

## 4. Citation and Bibliography Audit

### 4.1 Counts

- Unique citation keys in `root.tex`: 13
- BibTeX entries in `References.bib`: 13
- Missing citation keys: 0
- Unused BibTeX entries: 0

### 4.2 Coverage

The LaTeX bibliography covers the same 13 references already established in the dissertation evidence set:

- Alvarez Lopez et al. (SUMO)
- Cui et al. (LLM4AD)
- Dong et al. (LLM-based interactive decision-making)
- Dresner & Stone
- Driess et al. (PaLM-E)
- Hou et al. (DriveAgent)
- Huang et al. (LLM planning)
- Li et al. (survey)
- Ma et al. (LaMPilot)
- Safarov
- Wen et al. (DiLu)
- Xie et al. (DriveBench)
- Zhao et al. (cooperative intersection control)

No new references were added and no unverified metadata was introduced.

## 5. Figure Audit

All four figure assets referenced by the QA LaTeX root are present:

- `figure_1_mean_waiting_time.png`
- `figure_2_mean_speed.png`
- `figure_3_provider_success_fallback.png`
- `figure_4_latency.png`

Figure paths resolve locally in the QA package.

## 6. Table / Cross-Reference Audit

- No broken cross-reference issues were detected in the source-level checks performed on the QA copy.
- No evidence was found that the formal/post-hoc boundary was altered.
- The retained formal evidence remains distinct from the attribution-oriented discussion.

## 7. Remaining Human Actions

The QA root still contains user-facing placeholders that require manual completion:

- `INSERT TITLE HERE` appears in the title block and cover/title area.
- `INSERT AUTHOR HERE` appears in the author metadata and title block.
- `AI_DISCLOSURE_HUMAN_REVIEW_REQUIRED` remains as a disclosure placeholder.

These are intentional human-fill items, not LaTeX defects.

## 8. Validation Results

### 8.1 Mechanical source checks

- The traceability paragraph is clean and readable.
- The duplicate structural content has been removed.
- The reference set is internally consistent.
- The copied figure assets are present.

### 8.2 Git diff / whitespace check

- `git diff --no-index --check` between the stable LaTeX source and the QA copy produced no whitespace-format warnings.
- The command returned a non-zero exit code only because the files intentionally differ.

### 8.3 Compiler availability

`latexmk`, `pdflatex`, and `bibtex` were not available on the local PATH, so a local LaTeX compile could not be completed.

Result: `LATEX_COMPILER_UNAVAILABLE`

## 9. Page-Count Impact

No page-count claim was measured locally because the compiler toolchain was unavailable.

## 10. Research-Content Integrity

The QA pass did not alter:

- experimental values
- controller semantics
- fallback semantics
- attribution boundaries
- figure data
- bibliography content

This remains a formatting and submission-readiness pass only.

## 11. Final Verdict

`FINAL_LATEX_QA_BLOCKED`

Reason:

- the source-level LaTeX QA checks are clean, but
- the local compiler toolchain is unavailable, so full compile/render validation could not be completed.

