# LaTeX Compilation Error Fix Report

## Summary
The `Missing $ inserted` errors in `root.tex` were caused by unescaped artifact names in ordinary prose. The main paper content was not changed; only LaTeX syntax was corrected.

## Fixed locations
- Line 99: replaced bare `formal_v2` and `formal_v4` in the abstract with `\texttt{formal\_v2}` and `\texttt{formal\_v4}`.
- Line 201: replaced bare `formal_v2` and `formal_v4` in Experimental Design prose with `\texttt{formal\_v2}` and `\texttt{formal\_v4}`.
- Line 201: also corrected the historical `formal_v2` trace mention so it is now `\texttt{formal\_v2}`.

## Root cause
- LaTeX treats `_` as a math-mode subscript character.
- In the abstract and Experimental Design prose, `formal_v2` and `formal_v4` were written as plain text rather than escaped text or typewriter text.
- The fix uses `\texttt{...}` with escaped underscores, which is appropriate for repository artifact names.

## Whole-file scan result
- No remaining bare `formal_v2` / `formal_v4` strings remain in ordinary prose.
- Remaining underscore characters in `root.tex` are in expected LaTeX-safe contexts such as:
  - escaped text tokens like `AI\_DISCLOSURE...`
  - table labels like `\label{tab:evidence_boundary}`
  - figure file names inside graphics commands
  - `\texttt{...}` artifact names

## Subfig warning
- The Overleaf warning about `Package subfig Warning: document class has bad definition of \endfigure` / `\endtable` is a known compatibility warning for the official `ieeeconf` template with `subfig`.
- This warning comes from the template/class combination, not from the content edits made in this task.
- The class file was not modified.

## Validation
- `git diff --check` passed.
- The requested source-level LaTeX syntax errors were fixed.

## Verdict
`LATEX_SOURCE_ERRORS_FIXED`
