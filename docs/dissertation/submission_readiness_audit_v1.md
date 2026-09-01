# Submission Readiness Audit v1

> **HISTORICAL / SUPERSEDED STATUS AUDIT**
>
> This audit applies to an earlier Phase 18 manuscript path and does not state
> current repository or dissertation readiness. Use
> [`docs/current_project_status.md`](../current_project_status.md) for current
> state. The audit findings remain preserved as historical manuscript evidence.

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

## 1. Final manuscript path

- `docs/dissertation/full_draft_submission_v1.md`

## 2. Total word count

- Total words in final manuscript: `7281`

## 3. Chapter word counts

Section-block counts extracted from the markdown headings:

- Title Page (Placeholder): `30`
- Abstract: `152`
- Table of Contents (Placeholder): `13`
- 1 Introduction: `1046`
- 2 Literature Review: `1261`
- 3 Methodology / System Design: `524`
- 4 Experimental Design: `473`
- 5 Results: `1356`
- 6 Discussion: `904`
- 7 Limitations: `561`
- 8 Conclusion and Future Work: `543`
- References: `398`

## 4. Placeholders remaining

Only the following deliberate placeholders remain:

- Title Page (Placeholder)
- Table of Contents (Placeholder)
- title / author / supervisor / submission date fields

No other `TODO`, `TBD`, `CITATION NEEDED`, `placeholder`, or chapter-pointer text remains in the final manuscript.

## 5. Citation issues

- Missing in-text citations: `0`
- Unsupported citation placeholders in the final manuscript: `0`
- Duplicate reference entries: `0`
- Bibliographic incompleteness: `1`

The only bibliographic normalisation issue is the Dresner and Stone (2008) entry, where the local PDF archive did not expose a DOI/URL. That is a reference-formatting issue, not a citation failure.

## 6. Numerical inconsistencies

No scientific numerical inconsistencies were found in the final manuscript.

Key locked figures remain internally consistent across Results, Discussion, and Limitations:

- final 4V evidence: valid `formal_v2`
- final 8V evidence: corrected `formal_v4`
- invalid nominal `formal_v2` 8V: excluded
- `formal_v3`: excluded
- provider success in corrected final evidence: `4 / 2784`
- provider failure / fallback count: `2780 / 2784`
- fallback rate: about `99.86%`
- provider success rate: about `0.14%`

## 7. Evidence contamination issues

- `formal_v2` nominal 8V evidence is excluded
- `formal_v3` is excluded
- no final-draft sentence uses the invalid nominal 8V traces as usable evidence
- no final-draft sentence treats `formal_v3` as final evidence
- all 8V claims in the final manuscript refer to the corrected `formal_v4` evidence

## 8. Duplicated content

No harmful duplicate paragraphs were found.

There is deliberate thematic repetition across Discussion, Limitations, and Conclusion around:

- pipeline-level interpretation
- fallback-heavy provider reliability
- the distinction between pipeline behaviour and pure LLM behaviour

That repetition is appropriate for dissertation coherence and does not constitute accidental duplication.

## 9. Terminology inconsistencies

No blocking terminology inconsistencies remain.

The manuscript now consistently uses:

- `LLM-assisted pipeline`
- `pipeline behaviour`
- `fallback-heavy`
- `provider reliability`
- `formal_v2` valid 4V / `formal_v4` corrected 8V evidence

Minor terminology choices remain stylistic only, not substantive.

## 10. Figure/table gaps

- Results contains table-based presentation of the key evidence.
- No separate plotted figure files are embedded yet.
- Figure captions remain described in the prose, so Word formatting can still insert the final charts later if desired.

This is a formatting gap, not a scientific evidence gap.

## 11. Top 5 remaining weaknesses

1. Title page, author, supervisor, and submission-date fields still need manual completion.
2. The table of contents is still a placeholder and should be auto-generated in Word.
3. The bibliography contains one incomplete local citation entry (Dresner and Stone DOI/URL).
4. Figure artwork is not yet embedded as standalone graphics.
5. The manuscript is submission-ready in structure, but the final Word styling and house style still need to be applied.

## 12. Whether another experiment is needed

- Another experiment needed: `No`

The evidence boundary is already fixed and internally consistent. No new experiment is required for submission preparation.

## 13. Whether the manuscript is ready for Word formatting

- Ready for Word formatting: `Yes`

The manuscript is self-contained, the evidence boundary is stable, the citation chain is consistent, and no blocking scientific issue remains.

## 14. Estimated UK MSc dissertation quality band

- Estimated band: `Merit to low Distinction`
- Practical estimate: around `65-70`, with the final position depending on Word presentation and how strictly the examiner weighs the provider-reliability limitation.

## 15. Final Verdict

- `READY_FOR_WORD_FORMATTING`
