# Final Submission QA Report

## 1. Files Modified
- `D:\Sumo\sumo_train\docs\dissertation\full_draft_submission_v10.docx`
- `D:\Sumo\sumo_train\docs\research\final_submission_qa_report.md`

## 2. Chapter 4 QA
- Fixed the experimental-factor statement so the three factors are stated explicitly: controller architecture, vehicle scale, and random seed.
- Fixed the intended design statement so it reads as `4 controller architectures x 2 vehicle scales x 3 seeds = 24 runs`.
- Tightened the evidence-boundary wording so the retained formal evidence is clearly the valid 4V formal_v2 batch plus the corrected 8V formal_v4 batch.
- Added an explicit statement that the post-hoc Gemini/fallback diagnostics are supplementary and not part of the original formal matrix.
- Confirmed the controller descriptions remain aligned with Chapter 3.

## 3. Chapter 5 QA
- Cleaned the corrupted mean +/- SD glyphs and related hidden Unicode artifacts.
- Corrected the malformed metric equations for Completion Rate and Provider Success Rate.
- Removed the stray Chinese full stop from the throughput description.
- Softened interpretation language so the results read as pipeline-level observations under the evaluated conditions rather than direct LLM-causation claims.
- Confirmed the four retained figures and four retained tables remain tied to the frozen formal evidence boundary.

## 4. Chapter 6 Attribution Table QA
- Verified the two post-hoc attribution tables remain in Chapter 6 and are clearly labelled as supplementary, post-hoc evidence.
- Confirmed Table 5 states the 4V seed1 comparison between rule-based, fallback-only, and reliable Gemini.
- Confirmed Table 6 states the 132/132 and 39/39 agreement summaries and does not claim global policy equivalence.
- Confirmed the surrounding prose keeps the post-hoc diagnostic evidence separate from the formal 24-run matrix.

## 5. Terminology QA
- Kept `rule-based baseline` distinct from `deterministic fallback`.
- Preserved `LLM-assisted pipeline` for system-level results.
- Preserved `LLM` / `Gemini` decision wording only for model-generated decisions.
- Confirmed `provider success`, `parser success`, `operational waiting`, `post-hoc diagnostic`, `formal experiment`, `safety override`, and `postprocessor intervention` are used consistently.

## 6. Claim Consistency QA
- Removed or softened over-strong attribution language in the results/discussion sections.
- No surviving positive claims of `LLM superiority`, `LLM outperforms`, or `caused by the LLM` were found in the final text.
- The conclusion remains bounded: formal results support a pipeline-level traffic advantage, while the post-hoc Gemini diagnostic did not add incremental benefit beyond fallback-only.

## 7. Citation / Reference QA
- Key references checked in both the body and the reference list: Dresner and Stone, Cui et al., Dong et al., Driess et al., Hou et al., Huang et al., and Safarov.
- No obvious duplicate bibliography entries were found by local scan.
- Human verification is still required for the standard SUMO reference: the dissertation text uses SUMO extensively, but no explicit SUMO bibliography entry was found in the current reference list.
- Human verification is also recommended for any bibliography metadata that may require external checking before submission, especially the final institutional formatting expectations.

## 8. Figure / Table Numbering QA
- Confirmed Chapter 5 retains the expected figure sequence and the new Chapter 6 attribution tables do not break the numbering chain.
- Confirmed the post-hoc tables are numbered and captioned as Table 5 and Table 6.
- No broken in-text references were identified in the checked sections.

## 9. Formatting QA
- Removed the remaining Markdown-style `#` from the title page placeholder line.
- Cleared hidden Unicode artifacts in the document text.
- The document still contains a placeholder title page, which is acceptable only until the front-matter details are supplied by a human.
- Word field-based items such as TOC/List of Figures/List of Tables still need a final update in Word.

## 10. Front-Matter QA
- Current title page still contains user placeholders for `Title` and `Author`.
- No explicit `Supervisor`, `Programme`, `submission date`, or `word count` text was found in the current DOCX.
- A TOC placeholder note exists in the OOXML, but there is no populated Table of Contents / List of Figures / List of Tables text in the extracted paragraphs.
- These items should be filled or refreshed manually before submission.

## 11. Remaining HUMAN_ACTION_REQUIRED
- Fill in the title, author, supervisor, programme, submission date, and word count details.
- Update the Table of Contents, List of Figures, List of Tables, and all Word fields.
- Verify the final institutional cover-page requirements against the University of Bristol template.
- Confirm the missing standard SUMO bibliographic entry before submission.

## 12. VISUAL_RENDER_QA Status
- `VISUAL_RENDER_QA_PENDING`
- Attempted render through the packaged DOCX renderer, but the environment does not currently expose `soffice`, so page-image QA could not be completed in this session.

## 13. Remaining HIGH Risks
- The front matter is still not fully submission-ready because the title and author remain placeholders.
- The reference list appears to be missing the standard SUMO citation, which is a likely examiner-visible bibliographic gap.

## 14. Remaining MEDIUM Risks
- TOC/List of Figures/List of Tables still need a final Word field update.
- Visual layout could not be confirmed by rendered page images in this environment.
- The document should be opened in Word once for a final field refresh and pagination check.

## 15. Final Examiner Assessment
The dissertation is now much closer to submission quality. The substantive attribution boundary is consistent, the final evidence split is clear, the key tables and figures remain aligned with the frozen evidence base, and the major wording risks have been reduced. The remaining work is mainly front-matter completion, reference completion, and a final manual Word field refresh.

**Provisional status:** `FINAL_SUBMISSION_QA_PASS_WITH_HUMAN_ACTIONS`
