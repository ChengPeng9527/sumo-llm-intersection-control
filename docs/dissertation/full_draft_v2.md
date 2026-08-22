# Full Draft v2

## Front Matter

This draft integrates the existing dissertation chapters with the literature review recovered from the local reference archive. It keeps the formal-v2 evidence boundary unchanged and does not modify the frozen method, prompt, controller semantics, or experiment results.

## 1. Introduction

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

## 2. Literature Review / Background

# Literature Review v1

## 2.1 Autonomous Intersection Management

Autonomous intersection management has long been framed as a coordination problem rather than a pure vehicle-dynamics problem. In the classical reservation-based model proposed by Dresner and Stone, the intersection is treated as a shared resource that vehicles request and occupy according to a policy. That framing is important because it makes access control explicit: the question is not just how a vehicle moves, but how multiple vehicles can safely and efficiently negotiate a common conflict space. Their work also demonstrates that the policy at the intersection manager matters, because different policies can alter how vehicles are assigned to outbound lanes and how the system behaves under turning movements. The paper therefore establishes two enduring ideas that are still relevant here: intersection performance depends on policy, and policy needs to be visible rather than implicit.

The value of this foundation for the present dissertation is that it shifts the problem away from opaque end-to-end control. If the controller is responsible for deciding who may proceed, the decision logic must be inspectable, bounded, and measurable. That is especially important for simulation-based dissertation work, where the methodological goal is not to claim a magical autonomous capability but to compare control architectures fairly. Dresner and Stone also make clear that reservation-based coordination is not the end of the story: they explicitly point to future work on safety properties, failure handling, and more flexible intersection managers. In other words, the traditional literature already recognises that coordination is necessary, but that robustness and policy adaptation remain open questions.

Safarov's thesis extends this intersection-management perspective into unregulated junctions with mixed human-driver and autonomous-vehicle flows. This is especially relevant because the dissertation's SUMO scenario also concerns a junction where access is determined by policy and interaction style rather than traffic lights. Safarov shows that traffic performance is not only a function of the infrastructure, but also of the behavioural assumptions built into the vehicle model. Higher assertiveness generally improves performance at a busy unregulated junction, while a single passive vehicle can pull down the flow efficiency of a largely aggressive stream. That result is useful for this dissertation because it shows that interaction style can produce disproportionate effects in a shared junction, which is exactly the kind of phenomenon a cooperative decision pipeline is intended to regulate.

Taken together, these two sources support a conservative background claim: unsignalised or unregulated junctions are coordination problems in which policy design, behavioural assumptions, and access ordering all matter. They also show that the academic conversation around junction control has always involved trade-offs between efficiency and safety, not just throughput alone. That makes a staged decision architecture a reasonable research object, because the architecture can make each stage of the coordination process visible and testable.

## 2.2 Cooperative and Multi-Agent Decision-Making

The literature on autonomous intersection management already implies that a single isolated vehicle decision is rarely sufficient. Vehicles influence one another through a shared conflict space, which means the behaviour of one participant changes the feasible options for the others. In Dresner and Stone's reservation system, this is handled through explicit requests and manager policies; in Safarov's unregulated-junction setting, it appears through the interaction between assertive and passive flows. In both cases, the unit of analysis is not only the vehicle, but the interaction among multiple vehicles. That is the basic reason cooperative and multi-agent decision-making matters in this dissertation.

What is notable about the older intersection literature is that cooperation is usually encoded in a single policy mechanism. The policy may be reservation-based, priority-based, or symmetry-breaking, but the system still tends to present itself as one control logic. The dissertation is slightly different. It separates the decision process into multiple visible stages: a prompt builds the model input, the LLM proposes a structured action, a parser validates the response, a deterministic fallback handles failures, cooperative post-processing may adjust the result, and safety verification may downgrade unsafe actions. This means that the dissertation is not merely revisiting cooperation as a traffic concept; it is asking how cooperation looks when it is mediated by an LLM interface that is itself only one stage in the chain.

That distinction matters because cooperative behaviour can arise at different layers. Some systems cooperate by exchanging route-level information; others by arbitrating access to the intersection; still others by resolving conflicts after a proposal has been generated. The present project belongs to the latter category. It does not claim that language models are the same thing as cooperative controllers. Instead, it uses the cooperative control literature to justify why the LLM should not be treated as an isolated oracle. In a shared junction, the final action matters more than the raw proposal, and the final action is often shaped by bounded deterministic rules.

A second implication is that multi-agent decision-making is not just about more entities in the scene; it is about the structure of the decision process. The dissertation therefore positions itself as an evaluation of a structured coordination pipeline rather than as a generic autonomy benchmark. That framing is important for later interpretation, because it keeps the literature review aligned with the method. The project compares how different architectures handle the same interaction problem, rather than claiming that the LLM alone solves cooperation.

## 2.3 Language Models for Planning and Embodied Agents

The planning literature gives a direct reason to take language models seriously in embodied tasks. Huang et al. show that large language models can generate high-level plans in a zero-shot setting, without being explicitly trained on step-by-step action supervision for the target task. That is an important result because it demonstrates that the model can capture task structure and decompose a goal into action-like substeps. However, the same paper also demonstrates a central limitation: a semantically sensible plan is not automatically an executable plan. The generated sequence may read well in natural language but still fail to map cleanly onto the environment's admissible actions.

That result is highly relevant to this dissertation. The SUMO controller does not need the LLM to produce a creative narrative. It needs the LLM to produce a bounded action object that can be parsed into a simulator-ready decision. Huang et al. therefore support the dissertation's insistence on a structured output contract. If the model is to contribute to control, its output must be grounded in a representation that can survive parsing, validation, and deterministic execution. Their semantic translation approach is also a useful reminder that executability and correctness are not identical. A system can become more executable while still losing semantic fidelity, so the evaluation must distinguish between a valid control action and a merely fluent answer.

PaLM-E strengthens the same argument from the embodied-learning side. The paper proposes embodied multimodal language models that integrate continuous sensor modalities with language modelling, thereby linking words to percepts rather than treating language as a detached abstraction. This is important for any system that reasons about vehicles, because the vehicle state is not just text; it is a grounded configuration of positions, routes, and motion cues. PaLM-E's core lesson is that high-level language reasoning becomes more useful when it is coupled to sensor-grounded inputs. The dissertation adopts that lesson at a simpler scale: the traffic state is converted into a structured prompt so that the model sees a canonical representation of the scene, rather than a loose textual summary.

These two papers together suggest that LLMs are most defensible in embodied settings when they are used as planners or reasoners inside a constrained interface. They do not support the idea that raw language output is enough. They do support the idea that a language model can contribute to planning if the environment provides a usable state representation and if the downstream system is able to verify and execute the output. That is exactly the role the dissertation assigns to the LLM stage.

## 2.4 Large Language Models for Autonomous Driving

The autonomous-driving literature makes the relevance of LLMs more concrete. The LLM4AD paper positions large language models as potentially useful across a wide range of driving-related functions, from perception and scene understanding through to decision-making and interaction. This broad framing is important because it shows that the field is not limited to text-based driving assistants. Instead, researchers are exploring whether language models can participate in the broader autonomy stack. At the same time, the paper is careful to identify the challenges that remain: latency, deployment constraints, security and privacy, safety, trust, transparency, and personalization. Those challenges are not peripheral. They are part of the reason autonomous-driving LLMs still need careful experimental design.

DriveAgent contributes a more structured view of the same space. Its abstract describes a multi-agent autonomous driving framework in which LLM reasoning is combined with multimodal sensor fusion. The pipeline is modular: descriptive analysis, vehicle-level reasoning, environmental reasoning, and urgency-aware decision generation are separated into distinct functions. That modularity is conceptually close to the dissertation's own staged decision pipeline. It shows that modern LLM-for-driving work increasingly treats the model as one reasoning component among several, rather than as a stand-alone controller. It also reinforces the idea that multimodal sensor fusion and modular reasoning are likely to matter if the system is to handle richer driving scenes.

The interactive-decision-making paper by Dong et al. is perhaps the closest local reference to the dissertation's intent. It focuses on high-conflict mixed traffic with human-driven and autonomous vehicles, and it uses an Object-Process Methodology representation to model the scene semantically before passing it to an LLM. The paper's aim is not simply to ask whether the model can output a decision, but whether the model can parse explicit and implicit intents and make interactive decisions under safety constraints. That is a very relevant design move, because it shows that the LLM is being used as part of an interaction-aware architecture rather than as a free-form generator.

The same paper also shows why the dissertation must stay conservative in its claims. Although the reported simulator results are favourable, the authors explicitly note that the evidence is simulator-based and not broad real-world generalisation. They also point to future work involving more advanced reasoning, deeper multimodal integration, and real-road testing. The takeaway is not that the method is complete; it is that structured semantic abstraction plus safety constraints is a plausible direction for LLM-assisted decision-making. That is exactly the kind of prior work the dissertation needs.

## 2.5 Reliability, Safety, and Hybrid Decision Architectures

Across the recovered literature, reliability and safety appear as recurring constraints on what LLMs can do. Huang et al. show that output can be semantically plausible yet not executable. LLM4AD highlights latency, trust, transparency, and deployment as open challenges. Dong et al. build safety constraints into the interactive decision process itself. These papers converge on a common point: in a safety-relevant setting, raw model output is not enough. It must be grounded, bounded, and checked.

This is where the dissertation's hybrid architecture becomes methodologically sensible. By separating raw LLM proposal, parser validation, cooperative post-processing, and safety verification, the system allows each stage to be observed independently. That is not just an engineering preference; it is a response to what the literature already suggests. If a model can produce a sensible answer that still fails to execute, then the dissertation needs to record whether the failure occurred at the model stage, the parser stage, or the deterministic control stage. If a model behaves differently under different scene abstractions, then the dissertation needs to know whether that difference comes from the prompt, the contract, or the fallback policy.

A hybrid architecture also helps with interpretability. Traditional autonomous-driving and intersection-management work often assumes that the coordination policy itself is the object of study. LLM-based work introduces a new question: what happens when the policy proposal and the execution policy are not the same thing? The literature makes clear that this separation is necessary because of executability and safety issues, but it does not yet provide a single standard pipeline for evaluating the separation. That makes the dissertation's frozen prompt, frozen request configuration, and frozen controller comparison valuable as a research design, even if the final results remain modest or fallback-heavy.

Reliability should therefore be treated as a first-class research variable, not as a side effect. In this dissertation, that means provider success, parser success, fallback rate, latency, and intervention counts are not merely implementation logs; they are part of the evidence base. The literature justifies that decision because every source in this section points to some combination of grounding, boundedness, or safety as a prerequisite for useful LLM behaviour in embodied systems.

A further implication is that the dissertation should not collapse all "good" behaviour into a single traffic metric. A system can complete every run and still differ substantially in how often the LLM actually contributes, how often the parser succeeds, or how often deterministic fallback takes over. The recovered literature does not offer a standard way to measure those internal layers in intersection control, but it does consistently warn that executability, grounding, and safety are separate concerns. That is why this dissertation treats provider reliability and downstream intervention as first-class empirical variables rather than as logging noise.

## 2.6 Research Gap

The recovered literature is coherent, but it is also fragmented across problem settings. Dresner and Stone show why intersection coordination matters. Safarov shows that unregulated junction performance depends on behavioural assumptions. Huang et al. show that language models can produce plans but need semantic translation to be executable. PaLM-E shows that embodied reasoning benefits from multimodal grounding. LLM4AD, DriveAgent, and Dong et al. show that LLMs are increasingly relevant to driving, but they also make reliability, safety, latency, and simulation-to-reality transfer central concerns.

What is still missing is a controlled comparison that brings these ingredients together inside one frozen pipeline. The dissertation's question is narrower than "can LLMs be used in autonomous driving?" and narrower than "can autonomous intersection management improve efficiency?" It asks whether a structured LLM-assisted decision pipeline can be compared fairly with deterministic alternatives under the same SUMO unsignalised-intersection scenario while tracking not only traffic outputs but also provider reliability, parser success, fallback behaviour, latency, and downstream interventions. That combination is not directly supplied by any one recovered paper.

This is why the dissertation focuses on a staged architecture rather than a pure model claim. The literature supports the ingredients individually, but not yet the exact combination of frozen prompt, frozen request configuration, deterministic fallback, cooperative post-processing, and safety verification that the project evaluates. The resulting research gap is therefore methodological as much as topical: there is a need for a reproducible, pipeline-level comparison that keeps the control architecture visible and the evidence traceable.

From that gap, the dissertation's research questions follow naturally. RQ1 asks whether the LLM-assisted architecture changes traffic efficiency relative to rule-based control. RQ2 asks whether cooperative post-processing changes raw LLM behaviour in a meaningful way. RQ3 asks whether safety verification changes the final decision path and whether any safety-efficiency trade-off is observable. RQ4 asks whether the system remains stable when the scenario scales from four vehicles to eight vehicles. These questions are grounded in the recovered literature, but they are not answered by it. That makes them appropriate dissertation questions rather than retrospective confirmations.

## 3. Methodology / System Design

# Methodology v1

## 1. Overview

This dissertation studies unsignalized intersection control in SUMO using a separated decision pipeline. The method was frozen before the formal experiment and was not redesigned for the dissertation draft.

The system is not a single black-box LLM controller. It is a staged pipeline:

1. structured prompt construction,
2. live or mock provider call,
3. response parsing,
4. validation of the parsed action,
5. cooperative post-processing,
6. deterministic safety verification,
7. trace logging of raw, intermediate, and final decisions.

## 2. Research System

The repository supports four controller variants:

- rule_based
- raw_llm
- hybrid
- hybrid_safety

These controllers share the same frozen scenario family and the same canonical decision space:

- `PROCEED`
- `WAIT`
- `FREE`

## 3. Canonical Prompt and Output Contract

The canonical prompt is `P1_BASELINE`, and the output contract requires a single JSON object with per-vehicle decisions. Vehicles outside the control zone must be `FREE`. Vehicles inside the control zone must choose only `PROCEED`, `WAIT`, or `FREE`.

The prompt is intentionally simple and reproducible. It does not ask the model to justify its answer in prose.

## 4. Live Provider Configuration

The frozen live LLM configuration is:

- provider: Groq
- base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- max completion tokens: `256`
- reasoning effort: `low`
- timeout: `30.0`
- max retries: `0`

This freeze matters because it makes the dissertation evidence reproducible and avoids hidden retry or truncation behavior.

## 5. Decision Pipeline Semantics

### 5.1 Raw LLM stage

The raw LLM stage sends the structured prompt to the live provider and records the raw response.

### 5.2 Validation stage

The response parser and validator normalize invalid or missing actions to `WAIT`. This is a defensive interface step, not a behavioral redesign.

### 5.3 Cooperative post-processing

The cooperative postprocessor can promote compatible waiting vehicles when the local route conditions permit it. This stage is available in the hybrid controller variants.

### 5.4 Safety verification

The safety verifier deterministically checks conflicts and can downgrade an unsafe action. This stage is only enabled in the hybrid_safety controller.

### 5.5 Logging and traceability

The pipeline writes raw, validated, postprocessed, and final decisions to the trace so the dissertation can distinguish pipeline behavior from provider behavior.

## 6. Reproducibility Controls

The formal experiment uses frozen values for:

- research design
- prompt
- decision space
- controller semantics
- request configuration
- seeds
- scenario density
- vehicle counts
- execution matrix

The formal v2 run manifest records the freeze commit, freeze tag, prompt hash, and request configuration for each run.

## 7. What Counts as Methodology Evidence

Methodology evidence includes:

- code structure of the controller pipeline,
- frozen prompt specification,
- request configuration specification,
- logging schema,
- validation and safety logic,
- formal experiment manifest and results directory.

It does not include the final comparative conclusions. Those belong in Results and Discussion.

## 8. Methodological Caution

The dissertation should not describe the system as "pure LLM performance". The live LLM is only one stage in a larger decision pipeline, and the formal v2 traces show that fallback and deterministic intervention remain important.

## 4. Experimental Design

# Experimental Design v1

## 1. Design Goal

The formal experiment evaluates the frozen dissertation method under a controlled SUMO scenario. The goal is to compare controller variants using the same network, prompt family, request configuration, and logging schema.

## 2. Experimental Factors

The formal v2 matrix varies three factors:

- controller: `rule_based`, `raw_llm`, `hybrid`, `hybrid_safety`
- vehicle count: `4`, `8`
- seed: `1`, `2`, `3`

This yields:

- `4` controllers x `2` vehicle counts x `3` seeds = `24` planned runs

## 3. Fixed Conditions

The following elements are held constant:

- canonical prompt: `P1_BASELINE`
- scenario density: `low`
- live provider: Groq
- base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- request config: `256` max completion tokens, `low` reasoning effort, `30.0` s timeout, `0` retries
- SUMO network and route definitions
- decision space: `PROCEED / WAIT / FREE`

## 4. Execution Provenance

The formal experiment is tied to the freeze commit and tag:

- freeze commit: `7b363fa8add58ac83775eb26dd6ff0b68bea022e`
- freeze tag: `v0.9.1-formal-experiment-freeze`

The fresh formal v2 sweep was executed on branch:

- `phase-18-decision-pipeline-separation`

## 5. Outcome Measures

The dissertation can report the following outcome families:

- completion rate
- throughput
- mean waiting time
- mean speed
- episode duration
- collision count
- parser success rate
- provider success rate
- fallback rate
- request latency
- safety override count and rate
- postprocessor intervention count and rate
- decision-flow agreement / change rates

These measures are defined in `docs/research/evaluation_specification_v1.md` and are computable from the current logging schema.

## 6. Result Interpretation Plan

### RQ1

Compare rule-based control against raw LLM control.

### RQ2

Compare raw LLM against hybrid control.

### RQ3

Compare hybrid against hybrid_safety.

### RQ4

Assess 4V to 8V behavior under the frozen low-density scenario.

### RQ5

Use the trace fields to quantify how much of the final decision comes from validation, cooperative post-processing, and safety verification.

## 7. Validity Controls

The formal v2 design is strong enough for a dissertation first draft because it includes:

- counterbalanced controller order by seed,
- multiple seeds,
- two vehicle scales,
- full trace logging,
- frozen prompt and request settings,
- separate artifact storage for each run.

## 8. Validity Threats

The dissertation must still state the following threats clearly:

- provider reliability is fallback-heavy,
- completion rate is saturated at 100%, so waiting time and intervention metrics matter more than completion,
- no 16-vehicle formal v2 evidence is available,
- safety overrides are zero, so a safety-efficiency trade-off cannot be claimed from this dataset,
- sequential execution can still confound controller comparisons if not discussed carefully.

## 9. Why This Design Is Suitable for a First Draft

The design is already frozen, the runs are complete, and the dataset is reproducible from repository artifacts. That is enough to write a proper dissertation first draft without modifying the method.

## 5. Results

# Results v2



## 1. Formal Results Statistical Audit



This section re-derives the formal v2 results from the raw `step_records.csv` and `run_metadata.json` artifacts under:



`D:\Sumo\sumo_train\results\formal_experiment\dissertation_formal_v2\`



The experiment is descriptive rather than inferential. The sample size is `n = 3` per controller-scale cell, so the analysis should remain at the level of means, standard deviations, and seed-level values.



### 1.1 Formal v2 coverage



- planned runs: `24`

- completed runs: `24`

- valid runs: `24`

- missing runs: `0`

- duplicate runs: `0`

- technical reruns: `0`

- collisions: `0`

- truncations: `0`



### 1.2 Failure classification



All `2555` provider failures in the formal v2 LLM-bearing traces are classified as:



- `RateLimitError`: `2555`



Saved artifacts do not preserve HTTP status for these failed calls, so the evidence supports a provider-side throttling / rate-limit classification at the client error layer, not a parser or prompt-contract failure.



### 1.3 Decision-flow summary



Across the full formal v2 step records, the final decision source counts are:



- `DETERMINISTIC_INTERFACE_RULE`: `3522`

- `FALLBACK`: `1722`

- `LLM_RAW`: `23`

- `COOPERATIVE_POSTPROCESSOR`: `1`

- `SAFETY_VERIFIER`: `0`



This means the dissertation should treat the evaluated system as a staged pipeline, not as pure end-to-end LLM control.



## 2. Table 1: Formal Experiment Configuration



| Item | Value |

| --- | --- |

| Repository | `D:\Sumo\sumo_train` |

| Branch | `phase-18-decision-pipeline-separation` |

| Freeze commit | `7b363fa8add58ac83775eb26dd6ff0b68bea022e` |

| Freeze tag | `v0.9.1-formal-experiment-freeze` |

| Canonical prompt | `P1_BASELINE` |

| Prompt hash | `EA435588BE1CAFC099D02685060CF00223852D8834CDFCF4DAFE66233C474ECD` |

| Provider | Groq |

| Base URL | `https://api.groq.com/openai/v1` |

| Model | `openai/gpt-oss-20b` |

| Request config | `max_completion_tokens=256`, `reasoning_effort=low`, `timeout=30.0`, `max_retries=0` |

| Controllers | `rule_based`, `raw_llm`, `hybrid`, `hybrid_safety` |

| Vehicle scales | `4`, `8` |

| Seeds | `1`, `2`, `3` |

| Planned runs | `24` |

| Scenario density | `low` |



## 3. Table 2: Traffic Performance by Controller and Scale



Traffic outcomes are stable across seeds, so the seed values are shown explicitly.



| Controller | Scale | Completion rate | Mean waiting time | Mean speed | Collision count | Throughput | Seed-level values |

| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |

| Rule-based | 4V | `100%` | `82.0 ? 0.0` steps | `2.31 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[82, 82, 82]`, speed `[2.31, 2.31, 2.31]`, collisions `[0, 0, 0]` |

| Rule-based | 8V | `100%` | `82.0 ? 0.0` steps | `2.31 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[82, 82, 82]`, speed `[2.31, 2.31, 2.31]`, collisions `[0, 0, 0]` |

| Raw LLM | 4V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |

| Raw LLM | 8V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |

| Hybrid | 4V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |

| Hybrid | 8V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |

| Hybrid + Safety | 4V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |

| Hybrid + Safety | 8V | `100%` | `15.0 ? 0.0` steps | `6.80 ? 0.00` m/s | `0` | `4` | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.80, 6.80, 6.80]`, collisions `[0, 0, 0]` |



### Traffic observations



- Completion rate is saturated at `100%` in every cell, so it is not useful for separating controllers in formal v2.

- Waiting time and mean speed are the meaningful traffic discriminators in this dataset.

- Rule-based control is much more conservative than the LLM-assisted controllers under the tested low-density scenarios.



## 4. Table 3: LLM Reliability by Controller and Scale



| Controller | Scale | Provider attempts | Provider successes | Success rate | Parser success given provider success | Fallback rate | Mean latency | Seed-level provider successes | Seed-level fallback counts | Seed-level latency means |

| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |

| Raw LLM | 4V | `444` | `26` | `5.86%` | `100%` | `94.14%` | `93.64 ? 36.42` ms | `[26, 0, 0]` | `[122, 148, 148]` | `[135.68, 73.45, 71.80]` |

| Raw LLM | 8V | `444` | `3` | `0.68%` | `100%` | `99.32%` | `75.93 ? 3.50` ms | `[2, 1, 0]` | `[146, 147, 148]` | `[79.59, 75.60, 72.60]` |

| Hybrid | 4V | `444` | `22` | `4.95%` | `100%` | `95.05%` | `97.98 ? 25.58` ms | `[22, 0, 0]` | `[126, 148, 148]` | `[123.96, 97.16, 72.81]` |

| Hybrid | 8V | `444` | `18` | `4.05%` | `100%` | `95.95%` | `87.53 ? 24.99` ms | `[0, 18, 0]` | `[148, 130, 148]` | `[70.84, 116.26, 75.50]` |

| Hybrid + Safety | 4V | `444` | `22` | `4.95%` | `100%` | `95.05%` | `86.10 ? 23.77` ms | `[22, 0, 0]` | `[126, 148, 148]` | `[113.50, 73.67, 71.12]` |

| Hybrid + Safety | 8V | `444` | `18` | `4.05%` | `100%` | `95.95%` | `83.34 ? 15.05` ms | `[0, 18, 0]` | `[148, 130, 148]` | `[75.97, 100.65, 73.39]` |



### Reliability observations



- All successful provider responses were parsed successfully.

- Every failure was a provider-call failure, not a parser failure.

- Raw LLM reliability drops sharply at 8V.

- Hybrid and hybrid+safety are slightly more stable than raw LLM at 8V, but the traces remain fallback-heavy.

- Latency is not the main issue; availability/reliability is.



## 5. Seed-Level Summary



The seed-level pattern is important because it shows that the provider reliability signal is not uniform across repetitions.



### Raw LLM



- 4V seed 1: `26` provider successes, `122` fallbacks

- 4V seed 2: `0` provider successes, `148` fallbacks

- 4V seed 3: `0` provider successes, `148` fallbacks

- 8V seed 1: `2` provider successes, `146` fallbacks

- 8V seed 2: `1` provider success, `147` fallbacks

- 8V seed 3: `0` provider successes, `148` fallbacks



### Hybrid



- 4V seed 1: `22` provider successes, `126` fallbacks

- 4V seed 2: `0` provider successes, `148` fallbacks

- 4V seed 3: `0` provider successes, `148` fallbacks

- 8V seed 1: `0` provider successes, `148` fallbacks

- 8V seed 2: `18` provider successes, `130` fallbacks

- 8V seed 3: `0` provider successes, `148` fallbacks



### Hybrid + Safety



- 4V seed 1: `22` provider successes, `126` fallbacks

- 4V seed 2: `0` provider successes, `148` fallbacks

- 4V seed 3: `0` provider successes, `148` fallbacks

- 8V seed 1: `0` provider successes, `148` fallbacks

- 8V seed 2: `18` provider successes, `130` fallbacks

- 8V seed 3: `0` provider successes, `148` fallbacks



### Interpretation of seed-level variation



- The reliability problem is not a uniform failure; it is uneven across runs.

- Because the live provider success window is narrow, the dissertation should avoid treating these controller means as stable universal model properties.

- The traffic metrics are stable across seeds, but the provider path is not.



## 6. RQ-focused Results Summary



### RQ1: Rule-based vs LLM-assisted architecture



Observed result:



- LLM-assisted controllers have lower waiting time (`15` steps) and higher mean speed (`6.80 m/s`) than rule-based control (`82` steps, `2.31 m/s`) in the formal v2 scenarios.



Interpretation:



- the evaluated LLM-assisted architecture is more flow-friendly under these low-density scenarios.



Limitation:



- provider availability is poor, so this is a pipeline-level result rather than a pure LLM-only result.



### RQ2: Raw vs Hybrid



Observed result:



- hybrid slightly improves provider reliability relative to raw LLM at 8V (`18/444` vs `3/444` provider successes), but traffic metrics are unchanged in the aggregate.



Interpretation:



- cooperative post-processing exists in the pipeline, but formal v2 shows only a small visible effect on traffic outcomes.



Limitation:



- provider failures dominate the trace, so the postprocessor has limited room to influence the final behavior.



### RQ3: Hybrid vs Hybrid + Safety



Observed result:



- safety overrides are `0` in all formal v2 runs.



Interpretation:



- the safety layer is present and verified, but it is not strongly exercised by this dataset.



Limitation:



- the data cannot support a measurable safety-efficiency trade-off claim.



### RQ4: 4V vs 8V scalability



Observed result:



- traffic metrics remain stable across 4V and 8V in this low-density setup, but raw LLM reliability collapses more sharply at 8V than at 4V.



Interpretation:



- the system is operationally stable on the traffic side for both tested scales, but provider reliability becomes a serious threat at 8V.



Limitation:



- formal v2 does not include 16V, so the dissertation should not claim broader scalability.



## 7. Proposed Tables and Figures



The dissertation should use a small number of high-value tables and figures.



### Table 1



**Formal experiment configuration**



- repository, branch, freeze commit/tag, prompt, model, request config, controllers, scales, seeds, planned runs



### Table 2



**Traffic performance by controller and vehicle scale**



- completion rate

- mean waiting time

- mean speed

- collision count

- throughput

- seed values



### Table 3



**LLM reliability metrics by controller and vehicle scale**



- provider attempts

- provider successes

- success rate

- parser success given provider success

- fallback rate

- latency

- seed values



### Table 4



**Decision-flow source distribution**



- deterministic interface rule

- fallback

- raw LLM

- cooperative postprocessor

- safety verifier



### Figure 1



**Mean waiting time by controller, separated by 4V / 8V**



- y-axis: waiting time in steps

- x-axis: controller

- grouped or faceted by scale

- caption should note `n = 3` per cell and that the plot is descriptive



### Figure 2



**Mean speed by controller, separated by 4V / 8V**



- y-axis: mean speed in m/s

- x-axis: controller

- grouped or faceted by scale

- caption should note the same low-density scenario and `n = 3`



### Figure 3



**Provider success and fallback rate by LLM controller and scale**



- y-axis: percentage of provider attempts

- x-axis: controller

- grouped by scale

- show success and fallback together



### Figure 4



**Latency by LLM controller and scale**



- y-axis: mean provider latency in ms

- x-axis: controller

- grouped by scale



## 8. Caption-ready wording



Short caption templates:



- **Table 2**: "Descriptive traffic performance summary for the formal v2 dataset. The table reports mean values across three seeds for each controller-scale cell."

- **Table 3**: "Live provider reliability summary for the formal v2 dataset. The table reports provider attempts, successful responses, parser success, fallback rate, and latency."

- **Figure 1**: "Mean waiting time by controller and vehicle scale in the formal v2 experiment. Error bars represent one standard deviation across three seeds."

- **Figure 2**: "Mean speed by controller and vehicle scale in the formal v2 experiment. Error bars represent one standard deviation across three seeds."

- **Figure 3**: "Provider success and fallback rate for live LLM-bearing controllers in the formal v2 experiment."

- **Figure 4**: "Mean provider latency for live LLM-bearing controllers in the formal v2 experiment."



## 9. Safe Results Wording



A defensible dissertation sentence is:



> The formal v2 dataset shows collision-free completion across all 24 runs, with lower waiting time and higher speed for the LLM-assisted architecture than for the rule-based baseline, but the live-provider traces are heavily fallback-driven and must therefore be interpreted at the pipeline level rather than as pure model performance.

## 6. Discussion

# Discussion v1



## 1. Discussion framing



This discussion separates four kinds of statements:



- **OBSERVED RESULT**: what the formal v2 artifacts actually show

- **INTERPRETATION**: the most defensible meaning of the result

- **LIMITATION**: what the result does not establish

- **SPECULATION**: a possible explanation that is not directly proven



The dissertation should preserve that separation throughout the chapter.



## 2. RQ1: What can the results actually support?



**OBSERVED RESULT**



- The LLM-assisted architecture has lower waiting time (`15` steps) and higher mean speed (`6.80 m/s`) than rule-based control (`82` steps, `2.31 m/s`) in the formal v2 scenarios.

- Completion rate is `100%` for every controller and scale, so completion does not differentiate the systems.



**INTERPRETATION**



- Under the evaluated low-density settings, the LLM-assisted decision pipeline appears more flow-friendly than the deterministic baseline.



**LIMITATION**



- The formal v2 data do not prove that the LLM alone caused the improvement.

- The live-provider path is fallback-heavy, so the observed traffic advantage belongs to the pipeline, not to a pure model-only controller.



**SPECULATION**



- The structured prompt plus cooperative pipeline may have encouraged more permissive decisions in compatible traffic conditions.



## 3. Why is waiting time lower for the LLM-assisted architecture?



**OBSERVED RESULT**



- LLM-assisted runs have much lower waiting time than rule-based runs in both 4V and 8V formal v2 cells.



**INTERPRETATION**



- The LLM-assisted pipeline is less conservative than the rule-based baseline in this low-density scenario.

- The raw and hybrid controllers both include a decision pipeline that can produce `PROCEED` more readily than the baseline interface rule.



**LIMITATION**



- Because provider success is low, especially at 8V, the result cannot be treated as strong evidence about the intrinsic quality of the model?s decisions.



**SPECULATION**



- Some of the observed difference may come from cooperative promotion of compatible flows and from the way fallback handling maps uncertain states into executable actions.



## 4. Does the advantage really come from the LLM?



**OBSERVED RESULT**



- Provider success is only `109 / 2664` across formal v2.

- Most live provider attempts fail and therefore fall back.



**INTERPRETATION**



- The observed performance advantage cannot be attributed solely to direct LLM decisions.

- The system performance is better described as a pipeline effect: the prompt, parser, validation, interface rules, fallback policy, and the occasional live LLM success all contribute.



**LIMITATION**



- The current evidence does not isolate the LLM contribution cleanly enough to claim that the LLM itself is responsible for the entire performance gap.



## 5. RQ2: Why did hybrid not clearly improve traffic metrics?



**OBSERVED RESULT**



- Hybrid and raw LLM have the same completion rate and collision count.

- Hybrid does not improve the traffic metrics in a way that is visible in the aggregate formal v2 table.

- Cooperative post-processing is rare: only `1` intervention across the full formal v2 dataset.



**INTERPRETATION**



- The cooperative layer exists, but it is not exercised often enough in formal v2 to materially change the aggregate traffic metrics.



**LIMITATION**



- A sparse intervention count makes it hard to argue that cooperative post-processing is a strong effect in this dataset.



**SPECULATION**



- The provider reliability ceiling may be the real bottleneck; if the live LLM is unavailable most of the time, the cooperative layer has little opportunity to reshape the trajectory.



## 6. RQ2 / RQ4: What does the 8V reliability difference mean?



**OBSERVED RESULT**



- Raw LLM 8V has only `3` provider successes out of `444` attempts.

- Hybrid and hybrid+safety each have `18` provider successes out of `444` attempts at 8V.



**INTERPRETATION**



- The hybrid architecture appears more robust than raw LLM at 8V.

- The raw path is the most fragile live-provider configuration in the formal v2 dataset.



**LIMITATION**



- The improvement remains modest relative to the total number of failed attempts, so it should not be overstated.



**SPECULATION**



- The different reliability profiles may reflect execution-order sensitivity or load sensitivity in the live-provider path.



## 7. RQ3: How should safety override = 0 be interpreted?



**OBSERVED RESULT**



- Safety overrides are zero across all formal v2 runs.

- Collisions are also zero across all formal v2 runs.



**INTERPRETATION**



- The safety layer was available and verified, but formal v2 did not require it to change any action.

- The data therefore support a statement of verified safety plumbing, not a measurable safety-efficiency trade-off.



**LIMITATION**



- Zero safety overrides do not prove that the safety verifier is unnecessary.

- They only show that the current low-density dataset did not force it to intervene.



**SPECULATION**



- The low-density scenario may simply be too conservative to activate the safety layer often.



## 8. RQ4: How strong is the scalability claim?



**OBSERVED RESULT**



- The formal v2 dataset covers only `4V` and `8V`.

- Traffic metrics are stable across these two scales in the low-density setting.

- Raw provider reliability worsens markedly at `8V`.



**INTERPRETATION**



- The system appears to remain operational across the tested low-density scales, but the live provider path becomes less reliable as scale increases.



**LIMITATION**



- There is no formal v2 evidence for `16V`.

- There is no basis for a broad scalability claim beyond the tested low-density range.



**SPECULATION**



- A denser or more congested scenario would likely magnify the reliability bottleneck, but that remains untested here.



## 9. Provider reliability as a validity threat



**OBSERVED RESULT**



- All `2555` failures are recorded as `RateLimitError`.

- The artifacts do not preserve HTTP status for those failed requests.



**INTERPRETATION**



- Provider reliability is the main validity threat in formal v2.

- The dissertation must treat provider availability as part of the system under evaluation, not as a noise source that can be ignored.



**LIMITATION**



- Because the failure artifacts do not expose HTTP status, the exact provider-side mechanism cannot be proven beyond the recorded exception type.



**SPECULATION**



- The difference between smoke-style success and formal-sweep failure may be explained by load, repetition, or provider throttling over time.



## 10. What the study really proves



**OBSERVED RESULT**



- The formal v2 experiment is complete, reproducible, collision-free, and traceable.

- The LLM-assisted pipeline shows lower waiting time than the rule-based baseline in the tested low-density scenarios.

- Live-provider reliability is weak and uneven, especially for raw LLM at 8V.



**INTERPRETATION**



- The dissertation can legitimately claim that the staged architecture works and that, under the tested scenarios, the LLM-assisted pipeline is associated with better traffic efficiency.



**LIMITATION**



- The study does not prove pure LLM superiority.

- It does not prove a safety trade-off.

- It does not prove general scalability to denser or larger scenarios.



**SPECULATION**



- The most plausible story is that the architecture is useful as a decision pipeline, but its LLM component is currently too unreliable to stand alone.



## 11. Recommended discussion sentence



> The formal v2 evidence suggests that a structured LLM-assisted decision pipeline can reduce waiting time relative to a rule-based baseline in the evaluated low-density scenarios, but the result is mediated by substantial provider fallback and therefore should be interpreted as pipeline-level behavior rather than a demonstration of intrinsic LLM superiority.

## 7. Limitations

# Limitations v1



This chapter should only contain limitations that are directly supported by the current evidence.



## 1. Only 4V and 8V formal scenarios



- The formal v2 matrix evaluates only `4` and `8` vehicles.

- There is no formal v2 evidence for `16V`.

- Any scalability claim beyond `8V` would be unsupported.



## 2. Only three seeds



- The formal v2 dataset uses seeds `1`, `2`, and `3`.

- This is sufficient for descriptive reporting, but not for strong generalisation.



## 3. Simulation-only evaluation



- All formal v2 evidence comes from SUMO simulation.

- There is no physical robot or real traffic validation.



## 4. Single intersection topology



- The experiment uses one unsignalized intersection setting.

- Results cannot be generalized to multi-intersection networks without new evidence.



## 5. External LLM provider dependency



- The live LLM path depends on Groq.

- Provider availability and throttling are part of the system?s observed behavior.



## 6. High provider failure / fallback dependence



- Provider successes: `109`

- Provider failures: `2555`

- Fallback decisions dominate the live-provider traces.



This means the dissertation must not describe the result as pure LLM performance.



## 7. No observed safety overrides



- Safety overrides are `0` across the formal v2 dataset.

- This prevents a strong safety-efficiency trade-off claim.



## 8. Limited postprocessor intervention



- Cooperative post-processing is observed only once across the full formal v2 sweep.

- The cooperative mechanism is present, but its effect size is sparse in this dataset.



## 9. Completion-rate saturation



- Completion rate is `100%` in every formal v2 run.

- Because of that saturation, completion rate is not useful for separating controllers.

- Waiting time, speed, and provider reliability are more informative.



## 10. No evidence for dense-traffic generalisation



- The formal v2 runs are low-density.

- The evidence does not support claims about dense traffic or stressful congestion.



## 11. Sequential reliability confound



- The provider reliability pattern is uneven across seeds and controller order.

- This is a validity threat for interpreting controller differences as if they were purely algorithmic.



## 12. What should not be claimed



The dissertation should not claim:



- that LLM-assisted control is universally better,

- that safety verification improved metrics in formal v2,

- that the system scales to 16V,

- that the raw model alone explains the observed traffic advantage,

- that the study generalizes to real-world traffic without further validation.

## 8. Conclusion and Future Work

# Conclusion and Future Work v1



## 1. What was done?



This dissertation designed, implemented, and evaluated a structured LLM-assisted decision pipeline for unsignalised intersection control in SUMO. The system separates the decision stack into raw LLM proposal, validation, cooperative post-processing, deterministic safety verification, and trace logging. The evaluation used a frozen formal experiment matrix with four controllers, two vehicle scales, and three seeds.



The resulting formal v2 dataset is complete and collision-free:



- `24/24` runs completed

- `24/24` runs valid

- completion rate `100%` in every formal v2 run

- collision count `0`



## 2. What are the main findings?



The strongest traffic-side finding is that the LLM-assisted architecture is associated with lower waiting time and higher mean speed than the rule-based baseline in the tested low-density scenarios.



- rule-based waiting time: about `82` steps

- LLM-assisted waiting time: about `15` steps

- rule-based mean speed: about `2.31 m/s`

- LLM-assisted mean speed: about `6.80 m/s`



However, the live-provider traces show that this traffic advantage should not be presented as pure LLM performance. The formal v2 evidence shows heavy fallback dependence:



- provider attempts: `2664`

- provider successes: `109`

- provider failures: `2555`

- parser successes: `109`

- fallback-heavy behavior dominates the live LLM-bearing runs



Therefore, the most defensible conclusion is that the project demonstrates a functioning LLM-assisted decision pipeline, not a clean proof of pure model superiority.



## 3. Answers to the research questions



### RQ1



**Question:** Can an LLM-assisted architecture improve traffic efficiency relative to rule-based control?



**Answer:** Under the evaluated low-density scenarios, the LLM-assisted architecture exhibited lower waiting time and higher speed than the rule-based baseline. This supports a cautious claim that the architecture can improve traffic efficiency in this specific evaluation setting.



### RQ2



**Question:** Does cooperative post-processing change the behavior of raw LLM decisions in a meaningful way?



**Answer:** Cooperative post-processing exists in the pipeline, but formal v2 shows only a rare visible effect. There was only one recorded postprocessor intervention in the full formal v2 dataset. The effect is therefore present but small in the available evidence.



### RQ3



**Question:** What effect does deterministic safety verification have, and is there a safety-efficiency trade-off?



**Answer:** Safety verification was present and traceable, but it did not trigger any overrides in formal v2. The dataset therefore supports a statement that the safety layer is verified and available, but not that it produced a measurable safety-efficiency trade-off in this study.



### RQ4



**Question:** How does the system behave when scale increases from 4 vehicles to 8 vehicles?



**Answer:** The traffic metrics remain stable across 4V and 8V in the low-density setting, but provider reliability becomes more fragile, especially for raw LLM at 8V. This supports only a conservative scalability statement.



## 4. What is the most important limitation?



The most important limitation is provider reliability.



The formal v2 results are not invalid, but they are strongly mediated by live-provider fallback behavior. This affects how the results should be interpreted:



- the traffic metrics are pipeline outcomes,

- not pure direct LLM decision quality,

- and not a proof that the LLM itself is consistently available or robust.



Other limitations matter too, but none is more important than the provider reliability threat for this dissertation.



## 5. Overall research contribution



The dissertation's main contribution is not a claim of universal superiority. Its contribution is a reproducible, traceable comparison of controller architectures for unsignalised intersection control, together with an explicit analysis of how provider availability and fallback behavior shape the final system behavior.



That is a useful research contribution because it makes clear where the LLM helps, where it fails, and how much of the final behavior is attributable to deterministic pipeline stages.



## 6. Future work



The future work should follow directly from the real limitations of the current study.



### 6.1 Higher-density traffic and larger-scale evaluation



The current formal v2 matrix covers only 4V and 8V. A natural next step is to evaluate higher-density traffic and larger vehicle counts, including 16V or beyond, to test whether the pipeline remains operational under more demanding conditions.



### 6.2 More seeds



The formal v2 experiment uses three seeds. More seeds would improve the robustness of the descriptive comparison and help distinguish stable effects from run-level variation.



### 6.3 Additional intersection layouts



The current study uses one unsignalised intersection topology. Future work could evaluate additional intersection geometries or route structures to test whether the pipeline generalises beyond the current configuration.



### 6.4 Local or self-hosted LLM comparison



Because live provider reliability is a major validity threat, a useful follow-up would be to compare the current hosted provider path against a local or self-hosted model under the same prompt and decision contract. That would help separate model quality from provider availability.



### 6.5 Controlled fallback ablation



Future work could examine how much of the observed traffic behavior comes from fallback handling. A controlled fallback ablation would help quantify the contribution of deterministic fallback to the final system behavior.



### 6.6 Safety-triggered scenarios



The current dataset contains no safety overrides. Future experiments could include scenario designs that are more likely to trigger the safety verifier, so the dissertation can measure whether safety changes the final decision behavior in practice.



### 6.7 Real-time or hardware-in-the-loop validation



The present work is simulation-based. A later stage could move toward real-time or hardware-in-the-loop validation if the method is to be considered for more realistic deployment contexts.



## 7. Final conclusion



The dissertation shows that a frozen, traceable LLM-assisted decision pipeline can be evaluated systematically in SUMO and can exhibit lower waiting time than a rule-based baseline in the tested scenarios. At the same time, the formal v2 evidence makes clear that live-provider reliability is a first-order validity issue, so the final claim must stay at the level of pipeline behavior rather than pure LLM intelligence.

## 9. References

See `references_v1.md` for the consolidated bibliography list recovered from the local reference archive.

## 10. Notes on Integration

The literature review now provides the missing bridge between the background problem and the staged decision-pipeline method. The rest of the dissertation remains aligned with the frozen formal v2 evidence.
