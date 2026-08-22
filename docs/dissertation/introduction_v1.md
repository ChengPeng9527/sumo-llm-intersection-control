# Introduction v1



## 1. Background and motivation



Unsignalised intersection coordination remains a difficult problem because multiple vehicles may approach the same conflict space with competing priorities, partially overlapping routes, and limited room for conservative control. In simulation-based autonomous intersection management, a controller must balance traffic efficiency, safety, and traceability without turning the system into an opaque black box (Dresner and Stone, 2008; Safarov, 2022).



This dissertation investigates whether a structured LLM-assisted decision pipeline can support cooperative decision-making at an unsignalised intersection while preserving deterministic fallback behavior, cooperative post-processing, and safety verification.



The motivation for the work is practical as well as methodological. In many LLM-based control demonstrations, the model is treated as if it were the whole controller. That makes it difficult to separate the model's contribution from validation logic, rule-based fallback, cooperative heuristics, and safety checks. The present project addresses that issue by making the decision pipeline explicit and auditable.



## 2. Problem statement



The central problem is not whether an LLM can emit a valid JSON object, but whether a multi-stage decision architecture can integrate:



- structured vehicle state,

- cooperative reasoning,

- deterministic fallback handling,

- postprocessing,

- safety verification,

- and reproducible trace logging



in a way that can be evaluated fairly under a controlled SUMO scenario.



The repository therefore focuses on a traceable decision pipeline rather than a single end-to-end model call.



## 3. Research gap



The research gap is the lack of a fully frozen, traceable, controlled comparison of multiple intersection-control architectures under a shared scenario, prompt contract, and evaluation protocol.



The repository evidence shows that this project is not trying to claim a new general-purpose autonomous driving method. Instead, it aims to compare:



- rule-based control,

- raw LLM control,

- hybrid LLM control with cooperative post-processing,

- hybrid LLM control with cooperative post-processing and deterministic safety verification



within the same SUMO setup.



This gap can be stated conservatively as follows: there is still a need for a reproducible, pipeline-level comparison of LLM-assisted cooperative intersection control under a frozen prompt, a frozen request configuration, and a frozen evaluation matrix, especially when the broader literature spans autonomous intersection management, grounded planning, embodied multimodal reasoning, and LLM-assisted driving rather than one fixed experimental pipeline (Dresner and Stone, 2008; Huang et al., 2022; Driess et al., 2023; Cui et al., 2025; Dong et al., 2026).



## 4. Aim



The aim of the dissertation is to evaluate whether a structured LLM-assisted decision pipeline can improve cooperative decision-making at an unsignalised intersection while remaining traceable, reproducible, and deterministically bounded by validation and safety layers.



## 5. Research objectives



1. Design and implement a comparable set of controller architectures for a SUMO-based unsignalised intersection.

2. Separate the raw LLM proposal, validation, cooperative post-processing, and safety verification stages in the decision pipeline.

3. Freeze the canonical prompt and request configuration to support reproducible evaluation.

4. Execute a controlled formal experiment across controller, scale, and seed factors.

5. Measure traffic outcomes, provider reliability, parser success, fallback behavior, latency, and intervention rates.

6. Interpret the results conservatively, with clear distinction between observed result, interpretation, and limitation.



## 6. Research questions



The dissertation asks:



- **RQ1**: Can an LLM-assisted architecture improve traffic efficiency relative to rule-based control at an unsignalised intersection?

- **RQ2**: Does cooperative post-processing change the behavior of raw LLM decisions in a meaningful way?

- **RQ3**: What effect does deterministic safety verification have on the hybrid pipeline, and does it introduce a safety-efficiency trade-off?

- **RQ4**: How does the system behave when traffic scale increases from 4 vehicles to 8 vehicles under the frozen low-density scenario?



A fifth traceability question is useful for interpretation, but the main dissertation claims should be centered on RQ1-RQ4.



## 7. Proposed approach



The implemented approach is a staged decision pipeline:



1. Build a structured prompt from the current traffic state, route conflict matrix, and policy hints.

2. Send the prompt to a live or mock provider.

3. Parse the provider response into vehicle-level decisions.

4. Normalize invalid or missing actions to `WAIT`.

5. Apply a deterministic interface rule so vehicles outside the control zone become `FREE`.

6. Apply cooperative post-processing where compatible traffic flow can be promoted.

7. Apply deterministic safety verification where conflicting actions must be downgraded.

8. Log raw, validated, postprocessed, and final decisions separately.



This is not a pure LLM controller. It is a pipeline in which the LLM is one decision stage.



## 8. Contributions



The dissertation makes the following defensible contributions:



1. It designs and implements a set of comparable controller architectures for a SUMO-based unsignalised intersection.

2. It establishes a decision pipeline that combines an LLM proposal with deterministic fallback, cooperative post-processing, and safety verification.

3. It evaluates the architectures in a controlled SUMO matrix with frozen prompt, frozen request configuration, fixed seeds, and fixed vehicle scales.

4. It produces traceable evidence on provider reliability, parser success, fallback behavior, and downstream interventions.

5. It shows that provider reliability is a material part of the experimental validity story, not just an implementation detail.



These are engineering and evaluation contributions. The repository evidence does not justify a stronger novelty claim than that.



## 9. Dissertation structure



- **Chapter 1: Introduction** - problem, aim, gap, objectives, and questions.

- **Chapter 2: Literature Review / Background** - intersection control, cooperative decision-making, LLM-assisted control, and validation/safety concepts.

- **Chapter 3: Methodology / System Design** - pipeline architecture, prompt, parser, cooperative logic, safety logic, logging.

- **Chapter 4: Experimental Design** - formal matrix, scenarios, seeds, metrics, and execution provenance.

- **Chapter 5: Results** - traffic performance, reliability, and decision-flow evidence.

- **Chapter 6: Discussion** - interpretation of what the evidence does and does not support.

- **Chapter 7: Limitations** - scope, validity threats, and generalisation limits.

- **Chapter 8: Conclusion and Future Work** - final answer, summary contribution, and next steps.



## 10. Chapter-level caution



The introduction must not overclaim:



- it should not say that LLM control is universally superior,

- it should not say that safety verification improved metrics in formal v2,

- it should not say that real-world driving has been validated,

- it should not say that dense-traffic scalability has been proven.



The formal v2 evidence supports a careful claim about a structured LLM-assisted pipeline under a frozen SUMO scenario, not a broad autonomous-driving breakthrough.

