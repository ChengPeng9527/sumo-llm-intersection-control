# Final 10-Page Content Restoration Report

## 1. Sections Expanded

- Introduction
- Related Work
- Methodology
- Experimental Design
- Results
- Discussion and Limitations
- Conclusion

## 2. Word v9 Content Restored

The following Word v9 ideas and arguments were restored or expanded in the final LaTeX draft:

- Why fixed / rule-based control is a useful but limited baseline
- Why LLMs are worth studying in a structured traffic-control pipeline
- The research gap around pipeline-level attribution versus model-level attribution
- Autonomous intersection management as a coordination problem
- Cooperative / multi-agent control as explicit conflict reasoning
- LLM planning, grounding, and executable action contracts
- Reliability, latency, and safety as first-order constraints on LLM use
- The meaning of the frozen prompt, parser, fallback, cooperative stage, and safety verifier
- The four-factor 24-run formal design and the corrected 4V/8V evidence boundary
- Descriptive interpretation of traffic metrics, provider reliability, and post-hoc attribution
- The distinction between traceability and causal identifiability
- Bounded limitations and future-work priorities derived from the evidence

## 3. Reorganised, Not Newly Invented

The following were reorganised and expanded from existing dissertation material rather than newly invented research claims:

- Introduction background and research gap framing
- Related-work synthesis across the 13 restored references
- Methodology explanation of state representation, action interface, fallback semantics, and provenance
- Results narrative around the retained formal tables and post-hoc attribution evidence
- Discussion framing around pipeline-level versus model-level interpretation
- Conclusion wording that stays within the frozen evidence boundary

## 4. New Experimental Claims

- None.

## 5. Frozen Numbers Changed

- None.
- All formal values and post-hoc attribution values were preserved as previously frozen.

## 6. Formal / Post-hoc Boundary

- Preserved.
- The 24-run formal evidence remains separate from the post-hoc Gemini attribution diagnostic.
- The new prose continues to treat pipeline-level traffic advantage and model-level identifiability as separate questions.

## 7. References

- 13 references remain in `References.bib`.
- All citation keys in `root.tex` resolve successfully.
- No duplicate BibTeX entries were detected.
- No unused BibTeX entries were detected.

## 8. Figures Restored

The final paper now reuses the existing dissertation figures as compact evidence-supporting plots:

- Waiting-time plot: `../figures/figure_1_mean_waiting_time.png`
- Mean-speed plot: `../figures/figure_2_mean_speed.png`
- Provider-success / fallback plot: `../figures/figure_3_provider_success_fallback.png`
- Latency plot: `../figures/figure_4_latency.png`

These were inserted as two figure blocks:

- Traffic trends figure block for waiting and speed
- Provider reliability figure block for success/fallback and latency

## 9. Estimated Main-Paper Pages

Estimated main-paper length after restoration: approximately 9.2 to 9.7 pages.

This is a static estimate based on the expanded prose, the added figures, and the retained tables. Local compilation was not available, so the final page count must be confirmed in Overleaf.

## 10. Sections That May Still Be Short

- Conclusion is intentionally concise and may still read slightly tight if Overleaf wraps floats aggressively.
- If the main paper renders below target, the next best place to expand is Discussion, not Conclusion.

## 11. Sections That May Be Long

- Methodology may run close to the upper end of the target because of the added pipeline explanation.
- Results also carries the largest density of tables and figures.

## 12. Repetition Check

- No major duplicated claims were introduced.
- Some ideas are necessarily echoed across Introduction, Results, and Discussion, but they are used for reinforcement rather than as redundant filler.

## 13. Unsupported Claim Check

- No new unsupported claim was introduced.
- The draft still avoids independent LLM superiority, general scalability, safety superiority, or a standalone cooperative benefit.

## 14. LaTeX Syntax Risk

- `git diff --check` passed.
- All citation keys resolve.
- No duplicate labels were detected.
- No broken `ef` targets were detected.
- No obvious new special-character errors were detected in the edited manuscript.
- Local LaTeX compiler availability check failed, so final PDF validation must be done in Overleaf.

## 15. Next Overleaf Checks

After compiling in Overleaf, inspect:

1. Final main-body page count versus the 10-page limit.
2. Whether the new figure blocks stay near the Results text instead of drifting to the references area.
3. Whether Table 4, Table 5, and Table 6 still sit close to their discussion passages.
4. Whether the added figures fit cleanly in the two-column layout without crowding captions.
5. Whether any long lines in Methodology or Discussion need a small wording trim if the body exceeds the target.

## 16. Final Verdict

CONTENT_RESTORATION_READY_WITH_MINOR_ISSUES
