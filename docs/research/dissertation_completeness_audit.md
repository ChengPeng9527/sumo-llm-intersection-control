# Dissertation Completeness Audit

Scope: this audit checks completeness against the repository evidence only. It does not modify the dissertation, rerun experiments, or invent missing facts.

Evidence base used:
- `docs/dissertation/full_draft_submission_v5.md`
- `docs/dissertation/full_draft_v2.md`
- `docs/dissertation/results_v3_corrected.md`
- `docs/dissertation/discussion_v2_corrected.md`
- `docs/dissertation/references_v2_final.md`
- `docs/research/*` evidence notes and audits
- `src/*`, `config/*`, `scripts/*`, `tests/*`

## 1. Critical Missing Items

### [P0] Front matter is still placeholder-driven in the manuscript source
- Location: `docs/dissertation/full_draft_submission_v5.md` top block
- Problem: the title page still contains placeholders for title, author, supervisor, and submission date; the table of contents is also marked as a placeholder.
- Evidence in repository: lines 1-16 of `full_draft_submission_v5.md` show `Title: [Insert final dissertation title here]`, `Author: [Insert name here]`, `Supervisor: [Insert supervisor name here]`, `Submission date: [Insert date here]`, and `## Table of Contents (Placeholder)`.
- Recommended fix: replace the placeholders with the final dissertation metadata and generate a real Word TOC.
- Confidence: High
- Can Codex fix automatically? NO

### [P1] Back matter sections are not evidenced in the current manuscript source
- Location: end of `docs/dissertation/full_draft_submission_v5.md`
- Problem: no evidence was found in the manuscript source for a declaration, acknowledgements, list of figures, list of tables, abbreviations, or appendices.
- Evidence in repository: search across the dissertation drafts finds the title page and TOC placeholders, but no `Acknowledgements`, `Declaration`, `List of Figures`, `List of Tables`, `Abbreviations`, or `Appendix` blocks in the current draft source. The draft ends at `# References`.
- Recommended fix: confirm the Bristol template requirements, then add only the required front/back matter sections. If the template requires them, add appendices for reproducibility evidence.
- Confidence: Medium
- Can Codex fix automatically? NO

### [P1] Chapter 3 does not yet present the prompt schema and frozen request configuration in a dissertation-friendly form
- Location: `docs/dissertation/full_draft_submission_v5.md` Chapter 3; `src/llm/prompt_builder.py`; `src/llm/request_config.py`; `docs/research/canonical_prompt_specification.md`; `docs/research/llm_request_configuration_specification.md`
- Problem: the code and research notes contain the exact JSON contract, prompt structure, and frozen request settings, but the manuscript prose still reads as a summary rather than a compact evidence-backed specification. This is where a schema table or appendix would help.
- Evidence in repository: `build_structured_prompt(...)` in `src/llm/prompt_builder.py` defines the exact input blocks and JSON-only contract; `src/llm/request_config.py` freezes `Groq`, `openai/gpt-oss-20b`, `256` completion tokens, `low` reasoning effort, `30.0` s timeout, and `0` retries.
- Recommended fix: add a concise table or appendix that states the exact prompt input fields, output schema, and frozen request parameters.
- Confidence: High
- Can Codex fix automatically? YES

### [P1] Chapter 3 would benefit from a system architecture figure
- Location: `docs/dissertation/full_draft_submission_v5.md` Chapter 3; `src/controllers/decision_pipeline.py`; `src/llm/postprocessor.py`; `src/safety/safety_verifier.py`
- Problem: the manuscript describes the staged pipeline in prose, but there is no clear system architecture figure in the final figure set to anchor the stage separation visually.
- Evidence in repository: the figure documentation and figure assets are limited to the results plots (`figure_1` to `figure_4`); no architecture figure is evidenced in the final figure pack.
- Recommended fix: add a single architecture diagram showing raw proposal -> validation -> interface rule -> cooperative postprocessor -> safety verifier -> trace logging.
- Confidence: Medium-High
- Can Codex fix automatically? YES

### [P1] The bibliography is missing a standard SUMO citation
- Location: `docs/dissertation/references_v2_final.md`; `docs/dissertation/full_draft_submission_v5.md` Literature Review and References
- Problem: the dissertation discusses SUMO extensively, but the recovered bibliography contains only the seven recovered references and no standard SUMO software citation.
- Evidence in repository: `references_v2_final.md` explicitly says the bibliography is restricted to seven recovered references, and the listed entries do not include SUMO / Simulation of Urban MObility / Behrisch / Krajzewicz.
- Recommended fix: perform an external literature search for the canonical SUMO citation or software paper, verify it, then add it to the bibliography.
- Confidence: Medium
- Can Codex fix automatically? NO

## 2. Important Improvements

### [P2] Results still reads like a research notebook in places
- Location: `docs/dissertation/full_draft_submission_v5.md` Chapter 5; `docs/dissertation/results_v3_corrected.md`
- Problem: the result chapter is already evidence-based, but parts of it still read like an internal audit memo, especially the bullet lists and practical-note style rows.
- Evidence in repository: `results_v3_corrected.md` uses tables plus compact interpretation notes such as `Dominant decision pattern`, `Practical note`, and seed-level value dumps.
- Recommended fix: keep every number unchanged, but convert the section into conventional academic prose with short lead-in sentences before the tables.
- Confidence: High
- Can Codex fix automatically? YES

### [P2] Discussion still exposes draft scaffolding
- Location: `docs/dissertation/full_draft_submission_v5.md` Chapter 6; `docs/dissertation/discussion_v2_corrected.md`
- Problem: the discussion still uses labels such as `Observed result`, `Interpretation`, `What not to claim`, and block quotes for recommended wording.
- Evidence in repository: `discussion_v2_corrected.md` preserves these scaffold labels while already containing the correct bounded conclusions.
- Recommended fix: keep the evidence and conclusions, but rewrite the chapter as continuous dissertation prose under the RQ subsections.
- Confidence: High
- Can Codex fix automatically? YES

### [P2] Controller naming should be standardized in the narrative
- Location: `docs/dissertation/full_draft_submission_v5.md`; `src/experiments/formal_experiment_matrix.py`
- Problem: the manuscript and code use different naming surfaces for the same controllers, e.g. `rule_based` vs `Rule-based`, `raw_llm` vs `Raw LLM`, and `hybrid_safety` vs `Hybrid + Safety`.
- Evidence in repository: the code uses snake_case identifiers, while the dissertation tables use human-readable labels.
- Recommended fix: keep code identifiers in monospace only when needed for traceability, and use one consistent human-readable naming style everywhere else.
- Confidence: High
- Can Codex fix automatically? YES

### [P2] Internal provenance paths should be kept out of the final body text
- Location: `docs/dissertation/full_draft_submission_v5.md` References and results-provenance sections
- Problem: the manuscript source includes repository paths and local archive notes that are useful for audit work but too noisy for the final dissertation body.
- Evidence in repository: the references block includes local source paths, and several results sections repeat raw result-directory paths for provenance.
- Recommended fix: keep provenance in appendices or audit files, but present the final body with shorter academic phrasing.
- Confidence: High
- Can Codex fix automatically? YES

### [P2] Bullet-heavy results and discussion sections should be condensed into prose
- Location: `docs/dissertation/full_draft_submission_v5.md` Chapters 5 and 6
- Problem: several sections still depend on bullet lists to carry the argument.
- Evidence in repository: the results and discussion chapters mix bullets, tables, and short interpretive fragments instead of fuller paragraph transitions.
- Recommended fix: convert the arguments into paragraph form while preserving the exact numeric results and the same claim boundaries.
- Confidence: High
- Can Codex fix automatically? YES

## 3. Optional Improvements

### [P3] Notation should be normalized for publication readability
- Location: `docs/dissertation/results_v3_corrected.md` and the corresponding DOCX rendering
- Problem: the publication version should consistently show true Unicode `±` and a single convention for mean, standard deviation, and range notation.
- Evidence in repository: the corrected results file already uses `±` consistently, so the issue is mostly about making sure the Word rendering matches the source.
- Recommended fix: keep the existing numbers, but verify the final DOCX export preserves the true `±` glyph and consistent numeric typography.
- Confidence: Medium
- Can Codex fix automatically? YES

### [P3] Harvard-style punctuation should be normalized across the final bibliography
- Location: `docs/dissertation/references_v2_final.md`
- Problem: the recovered bibliography is usable, but the final Word version may need a cleaner Harvard presentation if the university template is strict.
- Evidence in repository: the bibliography is explicitly described as a recovered draft bibliography with one incomplete DOI/URL item.
- Recommended fix: normalize punctuation, italics, and line wrapping in the final Word file after the reference list is frozen.
- Confidence: Medium
- Can Codex fix automatically? YES

## 4. Citation Gaps

### [P1] SUMO software citation
- Theme needing external literature search: the canonical SUMO / Simulation of Urban MObility reference or software paper.
- Why this is a gap: SUMO is central to the method, but the recovered bibliography does not include a standard SUMO citation.
- Repository basis: `docs/dissertation/references_v2_final.md` and `docs/dissertation/literature_evidence_matrix_v1.md`
- Can Codex fill it now? NO

### [P2] Any missing software citation policy for the University of Bristol template
- Theme needing external literature search: whether the Bristol dissertation template expects separate software citations or only standard references.
- Why this is a gap: the repository does not contain the template text itself.
- Repository basis: `docs/dissertation/references_v2_final.md` and `docs/dissertation/final_reference_audit.md`
- Can Codex fill it now? NO

## 5. Formatting Defects

### [P2] Results and discussion sections are still hybrid academic/logbook prose
- Location: `docs/dissertation/full_draft_submission_v5.md` Chapters 5 and 6
- Problem: the chapter voice is academically valid in places, but still reveals its audit ancestry.
- Evidence in repository: frequent table captions, short bullet interpretation blocks, and repeated provenance notes.
- Recommended fix: rewrite into smoother prose while leaving the evidence untouched.
- Confidence: High
- Can Codex fix automatically? YES

### [P2] Repeated provenance paths make the manuscript feel internal rather than final
- Location: `docs/dissertation/full_draft_submission_v5.md` References and evidence-boundary sections
- Problem: local result directory paths appear where a final dissertation would normally keep the prose higher level.
- Evidence in repository: repeated `results/formal_experiment/...` paths and local archive source paths in the references section.
- Recommended fix: move those paths to appendices or a reproducibility note.
- Confidence: High
- Can Codex fix automatically? YES

### [P3] The final Word export should be checked for glyph integrity
- Location: final DOCX export path for `full_draft_submission_v6.docx` / `full_draft_submission_v7.docx`
- Problem: earlier drafts in the repository show some encoding artifacts in Markdown exports, so the Word export should be verified for clean glyphs and no replacement characters.
- Evidence in repository: previous publication-cleanup work already focused on `卤`/`±` normalization.
- Recommended fix: run a final DOCX text scan after export to confirm no bad-character regressions remain.
- Confidence: Medium
- Can Codex fix automatically? YES

## 6. Appendix Requirements

The following appendices are the most defensible additions if the final dissertation is meant to be fully evidence-backed:

- Final `P1_BASELINE` prompt appendix
- Frozen experiment configuration appendix
- Controller / pipeline pseudocode or algorithm table appendix
- Reproducibility appendix with freeze commit, freeze tag, and final 4V / 8V evidence boundary
- If required by the Bristol template, declaration, acknowledgements, list of figures, list of tables, and abbreviations

## 7. Proposed Final Dissertation Structure

Recommended formal structure:

1. Introduction
2. Literature Review
3. Methodology and System Design
4. Experimental Design
5. Results
   - 5.1 Experimental Evidence and Validity
   - 5.2 Traffic Performance
   - 5.3 Provider and Parser Reliability
   - 5.4 Decision-Flow Behaviour
   - 5.5 Safety Outcomes
   - 5.6 Summary
6. Discussion
   - 6.1 Traffic Efficiency and RQ1
   - 6.2 Cooperative Post-processing and RQ2
   - 6.3 Safety Verification and RQ3
   - 6.4 Vehicle Scale and RQ4
   - 6.5 Provider Reliability and Attribution
   - 6.6 Relationship to Existing Literature
   - 6.7 Overall Interpretation
7. Limitations
8. Conclusion and Future Work
9. References
10. Appendices

## 8. Safe Automatic Fix Plan

The following are safe to do automatically without changing experiment results:

1. Replace title-page placeholders once the user confirms the final metadata.
2. Generate the real table of contents in Word.
3. Add a concise Chapter 3 prompt/request/schema table from existing repository evidence.
4. Add a simple architecture figure drawn from the actual pipeline stages.
5. Add appendices for the frozen prompt, experiment configuration, and reproducibility boundary.
6. Rewrite Results and Discussion into dissertation prose without changing any numbers or claims.
7. Normalize controller naming and remove internal path noise from the final body text.
8. Verify the final DOCX export for glyph integrity and reference formatting.

## Priority Summary

- P0: 1
- P1: 5
- P2: 5
- P3: 3

Automatic fixability:

- Codex can fix directly: prompt/schema appendix, architecture figure, Results/Discussion prose cleanup, naming normalization, path cleanup, appendix scaffolding, glyph verification.
- Needs user confirmation: title, author, supervisor, submission date, and whether the Bristol template requires declaration/acknowledgements/list sections.
- Needs external literature search: SUMO citation and any template-driven software-citation requirement.
