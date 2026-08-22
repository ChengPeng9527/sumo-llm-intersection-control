# Literature Evidence Matrix v1

## Scope

This matrix records the local reference archive recovered from `C:\Users\Admin\Desktop\References\` and maps each paper to the dissertation research chain it supports.

The aim is not to restate every paper in isolation, but to show how the recovered literature supports the dissertation structure: autonomous intersection management, cooperative / multi-agent decision-making, language-model planning, autonomous-driving LLM work, and reliability / safety / hybrid architecture questions.

## Matrix

| Reference | Research problem | Method | Experimental setting | Key findings | Limitations | Relevance to this dissertation | Claims it can support | Claims it cannot support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dresner and Stone (2008) | How autonomous vehicles can coordinate at an intersection without relying on human-style negotiation | Reservation-based multi-agent autonomous intersection management | Simulated / algorithmic intersection coordination with reservation policies | Reservation-style coordination can reduce wasted time and injury risk compared with uncontrolled interaction, and policy choice matters | The paper itself calls for further study of safety properties, failure handling, and more flexible intersection-manager policies | Foundational prior work for unsignalised intersection coordination | Intersection control is a coordination problem; explicit reservation or policy-based control is a valid prior | Any claim about LLMs, prompt contracts, or this dissertation's exact pipeline |
| Safarov (2022) | How autonomous vehicles affect traffic performance at an unregulated junction, especially in mixed human/AV flow | PhD thesis using stylised driver models and junction-performance analysis | Unregulated junction scenarios with varying penetration levels, density, and assertiveness assumptions | Higher assertiveness generally improves performance at a busy unregulated junction; a passive vehicle can bottleneck an otherwise aggressive flow | Stylised simulation and model assumptions limit generalisation to real roads | Direct contextual support for unregulated-junction traffic behaviour | Behavioural assumptions matter; junction performance is sensitive to mixed-flow interaction style | Any claim that the thesis validates LLM control or safety layers |
| Huang et al. (2022) | Whether world knowledge in language models can be used for action planning | Zero-shot planning with semantic translation from generated plans to admissible actions | VirtualHome embodied environment tasks | Large language models can generate high-level plans, but naive plans are often not executable; semantic translation improves executability | Executability improvements can come at the cost of correctness; evaluation is tied to the task environment | Strong support for a structured output contract and executable interface | LLMs need grounding and action mapping to become executable | Any claim that unconstrained natural-language plans are directly deployable |
| Driess et al. (2023) | How to ground language models in multimodal embodied reasoning | Embodied multimodal language model combining continuous sensor modalities with pretrained language modelling | Multiple embodied tasks including manipulation planning, visual QA, and captioning | Directly incorporating visual/state encodings helps link words to percepts and broadens embodied reasoning capability | The paper is about robotics and multimodal grounding, not traffic control specifically | Supports the dissertation's emphasis on structured inputs and grounded decisions | Grounding language models in sensor/state inputs is useful for embodied decision-making | Any claim that this paper directly studies intersection control |
| Cui et al. (2025) | What LLMs can contribute to autonomous driving, and what challenges remain | Concept paper / benchmark / experiments / challenge discussion | Simulation benchmark plus real-vehicle experiments | LLMs may help from perception and scene understanding through decision-making; the paper highlights latency, deployment, safety, trust, transparency, and personalization as major issues | Broad survey-style framing; challenge list shows the field is not settled | Good background source for LLMs in autonomous driving | LLMs are relevant to autonomous driving but face unresolved system-level issues | Any claim that the paper proves a particular LLM controller is best |
| Hou et al. (2025) | How multi-agent reasoning plus sensor fusion can support autonomous driving | DriveAgent multi-agent structured reasoning with LLM and multimodal sensor fusion | Autonomous-driving experiments using camera, LiDAR, GPS, and IMU inputs | Modular agent-based reasoning can improve situational understanding and decision-making | The paper itself points to challenges around robustness in harder scenarios and sensor reliability | Supports the dissertation's structured / staged reasoning framing | Multi-agent LLM reasoning and multimodal fusion are plausible design directions | Any claim that the method directly matches SUMO intersection control |
| Dong et al. (2026) | How to support interactive decision-making for autonomous driving in mixed traffic | LLM-based interactive decision-making with semantic scene abstraction and safety constraints | Simulator-based high-conflict mixed-traffic scenarios with human-driven and autonomous vehicles | The paper reports improvements in safety, comfort, efficiency, and human-likeness, but only within the simulator scope | The authors explicitly frame the work as simulator-based and point to real-road testing and more advanced reasoning as future work | Closest conceptual neighbour to this dissertation's structured, safety-bounded pipeline | Structured scene abstraction and safety constraints can improve LLM-based driving decisions | Any claim of real-road validation or direct equivalence to the dissertation's SUMO pipeline |

## Cross-paper synthesis

These papers do not all solve the same problem, but together they form a coherent evidence chain.

1. **Autonomous intersection management is fundamentally a coordination problem.** Dresner and Stone show that explicit coordination policies are useful because the intersection bottleneck is not just vehicle motion, but access to shared conflict space. Safarov extends that viewpoint to unregulated junctions and mixed-flow behaviour, showing that behavioural assumptions change traffic performance.

2. **Language models can generate plans, but executable action mapping remains a separate problem.** Huang et al. demonstrate that zero-shot language planning is possible, yet the resulting plans are not automatically admissible in the environment. This supports the dissertation design choice to separate raw LLM output from parser, validation, fallback, and downstream control.

3. **Embodied LLM work shows why grounding matters.** PaLM-E is not a traffic paper, but it is strong evidence that language models become more useful when they are grounded in sensor/state representations rather than treated as text-only predictors.

4. **Autonomous-driving LLM work is promising but still constrained by reliability, safety, and deployment issues.** The LLM4AD paper and the DriveAgent paper both treat LLMs as part of a larger driving stack, not as a magic replacement for the rest of the system. Dong et al. further show that interactive decision-making can be improved by structured semantic abstraction and safety constraints, but also that simulator-only evidence remains a limitation.

5. **Taken together, the local literature supports a staged dissertation architecture.** The dissertation's research question is therefore not whether language models can be inserted into a driving stack at all. The more defensible question is whether a frozen, traceable, LLM-assisted decision pipeline can be compared fairly against deterministic alternatives while tracking reliability, fallback, parser success, and safety-related interventions.

## Mapping to dissertation sections

- **Autonomous Intersection Management / Background**: Dresner and Stone (2008), Safarov (2022)
- **Planning and Embodied Decision-Making**: Huang et al. (2022), Driess et al. (2023)
- **LLMs for Autonomous Driving**: Cui et al. (2025), Hou et al. (2025), Dong et al. (2026)
- **Reliability / Safety / Hybrid Architecture**: Huang et al. (2022), Cui et al. (2025), Dong et al. (2026)

## Source notes

- `A Multiagent Approach to Autonomous Intersection Management` is fully identified but still lacks a locally visible DOI/URL.
- `2505.02123v1`, `2604.23513v1`, `2201.07207v2`, `2410.15281v3`, and `2303.03378v1` are arXiv-preprint identifiers recovered from the PDFs.
- This matrix intentionally avoids adding papers that are not already present in the local archive.
