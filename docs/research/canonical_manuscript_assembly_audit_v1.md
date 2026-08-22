# Canonical Manuscript Assembly Audit

## 1. Completed Mechanical Assembly
- Title page placeholder title was replaced with a canonical dissertation title.
- A live Word TOC field was inserted at the top of the manuscript.
- Chapter 3 request-configuration prose was normalised to the verified Groq / `openai/gpt-oss-20b` / 256-token / low-reasoning / 30 s / 0-retry form in the body.
- Chapter 4 was rewritten into a formal 4.2 / 4.3 structure with the corrected 4 × 2 × 3 experimental framing.
- Chapter 5 was converted from audit-style notes into formal results prose.
- Chapter 6 was converted from audit-style notes into formal discussion prose.
- Table 2 was simplified to seven columns and retains the same scientific values.
- Appendix C now carries the seed-level raw values used to assemble Table 2.
- Appendix E abbreviations were reduced to the substantive dissertation abbreviations only.
- Figure 3 was regenerated to exclude the rule-based controller and to show only the live LLM controller categories.
- The bibliography entries with broken punctuation were normalised mechanically.

## 2. Validation Results
- Paragraphs: `415`
- Tables: `10`
- Inline shapes: `5`
- `卤`: `0`
- `U+200B`: `0`
- `U+FEFF`: `0`
- `U+FFFD`: `0`
- `U+FFFE`: `0`
- unintended `。`: `0`
- `±` occurrences: `26`
- TOC field present in paragraph 1: `YES`
- Word `updateFields` flag present: `YES`
- Table 2 columns after cleanup: `7`
- Table 2 cells containing `±`: `26`

Table 2 `±` cells:
- `r0c3`, `r0c4`
- `r1c3`, `r1c4`, `r1c5`
- `r2c3`, `r2c4`, `r2c5`
- `r3c3`, `r3c4`, `r3c5`
- `r4c3`, `r4c4`, `r4c5`
- `r5c3`, `r5c4`, `r5c5`
- `r6c3`, `r6c4`, `r6c5`
- `r7c3`, `r7c4`, `r7c5`
- `r8c3`, `r8c4`, `r8c5`

## 3. Remaining User-Confirmation Items
- `Author`, `Supervisor`, and `Submission date` remain marked `NEEDS_USER_CONFIRMATION` on the title page because the repository does not provide authoritative values.

## 4. File Outputs
- Manuscript: `D:\Sumo\sumo_train\docs\dissertationull_draft_submission_v8.docx`
- Audit: `D:\Sumo\sumo_train\docsesearch\canonical_manuscript_assembly_audit_v1.md`

## 5. Verdict
CANONICAL_MANUSCRIPT_ASSEMBLY_PASS
