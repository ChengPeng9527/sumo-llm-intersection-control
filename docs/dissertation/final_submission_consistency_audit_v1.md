# Final Submission Consistency Audit v1

Repository: `D:\Sumo\sumo_train`
Canonical manuscript: `D:\Sumo\sumo_train\docs\dissertation\full_draft_submission_v2.docx`
Source: `D:\Sumo\sumo_train\docs\dissertation\full_draft_submission_v2.md`

## Blocking issues

- None identified in the scientific content.
- No submission-blocking numerical inconsistency was found.
- No evidence-breaking contradiction was found between Abstract, Introduction, RQs, Methodology, Results, Discussion, Limitations, and Conclusion.

## Major issues

- The Markdown source is not a perfect one-to-one serialization of the DOCX presentation layer: the DOCX contains four figure captions, while the Markdown source does not serialize those figure-caption paragraphs as text.
- The manuscript keeps title-page placeholders for dissertation title, author, supervisor, and submission date. These are not scientific problems, but they still require manual completion before final submission.
- The Table of Contents is still a placeholder in the manuscript and must be updated in Word before submission.
- The manuscript explains provider reliability consistently as fallback-heavy and rate-limit constrained, but it does not restate the aggregate `4/2784` and `99.86%` formal_v4 headline figures as a single standalone summary. The underlying evidence is consistent, but the exact aggregate numbers are not foregrounded in every discussion section.

## Minor issues

- Some concepts are intentionally repeated across Results, Discussion, and Conclusion to preserve the evidence boundary and keep the claims conservative.
- `full_draft_submission_v2.md` still contains a placeholder title block and TOC placeholder text by design.
- The dissertation remains slightly prose-repetitive in the safe RQ summary / conclusion area, but this is not a contradiction.

## Numerical consistency

- The core traffic numbers are internally consistent across sections:
  - 4V rule-based: waiting `82.0`, speed `2.3098 m/s`
  - 4V LLM-assisted: waiting `15.0`, speed `6.8026 m/s`
  - 8V rule-based: waiting `242.0417`, speed `1.1895 m/s`
  - 8V LLM-assisted: waiting `15.2917`, speed `6.5991 m/s`
- Completion rate remains `100%` across the valid evidence.
- Collision count remains `0` across the valid evidence.
- Safety overrides remain `0` across the valid evidence.
- `formal_v2` nominal 8V remains excluded.
- `formal_v3` remains excluded.
- `formal_v4` remains the corrected final 8V evidence.

## Evidence consistency

- The final evidence boundary is consistent throughout the manuscript:
  - `4V = valid formal_v2`
  - `8V = formal_v4`
  - `formal_v2` nominal 8V excluded
  - `formal_v3` excluded
- The manuscript does not revert to the invalid nominal `formal_v2` 8V traces as final evidence.
- The text consistently frames the results as pipeline-level behaviour rather than pure LLM behaviour.
- Provider reliability is consistently treated as a first-order validity threat.

## Citation / reference consistency

- In-text citations and the recovered bibliography are broadly aligned.
- All seven recovered references are represented in the bibliography.
- No unsupported extra citation entries were introduced.
- No unsupported DOI was invented for Dresner and Stone.
- The bibliography is usable for the dissertation draft, with the caveat that Dresner and Stone remains bibliographically incomplete at DOI/URL level from the local archive alone.

## Figure / table consistency

- Table numbering is consistent:
  - Table 1: Experimental configuration
  - Table 2: Traffic performance by controller and scale
  - Table 3: Provider/parser/fallback reliability
  - Table 4: Decision-source / postprocessor / safety behaviour
- The DOCX contains four figures and four corresponding captions.
- The Markdown source does not serialize the figure captions as text paragraphs, so the source and DOCX are not a perfect textual mirror on that point.
- Figure/table ordering in the DOCX is coherent and the captions match the reported content.

## RQ consistency

- RQ1 is consistent with the reported traffic numbers and the cautious interpretation.
- RQ2 avoids claiming that Hybrid clearly outperforms Raw LLM.
- RQ3 avoids claiming safety superiority from `0` collisions and `0` safety overrides.
- RQ4 stays limited to the tested `4V -> 8V` scenarios and does not generalise beyond them.

## Methodology completeness

- The manuscript sufficiently explains:
  - SUMO scenario
  - scenario generation
  - vehicle count
  - control zone
  - decision space
  - fallback
  - cooperative postprocessor
  - safety verifier
  - request config
  - metrics
  - experiment matrix
- The method section is adequate for a first-draft dissertation and for examiner review.
- No new methodological gap blocks submission.

## Remaining placeholders

- Title page fields:
  - dissertation title
  - author name
  - supervisor name
  - submission date
- Table of Contents field update in Word

## Final Word manual actions

- Fill the title page fields.
- Open the DOCX in Word and update the Table of Contents field.

## Estimated dissertation readiness

- Ready for final human review.

## Another experiment needed?

- No.

## Final verdict

- `READY_FOR_FINAL_HUMAN_REVIEW`
