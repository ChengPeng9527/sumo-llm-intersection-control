# Final LaTeX Reference Restoration Report

## 1. Reference Counts

- Word v9 bibliography count: 13
- Original LaTeX bibliography count: 7
- Final LaTeX bibliography count: 13

## 2. Restored References

The following Word v9 references were restored into the final LaTeX source and/or re-cited in the body where they provide literature coverage:

- `AlvarezLopez2018` - SUMO methodology
- `Cui2024` - LLM4AD / autonomous driving benchmark
- `Dong2026` - LLM-based interactive decision-making for autonomous driving
- `Dresner2008` - autonomous intersection management
- `Driess2023` - PaLM-E / embodied multimodal planning
- `Hou2025` - DriveAgent / modular autonomous-driving pipeline
- `Huang2022` - language models as zero-shot planners
- `Li2024` - autonomous-driving survey
- `Ma2024` - LaMPilot / language-model programs for driving
- `Safarov2022` - unregulated junction baseline context
- `Wen2023` - DiLu / knowledge-driven autonomous driving
- `Xie2025` - DriveBench / reliability-oriented evaluation
- `Zhao2025` - cooperative unsignalised intersection control

## 3. Intentionally Omitted References

- None.

## 4. Citation Placement Changes

The restored citations were reintroduced in compact locations so that the 10-page body structure remains intact:

- Introduction / problem framing:
  - `\cite{AlvarezLopez2018,Dresner2008,Safarov2022}`
- Introduction / literature gap sentence:
  - `\cite{Huang2022,Driess2023,Wen2023,Li2024,Ma2024,Cui2024,Hou2025,Dong2026,Xie2025}`
- Chapter 2 / autonomous intersection and cooperative control:
  - `\cite{Dresner2008}`
  - `\cite{Safarov2022}`
  - `\cite{Zhao2025}`
- Chapter 2 / LLM planning and autonomous driving:
  - `\cite{Huang2022}`
  - `\cite{Driess2023}`
  - `\cite{Wen2023}`
  - `\cite{Li2024,Ma2024,Cui2024,Hou2025,Dong2026,Xie2025}`
- Chapter 2 / reliability and research gap:
  - `\cite{Xie2025}`
- Chapter 3 / system methodology:
  - `\cite{AlvarezLopez2018}`

## 5. BibTeX Metadata Issues

- No missing citation keys remain.
- No duplicate BibTeX entries remain.
- No unused BibTeX entries remain.
- The restored entries are intentionally compact and aligned with the Word v9 bibliography record.
- Remaining human-verification note: none required from the repository evidence available in this pass.

## 6. Literature Coverage Assessment

The final LaTeX source now covers the key literature chains required by the dissertation:

- Autonomous intersection management and cooperative control
- LLM planning / embodied reasoning
- LLM autonomous-driving pipelines and modular execution
- Reliability-oriented evaluation
- SUMO as the simulation methodology

This restores the literature backbone that was present in Word v9 while keeping the final 10-page paper structure compressed.

## 7. Estimated Page-Count Impact

The body impact is minor.

- Only citation markers and short citation-bearing phrases were restored.
- No long paragraphs were reintroduced.
- Bibliography length is unchanged in practical page-limit terms because references are excluded from the 10-page main-paper limit.

Estimated effect on the main body: negligible to small, well below one page.

## 8. Remaining HUMAN_VERIFY Items

- None identified from the local repository evidence used in this restoration pass.

## 9. Validation Summary

- `root.tex` citation keys all exist in `References.bib`.
- No duplicate BibTeX entries were detected.
- No unused BibTeX entries remain.
- `git diff --check` passed.
- Local LaTeX compiler availability check failed, so compilation could not be run.

## 10. Final Verdict

REFERENCE_RESTORATION_PASS

