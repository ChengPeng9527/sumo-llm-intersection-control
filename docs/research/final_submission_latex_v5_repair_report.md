# Final Submission LaTeX Repair Report

## Scope

This pass switched the working baseline away from `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_qa` and onto the expanded dissertation baseline extracted from `D:\Sumo\sumo_train\docs\dissertation\latex\final_submission_latex__4_.zip` into `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex_v5`.

The goal was to preserve the expanded正文 and repair only citation, bibliography, figure/table, cross-reference, and LaTeX submission issues.

## Baseline Comparison

| Metric | final_submission_latex_4 | final_submission_latex_qa | final_submission_latex_v5 |
|---|---:|---:|---:|
| root.tex words | 12,609 | 4,379 | 13,242 |
| root.tex characters | 93,325 | 30,252 | 97,471 |
| section count | 7 | 7 | 7 |
| subsection count | 28 | 13 | 28 |
| unique citation keys | 13 | 13 | 13 |
| BibTeX entries | 13 | 13 | 13 |
| figure environments | 1 | 3 | 4 |
| table environments | 1 | 6 | 4 |
| unresolved refs | 6 | 0 | 0 |
| authoritative compiled page count | not revalidated | not revalidated | not revalidated |

## What Was Repaired in v5

### Citation restoration

All old citation keys in the expanded baseline were mapped to the verified bibliography keys in `References.bib`.

Verified final citation set:
- `AlvarezLopez2018`
- `Dresner2008`
- `Safarov2022`
- `Zhao2025`
- `Huang2022`
- `Driess2023`
- `Wen2023`
- `Jin2023`
- `Cui2024`
- `Li2024`
- `Yang2024`
- `Hou2025`
- `Xie2025`

### Figure/table restoration

The expanded v5 baseline initially contained unresolved references to the formal traffic table, provider reliability table, post-hoc attribution table, and the related figure labels. These were restored in-source so that the expanded body now resolves all references.

Restored labels in v5:
- `fig:architecture`
- `tab:controllers`
- `sec:experimental_design`
- `tab:formal_traffic`
- `fig:waiting`
- `fig:speed`
- `tab:provider_reliability`
- `fig:provider`
- `tab:posthoc_attribution`

### Cross-reference status

- unresolved reference count in v5: 0
- missing citation keys in v5: 0
- unused BibTeX entries in v5: 0

## Content Preservation Check

The v5 baseline remains the expanded dissertation version, not the QA-shortened version.

Evidence from the source statistics:
- v5 has 13,242 word tokens vs 4,379 in QA.
- v5 has 28 subsections vs 13 in QA.
- v5 retains the full methodology, results, discussion, and limitations structure.
- the QA baseline was only used as a repair reference for structure and label recovery, not as the正文 source.

## Remaining Human Actions

The v5 root still contains manual placeholders that require human completion:

- `INSERT TITLE HERE`
- `INSERT AUTHOR HERE`

These are intentional submission metadata placeholders, not content defects.

## Validation

- `git diff --check` on the final v5 source did not report whitespace defects.
- The comparison against the stable source still exits non-zero because the files differ intentionally.
- Local LaTeX compiler tools (`latexmk`, `pdflatex`, `bibtex`) were unavailable, so compile/render validation could not be completed.

Result: `LATEX_COMPILER_UNAVAILABLE`

## Page Count Note

A trusted compile-time page count could not be revalidated locally because the compiler toolchain was unavailable. The archived `root.pdf` bundled with the package was not treated as authoritative for final page-count judgment.

## Final Verdict

`EXPANDED_LATEX_REPAIRED_WITH_WARNINGS`

Reason:
- the expanded baseline was preserved,
- unresolved citations/references were repaired,
- the citation set is internally consistent,
- but full compile validation could not be completed locally.
