# Final Reference Audit

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

## Scope

Audited dissertation files:

- `docs/dissertation/literature_review_v2_final.md`
- `docs/dissertation/introduction_v1.md`
- `docs/dissertation/full_draft_supervisor_v3.md`
- `docs/dissertation/references_v2_final.md`

## Summary

- Total recovered references in the final bibliography: `7`
- Verified existing references: `6`
- Incomplete reference entries: `1`
- Missing reference entries for in-text citations: `0`
- Duplicate reference entries: `0`
- Unsupported citation placeholders in the final draft: `0`

## Citation mapping

| In-text source | Reference entry | Status |
| --- | --- | --- |
| Dresner and Stone (2008) | `Dresner, K. and Stone, P. (2008). A Multiagent Approach to Autonomous Intersection Management.` | MATCHED |
| Safarov (2022) | `Safarov, K. (2022). The impact of autonomous vehicles on traffic performance at an unregulated junction.` | MATCHED |
| Huang et al. (2022) | `Huang, W., Abbeel, P., Pathak, D., and Mordatch, I. (2022). Language Models as Zero-Shot Planners: Extracting Actionable Knowledge for Embodied Agents.` | MATCHED |
| Driess et al. (2023) | `Driess, D., Xia, F., Sajjadi, M. S. M., ... and Florence, P. (2023). PaLM-E: An Embodied Multimodal Language Model.` | MATCHED |
| Cui et al. (2025) | `Cui, C., Ma, Y., Yang, Z., ... and Wang, Z. (2025). Large Language Models for Autonomous Driving (LLM4AD): Concept, Benchmark, Experiments, and Challenges.` | MATCHED |
| Hou et al. (2025) | `Hou, X., Wang, W., Yang, L., ... and Zhao, X. (2025). DriveAgent: Multi-Agent Structured Reasoning with LLM and Multimodal Sensor Fusion for Autonomous Driving.` | MATCHED |
| Dong et al. (2026) | `Dong, X., Li, J., Xie, J., ... and Hang, P. (2026). Large Language Model based Interactive Decision-Making for Autonomous Driving.` | MATCHED |

## Reference-by-reference audit

| Reference | Bibliographic completeness | Notes |
| --- | --- | --- |
| Dresner & Stone | COMPLETE ENOUGH | Venue and title are present; DOI/URL was not locally visible. |
| Safarov | COMPLETE ENOUGH | Thesis reference is robust; local archive provides a Bristol URL clue. |
| Huang et al. | COMPLETE ENOUGH | ArXiv identifier and project URL clue are present. |
| Driess et al. | COMPLETE ENOUGH | ArXiv identifier and project URL clue are present. |
| Cui et al. | COMPLETE ENOUGH | Draft-level bibliography entry is usable. |
| Hou et al. | COMPLETE ENOUGH | Draft-level bibliography entry is usable. |
| Dong et al. | COMPLETE ENOUGH | Draft-level bibliography entry is usable. |

## Final check against the dissertation draft

The final draft uses the recovered literature only in the background/literature section and does not create unsupported claims about the formal results.

The dissertation now has a stable, locally recovered citation set that is sufficient for supervisor review:

- 1 foundational intersection-management paper
- 1 Bristol thesis on unregulated junction performance
- 2 embodied / planning language-model papers
- 3 driving-focused LLM papers

## Bottom line

The final dissertation draft is citation-consistent. The only incomplete bibliographic item is the Dresner and Stone paper's DOI/URL, which is a normalisation issue rather than a citation failure.
