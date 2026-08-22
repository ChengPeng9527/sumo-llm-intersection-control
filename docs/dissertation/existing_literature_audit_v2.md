# Existing Literature Audit v2

## Scope

This audit covers local dissertation and research materials plus the PDF reference archive at:

- `C:\Users\Admin\Desktop\References\`

Searched repository locations:

- `D:\Sumo\sumo_train\docs\research\`
- `D:\Sumo\sumo_train\docs\dissertation\`
- repository `*.md`, `*.txt`, `*.bib`, `*.docx`, and `*.pdf` files

Search keywords:

- `References`
- `Bibliography`
- `Literature Review`
- `Related Work`
- `citation`
- `LLM`
- `large language model`
- `autonomous driving`
- `intersection`
- `unsignalised intersection`
- `cooperative driving`
- `SUMO`
- `decision making`
- `safety`
- `fallback`

## Method

I treated a source as a recoverable reference if the PDF itself provided enough local evidence to identify the work, usually from the title page, first page, metadata, or arXiv / repository URL shown in the PDF.

I did **not** use web search to fill gaps.
I did **not** guess missing bibliographic details.

## Summary

- PDFs found in `C:\Users\Admin\Desktop\References\`: `7`
- Verified external references recovered from the PDF archive: `6`
- Incomplete references recovered from the PDF archive: `1`
- Citation placeholders still present in dissertation prose: `3`
- Direct title/author matches already used in the current dissertation draft: `0`

## Verified / Recoverable References

### 1. `2505.02123v1.pdf`

- **Status**: `VERIFIED_EXISTING_REFERENCE`
- **Title**: *DriveAgent: Multi-Agent Structured Reasoning with LLM and Multimodal Sensor Fusion for Autonomous Driving*
- **Authors**: Xinmeng Hou, Wuqi Wang, Long Yang, Hao Lin, Jinglun Feng, Haigen Min, Xiangmo Zhao
- **Year**: 2025
- **Venue**: arXiv preprint (`cs.RO`)
- **DOI / URL**: `arXiv:2505.02123v1`
- **Local source**: `C:\Users\Admin\Desktop\References\2505.02123v1.pdf`
- **Current dissertation use**: not yet cited in the current draft; best fit is Literature Review / Background
- **Note**: useful for LLM + autonomous driving + structured reasoning framing

### 2. `2604.23513v1.pdf`

- **Status**: `VERIFIED_EXISTING_REFERENCE`
- **Title**: *Large Language Model based Interactive Decision-Making for Autonomous Driving*
- **Authors**: Xinwei Dong, Jiyang Li, Jiabin Xie, Yang Yi, Tianshang Jia, Shiyu Fang, Ye Tian, Peng Hang
- **Year**: 2026
- **Venue**: arXiv preprint (`cs.RO`)
- **DOI / URL**: `arXiv:2604.23513v1`
- **Local source**: `C:\Users\Admin\Desktop\References\2604.23513v1.pdf`
- **Current dissertation use**: not yet cited in the current draft; best fit is Literature Review / Background
- **Note**: directly relevant to interactive decision-making for autonomous driving

### 3. `A Multiagent Approach to Autonomous Intersection Management.pdf`

- **Status**: `INCOMPLETE_REFERENCE`
- **Title**: *A Multiagent Approach to Autonomous Intersection Management*
- **Authors**: Kurt Dresner, Peter Stone
- **Year**: 2008
- **Venue**: Journal of Artificial Intelligence Research 31, 591-656
- **DOI / URL**: not present in the local PDF text
- **Local source**: `C:\Users\Admin\Desktop\References\A Multiagent Approach to Autonomous Intersection Management.pdf`
- **Current dissertation use**: not yet cited in the current draft; best fit is Literature Review / Background
- **Note**: strong foundational intersection-management paper, but DOI/URL should be externally verified if the final bibliography needs a fully normalized entry

### 4. `Final_Copy_2022_04_04_Safarov_K_PhD.pdf`

- **Status**: `VERIFIED_EXISTING_REFERENCE`
- **Title**: *The impact of autonomous vehicles on traffic performance at an unregulated junction*
- **Author**: Karam Safarov
- **Year**: 2022
- **Venue**: University of Bristol PhD thesis
- **DOI / URL**: `http://research-information.bristol.ac.uk`
- **Local source**: `C:\Users\Admin\Desktop\References\Final_Copy_2022_04_04_Safarov_K_PhD.pdf`
- **Current dissertation use**: not yet cited in the current draft; best fit is Literature Review / Background or method-context discussion
- **Note**: directly relevant to unregulated / unsignalised junction traffic performance

### 5. `Language Models as Zero-Shot Planners.pdf`

- **Status**: `VERIFIED_EXISTING_REFERENCE`
- **Title**: *Language Models as Zero-Shot Planners: Extracting Actionable Knowledge for Embodied Agents*
- **Authors**: Wenlong Huang, Pieter Abbeel, Deepak Pathak, Igor Mordatch
- **Year**: 2022
- **Venue**: arXiv preprint (`cs.LG`)
- **DOI / URL**: `arXiv:2201.07207v2` and `https://huangwl18.github.io/language-planner`
- **Local source**: `C:\Users\Admin\Desktop\References\Language Models as Zero-Shot Planners.pdf`
- **Current dissertation use**: not yet cited in the current draft; best fit is Literature Review / Background
- **Note**: relevant for grounded LLM planning / action selection framing

### 6. `LLM Powered Autonomous Driving.pdf`

- **Status**: `VERIFIED_EXISTING_REFERENCE`
- **Title**: *Large Language Models for Autonomous Driving (LLM4AD): Concept, Benchmark, Experiments, and Challenges*
- **Authors**: Can Cui, Yunsheng Ma, Zichong Yang, Yupeng Zhou, Peiran Liu, Juanwu Lu, Lingxi Li, Yaobin Chen, Jitesh H. Panchal, Amr Abdelraouf, Rohit Gupta, Kyungtae Han, Ziran Wang
- **Year**: 2025
- **Venue**: arXiv preprint (`cs.RO`)
- **DOI / URL**: `arXiv:2410.15281v3`
- **Local source**: `C:\Users\Admin\Desktop\References\LLM Powered Autonomous Driving.pdf`
- **Current dissertation use**: not yet cited in the current draft; best fit is Literature Review / Background
- **Note**: high-level survey / benchmark-style context for LLMs in autonomous driving

### 7. `PaLM-E embodied multimodal language model.pdf`

- **Status**: `VERIFIED_EXISTING_REFERENCE`
- **Title**: *PaLM-E: An Embodied Multimodal Language Model*
- **Authors**: Danny Driess, Fei Xia, Mehdi S. M. Sajjadi, Corey Lynch, Aakanksha Chowdhery, Brian Ichter, Ayzaan Wahid, Jonathan Tompson, Quan Vuong, Tianhe Yu, Wenlong Huang, Yevgen Chebotar, Pierre Sermanet, Daniel Duckworth, Sergey Levine, Vincent Vanhoucke, Karol Hausman, Marc Toussaint, Klaus Greff, Andy Zeng, Igor Mordatch, Pete Florence
- **Year**: 2023
- **Venue**: ICML 2022 / conference paper as distributed in the PDF
- **DOI / URL**: `arXiv:2303.03378v1` and `https://palm-e.github.io`
- **Local source**: `C:\Users\Admin\Desktop\References\PaLM-E embodied multimodal language model.pdf`
- **Current dissertation use**: not yet cited in the current draft; best fit is Literature Review / Background
- **Note**: useful for embodied multimodal language-model framing

## Dissertation citation placeholders still present

| File | Location | Current text | Meaning |
| --- | --- | --- | --- |
| `D:\Sumo\sumo_train\docs\dissertation\introduction_v1.md` | line 5 | `[CITATION NEEDED]` | general motivation sentence about unsignalised intersection control |
| `D:\Sumo\sumo_train\docs\dissertation\introduction_v1.md` | line 39 | `[CITATION NEEDED]` | research-gap sentence about reproducible pipeline-level comparison |
| `D:\Sumo\sumo_train\docs\dissertation\full_draft_v1.md` | section 2 | `[LITERATURE REVIEW TO BE COMPLETED AFTER SOURCE AUDIT]` | explicit literature-review placeholder |

## What can enter the dissertation now

The PDF archive now provides enough locally recovered material to start a real Literature Review / Background section around:

- unsignalised intersection control,
- autonomous intersection management,
- LLM-assisted autonomous driving,
- embodied / multimodal language models,
- grounded planning and decision-making,
- the thesis-context of unregulated junction performance.

## What still needs external verification

The only item that is still incomplete from the local archive alone is:

- `A Multiagent Approach to Autonomous Intersection Management.pdf` because the PDF text does not expose a DOI or URL.

If the final dissertation bibliography needs a fully normalized citation entry, that paper should be checked against an external library source later.

## Bottom line

The dissertation Literature Review no longer needs to start from zero.
It can now continue from a **real local reference archive** of 7 PDFs, with 6 complete recoverable references and 1 incomplete reference that only needs DOI/URL verification.
