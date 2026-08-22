# Final LaTeX Template Audit

## 1. Official document class
- Template entry point: `D:\Sumo\sumo_train\docs\dissertation\final_submission_latex\root.tex`
- Document class: `\documentclass[letterpaper,10pt,conference]{ieeeconf}`
- This is an IEEE conference-style class, so the template is already fixed to a compact two-column conference layout.

## 2. Font / column / margin semantics
- The template uses the class's built-in 10 pt conference typography.
- `\overrideIEEEmargins` is enabled, so the template controls its own margins.
- The layout is two-column and should be treated as fixed; it should not be altered to force the 10-page target.

## 3. Cover-page structure
- The template has a dedicated `titlepage` block with:
  - title placeholder
  - author placeholder
  - programme wording
  - declaration of own work
  - ethics statement placeholder
- This is suitable as a separate cover page and can sit outside the assessed 10-page body.

## 4. References mechanism
- The template ends with:
  - `\bibliographystyle{IEEEtran}`
  - `\bibliography{References}`
- References are therefore BibTeX-driven, not manually hard-coded in the body.

## 5. Appendix conventions
- The template includes an optional `APPENDIX` section note, but it is presented as guidance rather than an officially exempt page-count section.
- The safe reading is:
  - appendix content may exist in the template
  - the official page-count exemption is not established by the template alone
  - key assessed evidence should remain in the main paper or in separate supplementary materials

## 6. Bibliography mechanism
- `IEEEtran.bst` is the active bibliography style.
- The template expects a `References.bib` database in the same folder.
- Bibliography compilation is therefore standard BibTeX / IEEEtran, with no custom bibliography pipeline.

## 7. Required frontmatter
- The template already includes:
  - title page
  - declaration of own work
  - ethics statement placeholder
- It does not provide an automatic AI disclosure statement; that remains a human-review item.

## 8. Expected compilation command
- Preferred: `latexmk -pdf root.tex`
- Equivalent manual flow: `pdflatex root.tex` -> `bibtex root` -> `pdflatex root.tex` -> `pdflatex root.tex`
- If the local toolchain is unavailable, the same source can be uploaded directly to Overleaf.

## 9. Template settings that should not be changed just to force page count
- Do not change the document class away from `ieeeconf`.
- Do not reduce font size below the template's 10 pt conference setting.
- Do not change margins to manufacture extra room.
- Do not use negative spacing or hidden text tricks.
- Do not compress line spacing below the template's normal behavior.
- Do not alter the bibliography mechanism away from the template's BibTeX flow.

