# Full Draft Consistency Audit v1

## Scope

Audit target: `D:\Sumo\sumo_train\docs\dissertation\full_draft_v2.md`

I checked the full narrative chain rather than individual chapters in isolation:

- Introduction
- Literature Review
- Research Gap
- Aim / Objectives / RQs
- Methodology
- Experimental Design
- Results
- Discussion
- Limitations
- Conclusion

## Overall judgment

The draft is logically consistent. The dissertation argument flows from problem statement to literature synthesis to a narrow research gap, then to the frozen method, the formal v2 experiment, and finally to a conservative interpretation of the evidence.

## Consistency checks

| Check | Status | Notes |
| --- | --- | --- |
| Research gap naturally yields RQ1-RQ4 | PASS | The gap is narrow enough to support the four RQs without overextending the literature. |
| RQ1-RQ4 align with the actual experiment | PASS | The RQs map directly onto the controller comparison, hybrid effect, safety layer, and 4V/8V comparison. |
| Methodology answers the RQs | PASS | The staged pipeline, prompt freeze, and trace logging provide the machinery needed to answer the questions. |
| Results provide the relevant evidence | PASS | Traffic, reliability, parser, fallback, latency, intervention, and safety evidence are all present. |
| Discussion answers the RQs one by one | PASS | Each RQ is interpreted separately and conservatively. |
| Conclusion matches the results and discussion | PASS | The conclusion repeats the main findings without introducing new claims. |
| Chapter transitions are coherent | PASS | Literature Review -> Methodology -> Experiment -> Results -> Discussion -> Limitations -> Conclusion reads naturally. |
| Numerical story is internally consistent | PASS | 24/24 runs, 24 valid, 0 collisions, 109 provider successes, 2555 failures, 0 safety overrides, 1 post-processor intervention all cohere across chapters. |
| Pipeline-level interpretation is preserved | PASS | The draft consistently avoids treating the pipeline outcome as pure LLM performance. |
| Novelty and safety claims are restrained | PASS | The draft avoids universal superiority and strong safety claims. |

## Issues found and corrected in the supervisor draft

1. **Project-log phrasing**
   - The original draft included provenance-heavy wording such as repository / branch / freeze commit / freeze tag references in the main body.
   - In the supervisor draft, this is reduced to a shorter reproducibility note so the text reads more like a dissertation.

2. **Repeated fallback warning**
   - The original draft repeated the same caution about pure LLM performance in several places.
   - This is still retained where needed for validity, but the supervisor draft should keep the repetition lighter.

3. **British English normalisation**
   - Some sections used American spellings or mixed spelling.
   - The supervisor draft normalises the main narrative to British spelling where practical.

4. **Section duplication**
   - Discussion and Conclusion both summarise the main finding.
   - This is acceptable, but the supervisor draft keeps the conclusion shorter so it does not re-litigate the full discussion.

## Remaining minor watchpoints

- One recovered reference remains bibliographically incomplete in the local archive because the DOI / URL is not visible in the PDF text.
- The results chapter still relies on a compact set of tables rather than a large figure gallery, which is appropriate for the current evidence but may need visual polishing later.
- A final word-processor pass is still useful for heading spacing, table layout, and final reference style normalisation.

## Final consistency verdict

The full draft is coherent and ready for supervisor review after light stylistic polishing.
