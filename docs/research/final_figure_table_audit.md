# Final Figure/Table Audit

## 1. Executive Summary

Chapter 5 contains 4 tables and 4 embedded figures. The underlying data for all eight items are still consistent with the frozen formal evidence boundary:

- valid 4V `formal_v2`
- corrected 8V `formal_v4`
- 24 retained formal runs total

No Chapter 5 figure or table needs regeneration from the same formal data. The required changes are limited to caption/wording alignment and evidence-boundary clarification.

The one addition that should be made later is a small post-hoc attribution table set in Chapter 6, not Chapter 5, so that formal evidence and attribution evidence remain separate.

## 2. Current Chapter 5 Inventory

| Item | Current label / caption | Data validity against frozen evidence | Audit classification | Required change |
|---|---|---|---|---|
| Table 1 | `Table 1. Experimental configuration` | Valid. It correctly distinguishes valid 4V formal_v2 evidence from corrected 8V formal_v4 evidence and excludes the nominal 8V failure batch from final results. | `KEEP_DATA_REWRITE_CAPTION` | Rewrite the caption so it explicitly frames the retained formal boundary, not just the historical configuration. |
| Table 2 | `Table 2. Traffic performance by controller and scale` | Valid. All reported means, SDs, completion rates, and throughput values match the frozen formal evidence summary. | `KEEP_DATA_REWRITE_CAPTION` | Keep the data, but align the caption and any surrounding prose with pipeline-level interpretation rather than LLM-specific causation. |
| Table 3 | `Table 3. Provider/parser/fallback reliability` | Valid for the retained formal evidence. It reflects the fallback-heavy formal runs, not the later Gemini diagnostic pilots. | `KEEP_DATA_REWRITE_CAPTION` | Clarify in the caption that this is formal-provider reliability for the retained evidence boundary. |
| Table 4 | `Table 4. Decision-source / postprocessor / safety behaviour` | Valid. The zero-intervention pattern is consistent with the corrected formal evidence. | `KEEP_DATA_REWRITE_CAPTION` | Keep the data, but caption it as retained formal pipeline behaviour. |
| Figure 1 | `Figure 1. Mean waiting time by controller and vehicle scale in the corrected formal evidence.` | Valid. The waiting-time pattern matches Table 2 and the frozen formal evidence. | `KEEP_DATA_REWRITE_CAPTION` | Keep the chart, but tighten the caption so it explicitly refers to the retained formal evidence boundary. |
| Figure 2 | `Figure 2. Mean speed by controller and vehicle scale in the corrected formal evidence.` | Valid. The mean-speed pattern matches Table 2 and the frozen formal evidence. | `KEEP_DATA_REWRITE_CAPTION` | Keep the chart, but align caption wording with pipeline-level interpretation. |
| Figure 3 | `Figure 3. Provider success and fallback rate by LLM controller and scale.` | Valid for the formal evidence, but the caption is too easy to confuse with the later post-hoc Gemini diagnostic work. | `KEEP_DATA_REWRITE_CAPTION` | Rewrite the caption to say `retained formal evidence` and avoid implying the later Gemini diagnostic is part of this figure. |
| Figure 4 | `Figure 4. Mean provider latency by LLM controller and scale.` | Valid for the formal evidence, but should not be read as a live Gemini diagnostic. | `KEEP_DATA_REWRITE_CAPTION` | Rewrite the caption to make clear this is formal-provider latency, not the later post-hoc diagnostic latency. |

### Inventory notes

- There are no missing Chapter 5 tables or figures.
- There is no evidence that any Chapter 5 figure/table must be regenerated from the same formal data.
- The existing Chapter 5 numerical summaries are aligned with the frozen formal evidence boundary.
- The main remaining issue is wording, not data.

## 3. Validity Status by Item

### Table 1

Status: `KEEP_DATA_REWRITE_CAPTION`

Reason:
- The underlying data are valid.
- The table is useful because it documents the final evidence boundary.
- The caption should be tightened so it reads as a formal evidence-selection table, not as a historical experiment log.

### Table 2

Status: `KEEP_DATA_REWRITE_CAPTION`

Reason:
- The traffic metrics are frozen and match the retained formal evidence.
- No recalculation is needed.
- The table should be framed at the pipeline level, not as proof of independent LLM superiority.

### Table 3

Status: `KEEP_DATA_REWRITE_CAPTION`

Reason:
- The provider/parser/fallback counts are valid for the retained formal runs.
- The caption should make clear that this is the formal-provider reliability picture, not the later reliable Gemini diagnostic condition.

### Table 4

Status: `KEEP_DATA_REWRITE_CAPTION`

Reason:
- The zero-intervention pattern is consistent with the formal evidence.
- The caption should remain tied to the retained formal matrix.

### Figure 1

Status: `KEEP_DATA_REWRITE_CAPTION`

Reason:
- The underlying chart data are valid.
- The caption should say `retained formal evidence` and should not imply a post-hoc attribution result.

### Figure 2

Status: `KEEP_DATA_REWRITE_CAPTION`

Reason:
- The underlying chart data are valid.
- The caption should be rewritten only to align with the final pipeline-level claim boundary.

### Figure 3

Status: `KEEP_DATA_REWRITE_CAPTION`

Reason:
- The underlying chart data are valid.
- The phrase `LLM controller` is acceptable only if the surrounding text clearly means the formal live-provider controllers.
- The caption should be revised so it cannot be mistaken for the later Gemini diagnostic pilot.

### Figure 4

Status: `KEEP_DATA_REWRITE_CAPTION`

Reason:
- The underlying chart data are valid.
- The figure belongs to the formal reliability story and should not be conflated with the later 60-second timeout audits or Gemini live probes.

## 4. Recommended Caption Rewrites

These are caption-only recommendations. They do not require any data changes.

### Table 1

Recommended caption:

> Table 1. Retained formal evidence boundary and run validity

### Table 2

Recommended caption:

> Table 2. Traffic performance by controller and vehicle scale in the retained formal evidence

### Table 3

Recommended caption:

> Table 3. Provider/parser/fallback reliability in the retained formal evidence

### Table 4

Recommended caption:

> Table 4. Decision source, postprocessor, and safety behaviour in the retained formal evidence

### Figure 1

Recommended caption:

> Figure 1. Mean waiting time by controller and vehicle scale in the retained formal evidence

### Figure 2

Recommended caption:

> Figure 2. Mean speed by controller and vehicle scale in the retained formal evidence

### Figure 3

Recommended caption:

> Figure 3. Provider success and fallback rate across the retained formal evidence

### Figure 4

Recommended caption:

> Figure 4. Mean provider latency across the retained formal evidence

## 5. Proposed Post-hoc Attribution Tables for Chapter 6

These should be added to Chapter 6, not Chapter 5. They are post-hoc attribution evidence and must be labelled as such.

### 5.1 Attribution comparison table

Recommended table content:

| Controller | Operational waiting | Mean speed | Completion rate | Collision count | Attribution note |
|---|---:|---:|---:|---:|---|
| Rule-based 4V seed1 | 82.0 | 2.3098 m/s | 100% | 0 | Formal baseline |
| Fallback-only 4V seed1 | 11.0 | 7.5839 m/s | 100% | 0 | Post-hoc deterministic attribution comparator |
| Reliable Gemini Raw LLM 4V seed1 | 11.0 | 7.5839 m/s | 100% | 0 | Post-hoc live diagnostic with complete provenance |

Recommended caption:

> Table 6.x. Post-hoc 4V seed1 attribution comparison: rule-based baseline, deterministic fallback-only controller, and reliable live Gemini diagnostic

Recommended insertion location:

- Chapter 6, Section 6.5, immediately after the paragraph that introduces the reliable Gemini diagnostic pilot and before the decision-level discussion.

Why this should be a table:

- The values are exact and should be read side-by-side.
- The comparison is descriptive and does not need a figure to communicate trends.
- A table makes the evidence boundary clearer than a chart because it keeps the provenance note visible.

### 5.2 Decision-agreement summary table

Recommended table content:

| Comparison set | Comparable rows | Raw agreement | Final agreement | Note |
|---|---:|---:|---:|---|
| All comparable Gemini/fallback rows | 132 | 132/132 | 132/132 | Full aligned decision stream |
| High-discrimination subset | 39 | 39/39 | 39/39 | Mixed route-group probe rows |

Recommended caption:

> Table 6.y. Post-hoc decision agreement between reliable Gemini and fallback-only controllers

Recommended insertion location:

- Chapter 6, after the attribution comparison table, or at the end of Section 6.5.

Why a second table is useful:

- The traffic comparison and the agreement analysis answer different questions.
- The first table shows whether the traffic outcome differs.
- The second table shows whether the decision streams differ.
- Keeping them separate prevents the agreement data from being misread as traffic evidence.

## 6. Evidence-Boundary Warnings

1. Do not move the post-hoc Gemini attribution tables into Chapter 5.
2. Do not label the Chapter 5 provider/fallback charts as Gemini diagnostic evidence.
3. Do not mix the retained formal 24-run comparison with the fallback-only ablation or Gemini diagnostic runs.
4. Do not regenerate Chapter 5 figures unless the underlying data are found to be wrong. At present they are not.
5. If Chapter 6 adds attribution tables, label them explicitly as `post-hoc` or `supplementary attribution` evidence.
6. The formal 24-run evidence remains the only valid basis for the Chapter 5 results figures and tables.

## 7. Recommended Chapter 6 Addendum

If the dissertation layout permits only one extra object, prioritize the attribution comparison table first.

If two objects are allowed, add both:

1. the traffic attribution comparison table; and
2. the decision-agreement summary table.

No additional figure is strictly necessary. The table format is the better choice for this evidence because it preserves exact numbers and provenance labels.

## 8. Final Verdict

`FIGURES_REQUIRE_MINOR_UPDATE`

Rationale:

- Chapter 5 figures and tables are data-valid.
- No Chapter 5 object needs regeneration from the same formal data.
- Captions and surrounding prose should be tightened to match the final evidence boundary.
- The substantive new post-hoc attribution evidence belongs in Chapter 6 as tables, not as Chapter 5 figure replacements.
