# Writing Gap Audit v1

## Chapter readiness summary

| Chapter | Status | Notes |
| --- | --- | --- |
| Introduction | READY | Can be written from current evidence, but research-gap wording needs cautious citation markers. |
| Literature Review / Background | MISSING | Needs source audit and real citations before it can be drafted properly. |
| Methodology / System Design | READY | Already written and consistent with frozen implementation. |
| Experimental Design | READY | Already written and aligned with the formal v2 manifest. |
| Results | READY | Already written and backed by raw formal v2 evidence. |
| Discussion | READY | Already drafted, but still needs polishing to avoid over-interpretation. |
| Limitations | READY | Already drafted and evidence-aligned. |
| Conclusion and Future Work | READY | Can be written now from current evidence. |

## Section-by-section audit

### Introduction

- Status: `READY`
- Citation gaps: `NEEDS_CITATIONS` for the research-gap sentence and any broader motivation claims about the field.
- Figure/table gaps: none required.
- Internal issue: avoid claiming general autonomous-driving novelty.

### Literature Review / Background

- Status: `MISSING`
- Citation gaps: `NEEDS_CITATIONS`
- Comment: this chapter cannot be completed from repository evidence alone.

### Methodology / System Design

- Status: `READY`
- Citation gaps: only minimal external citation support may be needed if the thesis discusses general background concepts.
- Internal issue: make sure it remains a method description, not a results chapter.

### Experimental Design

- Status: `READY`
- Citation gaps: none for the experimental matrix itself.
- Internal issue: do not mix design with outcome interpretation.

### Results

- Status: `READY`
- Citation gaps: no external citations required for the results themselves, but any comparative background statement would need citations.
- Figure/table gaps: the chapter is strongly improved by actually rendering the proposed tables and figures.
- Internal issue: ensure provider reliability is clearly separated from traffic performance.

### Discussion

- Status: `READY`
- Citation gaps: citation support may be needed for any broad statement about prior work or general field behavior.
- Internal issue: avoid turning the discussion into speculation beyond the evidence.
- Main risk: overclaiming that the LLM itself caused the traffic improvement.

### Limitations

- Status: `READY`
- Citation gaps: none required for evidence-backed limitations.
- Internal issue: avoid duplicating the Discussion chapter verbatim.

### Conclusion and Future Work

- Status: `READY`
- Citation gaps: future work statements do not need citations if they are directly derived from limitations.
- Internal issue: do not promise outcomes that the present data cannot support.

## Cross-chapter consistency checks

### 1. Research questions

- Status: `READY`
- Finding: RQ1-RQ4 are consistent across the research design, results, and discussion.

### 2. Methodology and implementation consistency

- Status: `READY`
- Finding: the written method matches the frozen controller architecture and request configuration.

### 3. Results and discussion boundary

- Status: `READY`
- Finding: Results reports observed metrics; Discussion interprets them; neither chapter currently needs a method change.

### 4. Over-interpretation risk

- Status: `NEEDS_REVISION`
- Finding: the wording must continue to avoid claims such as "LLM significantly outperformed rule-based" unless a future statistical argument is added.

### 5. Missing visualisation artifacts

- Status: `NEEDS_REVISION`
- Finding: the dissertation needs rendered tables/figures, not just a design list.
- Priority figures: waiting time, speed, provider success/fallback rate, latency.

### 6. Literature review dependency

- Status: `BLOCKED`
- Finding: the introduction and full draft are structurally ready, but the literature review still needs real source audit and citations.

## Overall gap assessment

- Ready: most of the core dissertation scaffold.
- Needs citation work: introduction framing and literature review.
- Needs revision: visualisation outputs and careful wording around causality.
- Missing: actual literature review prose.
- Blocked: none of the evidence-based results or method chapters are blocked.

## Main residual risk

The only serious writing risk left is narrative overreach. The dissertation must continue to treat provider reliability as part of the scientific story, not as a footnote.
