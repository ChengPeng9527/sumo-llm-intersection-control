# Final 10-Page LaTeX Restructuring Report

## 1. Current-to-final structure map
- Current long-form dissertation chapters are compressed into a journal-paper style final paper with the following body structure:
  - Abstract
  - 1. Introduction
  - 2. Related Work
  - 3. Methodology
  - 4. Experimental Design
  - 5. Results
  - 6. Discussion and Limitations
  - 7. Conclusion
- The long-form dissertation appendices are not carried into the assessed paper body unless they are essential to the narrative.

## 2. Exact sections to keep
- Problem framing around unsignalised intersection coordination.
- Modular LLM-assisted pipeline description.
- The four controller variants:
  - Rule-Based
  - Raw LLM
  - Hybrid
  - Hybrid + Safety
- Frozen 24-run formal evidence boundary:
  - valid 4V formal_v2
  - corrected 8V formal_v4
- Formal traffic comparison.
- Provider reliability / fallback behaviour.
- Post-hoc Gemini attribution evidence.
- Experimental identifiability limitation.
- Bounded discussion of what can and cannot be claimed.

## 3. Exact sections to merge
- Merge the long introduction background, problem statement, gap, aim, and contributions into one compact Introduction.
- Merge the broad literature review into three synthesis subsections.
- Merge implementation and experiment design into a concise Methodology plus Experimental Design split.
- Merge discussion and limitations into one section with RQ-by-RQ interpretation.
- Merge conclusion and future work into one compact closing section.

## 4. Exact sections to delete from the main paper
- Long dissertation-structure overview.
- Repeated metric explanations that do not add new evidence.
- Appendix-length prompt and request-configuration details.
- Repeated provider-reliability prose that is already shown in tables.
- Any narrative implying independent LLM superiority.
- Any narrative turning post-hoc Gemini diagnostics into a formal matrix row.

## 5. Figures to keep
- Main-paper architecture figure promoted from the appendix concept.
- Optional compact summary figure only if it does not displace higher-value text or tables.

## 6. Tables to keep
- Controller configuration table.
- Formal evidence boundary table.
- Formal traffic results table.
- Provider reliability / fallback table.
- Post-hoc attribution table.

## 7. Figures / tables to remove from the main paper
- Any duplicate latency figure if space becomes tight.
- Any appendix-only evidence table that merely repeats raw logs.
- Any visual that restates numbers already shown in a nearby table.

## 8. Target page budget
- Cover page: outside the 10-page limit.
- Main paper body target: about 8.5 to 9.5 pages.
- References: outside the 10-page limit.
- This gives a small safety margin while staying close to the assessed length target.

## 9. Supplementary materials plan
- Recommended folder structure:
  - `supplementary_materials/README.md`
  - `supplementary_materials/code/`
  - `supplementary_materials/configs/`
  - `supplementary_materials/experiment_scripts/`
  - `supplementary_materials/results_summary/`
  - `supplementary_materials/raw_or_selected_results/`
  - `supplementary_materials/diagnostics/`
  - `supplementary_materials/prompt_and_controller_specs/`
  - `supplementary_materials/reproducibility_instructions/`
- Keep the supplementary bundle focused on reproducibility and integrity checking, not on replacing evidence that belongs in the main paper.

## 10. 3-minute video storyboard
- 0:00-0:20: problem, research question, and why the intersection setting matters.
- 0:20-0:50: system architecture and SUMO control loop.
- 0:50-1:20: the four controller variants and the staged pipeline.
- 1:20-1:55: formal results for waiting time, speed, and fallback-heavy provider behaviour.
- 1:55-2:30: post-hoc attribution finding showing reliable Gemini still matches fallback-only.
- 2:30-2:50: main methodological contribution and identifiability lesson.
- 2:50-3:00: concise conclusion and submission close.

## 11. AI disclosure reminder
- `AI_DISCLOSURE_HUMAN_REVIEW_REQUIRED`
- Place the final wording in the front matter, near the declaration / ethics material or immediately adjacent to the title-page metadata, depending on the final institutional convention.
- Do not fabricate final disclosure wording without user review.

## 12. Submission checklist
- Verify the cover page content.
- Update the AI disclosure wording after human review.
- Confirm the References bibliography compiles from `References.bib`.
- Confirm all formal evidence statements still refer only to the 24 valid formal runs.
- Confirm the Gemini attribution evidence remains explicitly post-hoc.
- Confirm the main paper body remains at or below 10 pages in the compiled PDF.
- Confirm tables and figures are readable at the final page size.
- Confirm the final PDF matches the template expectations before upload.

