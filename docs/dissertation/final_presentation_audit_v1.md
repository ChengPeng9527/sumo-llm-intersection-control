# Final Presentation Audit v1

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

## Figures created

- `docs/dissertation/figures/figure_1_mean_waiting_time.png`
- `docs/dissertation/figures/figure_2_mean_speed.png`
- `docs/dissertation/figures/figure_3_provider_success_fallback.png`
- `docs/dissertation/figures/figure_4_latency.png`

## Tables retained

- Table 1: Experimental configuration
- Table 2: Traffic performance by controller and scale
- Table 3: Provider/parser/fallback reliability
- Table 4: Decision-source / postprocessor / safety behaviour

## Figure and table map

| Number | Caption | First citation location | Short interpretation |
| --- | --- | --- | --- |
| Figure 1 | Mean waiting time by controller and vehicle scale | Results section 5.2; first mentioned immediately after the traffic-performance claim | Rule-based degrades sharply at 8V; LLM-assisted controllers remain comparatively stable. |
| Figure 2 | Mean speed by controller and vehicle scale | Results section 5.2; first mentioned immediately after Figure 1 | LLM-assisted controllers sustain higher speed than rule-based in both tested scales. |
| Figure 3 | Provider success and fallback reliability | Results section 5.3; first mentioned immediately after the provider reliability paragraph | Fallback dominates every live LLM-bearing cell; provider success is especially low at 8V. |
| Figure 4 | Live-provider latency by controller and vehicle scale | Results section 5.3; first mentioned immediately after Figure 3 | Latency stays bounded, but provider availability remains the dominant limitation. |
| Table 1 | Experimental configuration | Results section 1, opening table in the Results chapter | Defines the formal evidence boundary and the 24-run design. |
| Table 2 | Traffic performance by controller and scale | Results section 2, immediately after the traffic-performance discussion begins | Summarises completion, waiting time, speed, throughput, and collisions. |
| Table 3 | Provider/parser/fallback reliability | Results section 3, immediately after provider reliability discussion begins | Summarises provider attempts, successes, fallback, and latency. |
| Table 4 | Decision-source / postprocessor / safety behaviour | Results section 4, immediately after the decision-flow discussion begins | Summarises the dominant decision source and the absence of visible intervention. |

## Methodology reproducibility gaps

- No blocking reproducibility gap remains in the manuscript.
- The SUMO scenario, controller architecture, prompt/parser interface, fallback mechanism, safety verifier, simulation parameters, evaluation metrics, and formal experiment matrix are all described in the repository evidence and in the manuscript.
- The manuscript still benefits from the repository-level traceability already documented in the research and results files, but no extra experiment or method change is required.

## Literature support gaps

- The seven recovered references are sufficient for the claims actually made in the literature review.
- The review is selective rather than exhaustive, but each major claim in the manuscript is supported by the recovered archive.
- No additional literature source is required to justify the final dissertation claims as written.

## Bibliography gaps

- Dresner and Stone (2008) is bibliographically incomplete at DOI/URL level from the local archive alone.
- The local PDF confirms the title, authors, venue, and publication context, but not a DOI or a URL.
- Mark as `NEEDS_EXTERNAL_VERIFICATION` if a fully normalised bibliography format is required for the final Word document.

## Remaining formatting tasks

- Fill title page fields.
- Generate the final table of contents in Word.
- Insert the four PNG figures into the final document if the Word export workflow requires embedded images.
- Apply the university's final Word style if a template is used.

## Final word count

- `7,287` words in `docs/dissertation/full_draft_word_ready_v1.md`

## Scientific text changed

- No substantive scientific text changed.
- The final evidence boundary remains frozen:
  - 4V = valid `formal_v2` evidence
  - 8V = corrected `formal_v4` evidence
  - nominal `formal_v2` 8V excluded
  - `formal_v3` excluded
- The new Word-ready file only adds presentation-layer figure inserts and layout scaffolding.

## Final verdict

- `READY_FOR_DOCX_GENERATION`
