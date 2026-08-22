# Overleaf Compile Fix Pass Report

## 1. Undefined Control Sequence Root Causes

The Overleaf errors were caused by text corruption introduced during prior content-restoration edits, not by research content changes.

Fixed root causes:

- Literal `\n\n` sequences were present in `root.tex` inside the Related Work section, which LaTeX interpreted as commands.
- One traceability sentence in Methodology was truncated and left an unterminated quoted clause.
- One duplicated Related Work paragraph remained after the autonomous-driving synthesis block.
- Figure paths initially pointed outside the self-contained package (`../figures/...`) instead of the package-local `figures/...` directory.

## 2. Exact Text Corruption Fixed

- Restored the Zhao et al. sentence in Related Work so it now reads as a normal academic paragraph with a real paragraph break.
- Restored the autonomous-driving literature synthesis so the section no longer concatenates two paragraphs or repeats the same sentence block.
- Fixed the Methodology traceability sentence so it now reads:
  - traceability can answer what happened inside the pipeline
  - traceability alone cannot establish whether the outcome would have changed if one stage had been absent
- Removed the stray truncated quotation mark at the end of that sentence.

## 3. Duplicate Prose Removed

- Removed the duplicated standalone sentence that repeated the autonomous-driving LLM literature summary immediately after the expanded synthesis paragraph.
- The remaining use of “descriptive rather than inferential” is intentional and appears in distinct sections, not as duplicated filler.

## 4. Figure Files Copied

The following frozen figures were copied into the self-contained LaTeX package:

- `docs/dissertation/final_submission_latex/figures/figure_1_mean_waiting_time.png`
- `docs/dissertation/final_submission_latex/figures/figure_2_mean_speed.png`
- `docs/dissertation/final_submission_latex/figures/figure_3_provider_success_fallback.png`
- `docs/dissertation/final_submission_latex/figures/figure_4_latency.png`

## 5. Figure Paths Corrected

`root.tex` now uses package-local paths:

- `figures/figure_1_mean_waiting_time.png`
- `figures/figure_2_mean_speed.png`
- `figures/figure_3_provider_success_fallback.png`
- `figures/figure_4_latency.png`

This makes the final_submission_latex directory portable as a standalone Overleaf upload.

## 6. Package Self-Containment Status

- `root.tex` references only files inside `final_submission_latex/` for the main document assets.
- `References.bib` remains in the same package.
- `ieeeconf.cls`, `.bst` files, logos, and figure assets are all present inside the package.
- The package is now self-contained for Overleaf upload.

## 7. Expected Remaining Warnings

Likely remaining warnings are template-level and should not block the final PDF:

- `subfig` / `ieeeconf.cls` compatibility warnings about `\endfigure` and `\endtable`
- possible float placement warnings because the document uses `figure*` / `table*` in IEEE two-column layout

These are expected and not part of the compile-breaking issues fixed in this pass.

## 8. Validation

- `git diff --check` passed.
- All figure references now point to package-local files.
- No literal `\n\n` artifacts remain in `root.tex`.
- No new experimental data, claims, or citations were introduced.

## 9. Final Verdict

OVERLEAF_COMPILE_FIX_READY_WITH_WARNINGS
