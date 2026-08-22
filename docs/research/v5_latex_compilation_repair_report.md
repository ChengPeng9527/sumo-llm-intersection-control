# V5 LaTeX Compilation Repair Report

## 1. First Root Cause

The first compile-stopping defect was the `hyperref` package declaration in the preamble. The option block contained blank lines inside `\usepackage[...]`, which can trigger the `Runaway argument?` / `Paragraph ended before \@fileswith@ptions was complete` failure reported by Overleaf.

## 2. Cascade Errors Caused By It

That preamble failure was the likely source of several downstream diagnostics that should not be treated as independent root causes:

- `Missing \begin{document}`-style follow-on errors
- title-page line-break complaints that only became visible after the preamble was parsed
- later math-mode complaints reported around the experimental-matrix sentence

## 3. Exact Lines Modified

Modified in `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_v5\root.tex`:

- Preamble lines 41--46: normalized the `hyperref` option block so it is a single legal `\usepackage[...]` declaration.
- Title page lines 74--124: replaced standalone `\\` line breaks with legal paragraph breaks, removed the unsafe `\center` usage, and preserved the visual structure with `\par`, `\vspace`, and `\centering`.
- Experimental-design matrix line 641: converted the display-math block `\[ ... \]` into inline math `\(4 \times 2 \times 3 = 24\)` to avoid the reported math-mode cascade while keeping the same value.

`D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_v5\References.bib` was not changed in this pass.

## 4. Remaining Syntax Errors

Static checks after the repair found no remaining structural syntax problems in `root.tex`:

- unresolved refs: 0
- unmatched begin environments: 0
- unmatched end environments: 0
- `git diff --check`: clean

A full local LaTeX compile could not be run because the required compiler tools were unavailable on the machine.

## 5. Citation Status

- unique citation keys in `root.tex`: 13
- BibTeX entries in `References.bib`: 13
- missing citation keys: 0
- unused BibTeX entries: 0

## 6. Ref/Label Status

- labels present: `fig:architecture`, `fig:waiting`, `fig:speed`, `fig:provider`, `tab:controllers`, `tab:formal_traffic`, `tab:provider_reliability`, `tab:posthoc_attribution`, `sec:experimental_design`
- unresolved references: 0

## 7. Word Count / Subsection Count

Comparison against the prior v5 baseline:

- root.tex words before: 13,242
- root.tex words after: 13,251
- subsection count before: 28
- subsection count after: 28

The small word-count change comes from syntax-token normalization only and does not reflect any research-content reduction.

## 8. Whether Any Research Content Changed

No research content changed.

This pass only repaired LaTeX syntax and layout legality in the title page and preamble, plus one display-math formatting issue. Experimental values, controller semantics, evidence boundaries, and conclusions were left intact.

## 9. Final Verdict

`LATEX_SYNTAX_REPAIR_PASS_WITH_WARNINGS`

## 10. Warning Note

`LATEX_COMPILER_UNAVAILABLE`

Because the local LaTeX toolchain was not available, this pass is validated by static source checks rather than a fresh local Overleaf-equivalent compile.
