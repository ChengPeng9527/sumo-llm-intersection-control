# Title Page (Placeholder)

University of Bristol MSc Robotics Dissertation

Title: [Insert final dissertation title here]
Author: [Insert name here]
Supervisor: [Insert supervisor name here]
Submission date: [Insert date here]

## Abstract

This dissertation investigates whether a structured large language model (LLM)-assisted decision pipeline can support unsignalised intersection control in Simulation of Urban MObility (SUMO). The system separates prompt construction, live-provider request handling, parsing, deterministic validation, cooperative post-processing, and safety verification so that each stage can be observed independently. The final evidence boundary is fixed: 4-vehicle results are taken from the valid formal_v2 evidence, while 8-vehicle results are taken from the corrected formal_v4 evidence. Across that boundary, the LLM-assisted pipeline exhibits lower waiting time and higher mean speed than the rule-based baseline in the tested scenarios, but live-provider reliability remains the main validity threat. Provider success is very low and fallback-heavy, so the dissertation interprets the result as pipeline behaviour rather than pure LLM performance. The study therefore contributes a reproducible comparison of controller architectures, together with an explicit account of how provider reliability and fallback handling shape the observed system behaviour.

## Table of Contents (Placeholder)

[Generate the final table of contents in Word.]

# 1 Introduction

## 1. Background and motivation



Unsignalised intersection coordination remains a difficult problem because multiple vehicles may approach the same conflict space with competing priorities, partially overlapping routes, and limited room for conservative control. In simulation-based autonomous intersection management, a controller must balance traffic efficiency, safety, and traceability without turning the system into an opaque black box (Dresner and Stone, 2008; Safarov, 2022).



This dissertation investigates whether a structured LLM-assisted decision pipeline can support cooperative decision-making at an unsignalised intersection while preserving deterministic fallback behaviour, cooperative post-processing, and safety verification.



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

5. Measure traffic outcomes, provider reliability, parser success, fallback behaviour, latency, and intervention rates.

6. Interpret the results conservatively, with clear distinction between observed result, interpretation, and limitation.



## 6. Research questions



The dissertation asks:



- **RQ1**: Can an LLM-assisted architecture improve traffic efficiency relative to rule-based control at an unsignalised intersection?

- **RQ2**: Does cooperative post-processing change the behaviour of raw LLM decisions in a meaningful way?

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

4. It produces traceable evidence on provider reliability, parser success, fallback behaviour, and downstream interventions.

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



Accordingly, the dissertation should be read as a controlled comparison of controller architectures under a frozen SUMO evidence boundary, not as a claim of universal LLM superiority, real-world validation, or dense-traffic scalability.
# 2 Literature Review

## 2.1 Autonomous intersection management and unsignalised junction control

Autonomous intersection management frames the junction as a shared coordination problem rather than a pure vehicle-dynamics problem. Dresner and Stone (2008) are the most important foundational reference in the recovered archive because they show that intersection performance depends on the access policy governing a conflict space. Their reservation-based framing makes two points that remain relevant for this dissertation. First, a controller must decide who may proceed into the junction. Second, the policy itself needs to be visible and auditable if performance is to be compared fairly.

Safarov (2022) extends that logic to an unregulated junction context. His thesis shows that traffic performance depends not only on infrastructure but also on the behavioural assumptions encoded in the vehicle model. This is directly relevant to the present SUMO dissertation because the project also evaluates a policy-driven junction rather than a signalised system. The key lesson is that interaction style matters: a single conservative participant can alter flow efficiency in a shared conflict space.

Taken together, these sources support a conservative background claim: unsignalised junctions are coordination problems in which policy design, behavioural assumptions, and access ordering all matter. They also show that efficiency and safety have always been joint concerns in the intersection-management literature.

## 2.2 Cooperative and multi-agent decision-making

The intersection literature already implies that a single isolated vehicle decision is rarely enough. Vehicles influence one another through a shared conflict space, so the unit of analysis is the interaction among multiple participants, not just one vehicle in isolation.

The present dissertation makes that interaction visible through a staged decision pipeline. The controller is not a black box. Instead, the method separates prompt construction, live-provider proposal, parsing, validation, deterministic fallback, cooperative post-processing, and safety verification. That design is consistent with the recovered literature because the literature repeatedly treats policy, access ordering, and safety as distinct from raw motion generation.

The cooperative aspect is therefore not presented as an abstract claim that the model is "cooperative" in itself. It is presented as a bounded control stage that may alter the final decision when local traffic conditions permit it. The literature supports that separation because it shows that coordination is an explicit policy problem, not an emergent property that can be assumed from a fluent model output.

## 2.3 Language models as planners and embodied reasoners

Huang et al. (2022) provide the clearest justification for using language models in a constrained planning role. Their zero-shot planner framing shows that an LLM can generate high-level action structure, but it also exposes a key limitation: a semantically plausible plan is not automatically executable. That distinction matters for this dissertation because the SUMO controller does not need a prose explanation. It needs a bounded, simulator-ready action object that can be parsed and validated.

PaLM-E (Driess et al., 2023) strengthens the same point from the embodied multimodal side. The paper links language reasoning with grounded sensor-like inputs, showing that language models become more useful when they are coupled to a structured view of the world rather than detached text alone. The present dissertation adopts that lesson at a simpler scale by converting the traffic scene into a canonical structured prompt instead of asking the model to infer the state from loosely phrased text.

The combined lesson is straightforward: language models are most defensible in embodied settings when they are treated as one stage in a constrained, grounded pipeline. They are not treated as self-sufficient controllers.

## 2.4 Large language models for autonomous driving

The autonomous-driving literature makes the relevance of LLMs more concrete. LLM4AD (Cui et al., 2025) frames language models as potentially useful across several parts of the driving stack, but it also emphasises challenges such as latency, trust, transparency, deployment constraints, safety, and privacy. These are not side issues. They are part of why a dissertation on LLM-assisted control must evaluate reliability as well as traffic outcome.

DriveAgent (Hou et al., 2025) contributes a more modular view of the same space. Its structured reasoning pipeline separates different reasoning functions rather than treating the model as a monolithic decision maker. That modularity is conceptually close to the present dissertation because the current project also uses a separated decision pipeline with explicit intermediate stages.

Dong et al. (2026) are perhaps the closest recovered paper to the current project in spirit. Their interactive decision-making work treats the driving scene as an explicit decision problem under safety constraints and uses a structured representation before invoking the LLM. That design move is important because it shows that the field is already moving toward traceable interaction-aware architectures rather than pure free-form generation.

## 2.5 Reliability, safety, and hybrid pipeline design

Across the recovered archive, reliability and safety appear as recurring constraints on LLM use. Huang et al. (2022) show that output can be plausible but not executable. LLM4AD (Cui et al., 2025) identifies operational challenges that remain open. Dong et al. (2026) build safety constraints into the decision process itself. The shared implication is that raw model output is not enough in a safety-relevant setting.

This is the justification for the dissertation's hybrid architecture. By separating raw proposal, parser validation, deterministic fallback, cooperative post-processing, and safety verification, the system allows each stage to be observed independently. That is not merely an engineering preference. It is an experimental necessity if the dissertation wants to know where a failure or decision came from.

The literature also supports using provider reliability as an empirical variable rather than hidden infrastructure noise. If a live provider is unreliable, then the final traffic behaviour is the behaviour of the pipeline under constrained provider availability. That is precisely why the dissertation logs provider success, parser success, fallback rate, latency, post-processing, and safety intervention.

## 2.6 Research gap

The recovered literature is coherent, but it is fragmented across problem settings. Dresner and Stone (2008) show why intersection coordination matters. Safarov (2022) shows that unregulated-junction performance depends on behavioural assumptions. Huang et al. (2022) show that language models can produce plans but need semantic translation to be executable. PaLM-E (Driess et al., 2023) shows that embodied reasoning benefits from grounding. LLM4AD (Cui et al., 2025), DriveAgent (Hou et al., 2025), and Dong et al. (2026) show that LLMs are increasingly relevant to driving, but they also make reliability, safety, latency, and simulation-to-reality transfer central concerns.

What is still missing is a controlled comparison that brings these ingredients together inside one frozen pipeline. The present dissertation is narrower than "can LLMs be used in autonomous driving?" and narrower than "can autonomous intersection management improve efficiency?" It asks whether a structured LLM-assisted decision pipeline can be compared fairly with deterministic alternatives under the same SUMO unsignalised-intersection scenario while tracking traffic outcomes, provider reliability, parser success, fallback behaviour, latency, and downstream interventions.

That gap is methodological as much as topical. The literature supports the ingredients individually, but not the exact combination of frozen prompt, frozen request configuration, deterministic fallback, cooperative post-processing, and safety verification that this dissertation evaluates. From that gap, the research questions follow naturally:

- **RQ1:** Does the LLM-assisted architecture change traffic efficiency relative to rule-based control?
- **RQ2:** Does cooperative post-processing change raw LLM behaviour in a measurable way?
- **RQ3:** Does deterministic safety verification change the final decision path, and is any safety-efficiency trade-off observable?
- **RQ4:** Does the system remain stable when the scenario scales from four vehicles to eight vehicles?

These questions are grounded in the recovered literature, but they are not answered by it. That makes them appropriate dissertation questions rather than retrospective confirmations.

# 3 Methodology / System Design

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

This freeze matters because it makes the dissertation evidence reproducible and avoids hidden retry or truncation behaviour.

## 5. Decision Pipeline Semantics

### 5.1 Raw LLM stage

The raw LLM stage sends the structured prompt to the live provider and records the raw response.

### 5.2 Validation stage

The response parser and validator normalize invalid or missing actions to `WAIT`. This is a defensive interface step, not a behavioural redesign.

### 5.3 Cooperative post-processing

The cooperative postprocessor can promote compatible waiting vehicles when the local route conditions permit it. This stage is available in the hybrid controller variants.

### 5.4 Safety verification

The safety verifier deterministically checks conflicts and can downgrade an unsafe action. This stage is only enabled in the hybrid_safety controller.

### 5.5 Logging and traceability

The pipeline writes raw, validated, postprocessed, and final decisions to the trace so the dissertation can distinguish pipeline behaviour from provider behaviour.

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

# 4 Experimental Design

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

Assess 4V to 8V behaviour under the frozen low-density scenario.

### RQ5

Use the trace fields to quantify how much of the final decision comes from validation, cooperative post-processing, and safety verification.

## 7. Validity Controls

The formal v2 design includes:

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

# 5 Results

- valid 4V evidence from `results/formal_experiment/dissertation_formal_v2/`
- corrected 8V evidence from `results/formal_experiment/dissertation_formal_v4/`

The nominal 8V `formal_v2` traces are excluded because the raw traces show only 4 observed / departed / arrived vehicles.

## 1. Experimental validity

- Valid 4V evidence: 12 runs, 4 observed / departed / arrived vehicles per run, 0 collisions.
- Corrected 8V evidence: 12 runs, 8 observed / departed / arrived vehicles per run, 0 collisions.
- Corrected dissertation evidence base: 24 valid runs total.

### Table 1. Experimental configuration

| Dataset | Controllers | Vehicle scales | Seeds | Valid runs used | Status |
|---|---:|---:|---:|---:|---|
| `formal_v2` | 4 | 4V + 8V planned | 1, 2, 3 | 12 valid 4V runs | 4V valid, 8V invalid |
| `formal_v4` | 4 | 8V | 1, 2, 3 | 12 corrected 8V runs | Fully valid 8V evidence |
| Corrected dissertation evidence | 4 | 4V + 8V | 1, 2, 3 | 24 valid runs total | 4V from `formal_v2`, 8V from `formal_v4` |

## 2. Traffic performance

The analysis remains descriptive because each controller-scale cell has `n = 3` seeds.

### Table 2. Traffic performance by controller and scale

| Controller | Scale | Completion rate | Mean waiting time | Mean speed | Throughput | Collision count | Seed-level values |
|---|---|---:|---:|---:|---:|---:|---|
| Rule-based | 4V | 100% | 82.000 卤 0.000 [82.000, 82.000] steps | 2.310 卤 0.000 [2.310, 2.310] m/s | 4.000 卤 0.000 [4.000, 4.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[82, 82, 82]`, speed `[2.310, 2.310, 2.310]` |
| Rule-based | 8V | 100% | 242.042 卤 110.586 [86.000, 329.125] steps | 1.189 卤 0.754 [0.655, 2.255] m/s | 8.000 卤 0.000 [8.000, 8.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[86, 311, 329.125]`, speed `[2.255, 0.655, 0.658]` |
| Raw LLM | 4V | 100% | 15.000 卤 0.000 [15.000, 15.000] steps | 6.803 卤 0.000 [6.803, 6.803] m/s | 4.000 卤 0.000 [4.000, 4.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.803, 6.803, 6.803]` |
| Raw LLM | 8V | 100% | 15.292 卤 2.045 [12.875, 17.875] steps | 6.599 卤 0.254 [6.265, 6.880] m/s | 8.000 卤 0.000 [8.000, 8.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[17.875, 12.875, 15.125]`, speed `[6.265, 6.880, 6.652]` |
| Hybrid | 4V | 100% | 15.000 卤 0.000 [15.000, 15.000] steps | 6.803 卤 0.000 [6.803, 6.803] m/s | 4.000 卤 0.000 [4.000, 4.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.803, 6.803, 6.803]` |
| Hybrid | 8V | 100% | 15.292 卤 2.045 [12.875, 17.875] steps | 6.599 卤 0.254 [6.265, 6.880] m/s | 8.000 卤 0.000 [8.000, 8.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[17.875, 12.875, 15.125]`, speed `[6.265, 6.880, 6.652]` |
| Hybrid + Safety | 4V | 100% | 15.000 卤 0.000 [15.000, 15.000] steps | 6.803 卤 0.000 [6.803, 6.803] m/s | 4.000 卤 0.000 [4.000, 4.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[15, 15, 15]`, speed `[6.803, 6.803, 6.803]` |
| Hybrid + Safety | 8V | 100% | 15.292 卤 2.045 [12.875, 17.875] steps | 6.599 卤 0.254 [6.265, 6.880] m/s | 8.000 卤 0.000 [8.000, 8.000] | 0 | completion `[1.0, 1.0, 1.0]`, waiting `[17.875, 12.875, 15.125]`, speed `[6.265, 6.880, 6.652]` |

### Interpretation

- The rule-based baseline degrades substantially from 4V to 8V.
- The LLM-assisted pipeline remains comparatively stable over the tested 4V-to-8V range.
- Completion rate saturates at 100% in every valid cell, so it does not separate controllers.
- Collision count remains 0 throughout the valid corrected evidence.

## 3. LLM/provider reliability

### Table 3. Provider/parser/fallback reliability

| Controller | Scale | Provider attempts | Provider successes | Success rate | Parser success given success | Fallback steps | Mean latency | Seed-level successes | Seed-level fallback counts |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| Raw LLM | 4V | 53.000 卤 0.000 [53.000, 53.000] | 3.333 卤 4.714 [0.000, 10.000] | 6.29% 卤 8.89% [0.00%, 18.87%] | 100% | 49.667 卤 4.714 [43.000, 53.000] | 101.412 卤 29.695 ms | `[10, 0, 0]` | `[43, 53, 53]` |
| Raw LLM | 8V | 106.333 卤 0.471 [106.000, 107.000] | 0.667 卤 0.471 [0.000, 1.000] | 0.63% 卤 0.44% [0.00%, 0.94%] | 100% | 105.667 卤 0.471 [105.000, 106.000] | 76.846 卤 1.552 ms | `[1, 1, 0]` | `[106, 105, 106]` |
| Hybrid | 4V | 53.000 卤 0.000 [53.000, 53.000] | 3.000 卤 4.243 [0.000, 9.000] | 5.66% 卤 8.00% [0.00%, 16.98%] | 100% | 50.000 卤 4.243 [44.000, 53.000] | 111.021 卤 23.614 ms | `[9, 0, 0]` | `[44, 53, 53]` |
| Hybrid | 8V | 106.333 卤 0.471 [106.000, 107.000] | 0.333 卤 0.471 [0.000, 1.000] | 0.31% 卤 0.44% [0.00%, 0.93%] | 100% | 106.000 卤 0.000 [106.000, 106.000] | 79.035 卤 4.074 ms | `[1, 0, 0]` | `[106, 106, 106]` |
| Hybrid + Safety | 4V | 53.000 卤 0.000 [53.000, 53.000] | 3.000 卤 4.243 [0.000, 9.000] | 5.66% 卤 8.00% [0.00%, 16.98%] | 100% | 50.000 卤 4.243 [44.000, 53.000] | 96.152 卤 22.919 ms | `[9, 0, 0]` | `[44, 53, 53]` |
| Hybrid + Safety | 8V | 106.333 卤 0.471 [106.000, 107.000] | 0.333 卤 0.471 [0.000, 1.000] | 0.31% 卤 0.44% [0.00%, 0.94%] | 100% | 106.000 卤 0.816 [105.000, 107.000] | 76.398 卤 1.312 ms | `[0, 0, 1]` | `[107, 106, 105]` |

### Interpretation

- Provider success is low in every live LLM-bearing cell.
- The 8V corrected evidence is especially weak on provider availability.
- Successful responses used `finish_reason = stop` and finite token usage (`prompt_tokens = 543`, `completion_tokens = 35-37`, `reasoning_tokens = 9-11`).
- Parser success given provider success is 100% in the corrected evidence.
- Because fallback dominates, traffic outcomes must be interpreted as pipeline-level behaviour rather than pure model behaviour.

## 4. Decision-flow behaviour

The trace schema preserves raw, validated, postprocessed, and final decisions separately.

### Table 4. Decision-source / postprocessor / safety behaviour

| Controller | Scale | Dominant decision pattern | Postprocessor intervention | Safety override | Practical note |
|---|---|---|---:|---:|---|
| Rule-based | 4V | deterministic interface rule | 0 | 0 | No live provider path is used. |
| Rule-based | 8V | deterministic interface rule | 0 | 0 | No live provider path is used. |
| Raw LLM | 4V | fallback-heavy live path | 0 | 0 | Live provider exists, but most attempts fail. |
| Raw LLM | 8V | fallback-heavy live path | 0 | 0 | Live provider reliability is weaker at 8V. |
| Hybrid | 4V | fallback-heavy live path | 0 | 0 | Cooperative logic is present, but not visibly exercised in the valid evidence. |
| Hybrid | 8V | fallback-heavy live path | 0 | 0 | No visible cooperative intervention in the corrected 8V evidence. |
| Hybrid + Safety | 4V | fallback-heavy live path | 0 | 0 | Safety verifier is operational but not triggered. |
| Hybrid + Safety | 8V | fallback-heavy live path | 0 | 0 | Safety verifier is operational but not triggered. |

## 5. Safety observations

- Collision count is 0 in every valid run.
- Safety override count is 0 in every valid run.
- The safety verifier exists and is logged, but it is not meaningfully exercised in the corrected formal evidence.

## 6. Corrected result boundary

- `formal_v2` valid 4V is usable evidence.
- `formal_v4` corrected 8V is usable evidence.
- `formal_v2` nominal 8V traces are historical execution-layer failure evidence and must not be used in the final dissertation results.

## 7. Final evidence provenance

- Final 4V source: `formal_v2` valid 4V runs
- Final 8V source: `formal_v4`
- Excluded from final tables: `formal_v2` nominal 8V, `formal_v3`

The identical 8V traffic results for Raw LLM, Hybrid, and Hybrid + Safety are consistent with fallback dominance, very low provider success, zero visible postprocessor intervention, and zero safety overrides. This is a pipeline-level explanation, not evidence that the three architectures are intrinsically equivalent.

# 6 Discussion

- valid 4V evidence from `formal_v2`
- corrected 8V evidence from `formal_v4`

## 1. RQ1: Rule-based vs LLM-assisted architecture

### Observed result

The LLM-assisted pipeline exhibits lower waiting time and higher mean speed than the rule-based baseline in the corrected evidence.

- 4V rule-based: waiting `82.0` steps, speed `2.3098 m/s`
- 4V LLM-assisted: waiting `15.0` steps, speed `6.8026 m/s`
- 8V rule-based: waiting `242.0417` steps, speed `1.1895 m/s`
- 8V LLM-assisted: waiting `15.2917` steps, speed `6.5991 m/s`

### Interpretation

The evidence supports a cautious statement that the LLM-assisted pipeline improves traffic efficiency in the tested SUMO scenarios.

The live provider path is fallback-heavy, so the observed traffic advantage belongs to the pipeline rather than to a model-only controller.

## 2. RQ2: Raw vs Hybrid

### Observed result

The corrected evidence does **not** show a clear traffic-performance advantage for hybrid over raw LLM.

The 4V and 8V valid cells are effectively similar on the traffic metrics, and the corrected evidence contains no visible postprocessor intervention.

### Interpretation

The cooperative stage is implemented, but the valid formal evidence does not show that it changes traffic outcomes in a measurable way. The correct reading is therefore:

> No clear traffic-performance advantage was observed for the hybrid architecture over the raw LLM architecture in the corrected formal evidence.

Provider reliability also does not show a stable hybrid advantage. The live-provider path remains weak and seed-sensitive.

## 3. RQ3: Safety layer behaviour

### Observed result

The corrected valid evidence shows:

- `0` collisions in every valid run,
- `0` safety overrides in every valid run,
- no visible safety-verifier intervention.

### Interpretation

The safety layer is present and traceable, but the evaluated scenarios did not sufficiently exercise it. Therefore the dissertation should not claim that safety improved safety.

## 4. RQ4: 4V to 8V scalability

### Observed result

The corrected evidence supports a dual-layer interpretation.

1. **Traffic-level behaviour**
   - Rule-based performance degrades substantially from 4V to 8V.
   - LLM-assisted traffic metrics remain comparatively stable over the evaluated 4V-to-8V range.

2. **Provider-level behaviour**
   - Live-provider reliability remains weak at both scales.
   - The corrected 8V evidence is especially fallback-heavy.

### Interpretation

## 5. Provider reliability as a validity threat

Provider reliability is the main interpretive limitation of the dissertation.

In the corrected evidence:

- provider success is low,
- `RateLimitError` dominates failures,
- fallback-heavy execution is the norm,
- successful provider calls are rare and seed-sensitive.

This means the dissertation's traffic results should be read as the behaviour of a structured pipeline under constrained provider availability, not as a clean test of model intelligence alone.

## 6. What the study actually shows

The corrected dissertation supports the following bounded claims:

- a structured, traceable LLM-assisted control pipeline can be implemented in SUMO,
- the pipeline can be compared against a rule-based baseline in a frozen experimental design,
- the pipeline shows lower waiting time and higher mean speed than the rule-based baseline in the tested scenarios,
- traffic-level performance remains comparatively stable from 4V to 8V,
- provider reliability and fallback behaviour are first-order validity threats,
- the safety layer exists but was not strongly exercised,
- the cooperative postprocessor was not visibly exercised in the valid formal evidence.

## 7. What the study does not show

The corrected evidence does **not** prove:

- pure LLM superiority,
- general scalability to denser or larger scenarios,
- real-world validity,
- safety superiority,
- a visible effect from cooperative postprocessing,
- sufficient provider reliability for deployment.

## 9. Revised RQ summary

- **RQ1:** supported cautiously, at the pipeline level.
- **RQ2:** no clear traffic-performance advantage for hybrid over raw LLM.
- **RQ3:** safety layer present but insufficiently exercised.
- **RQ4:** traffic robustness is visible from 4V to 8V, but provider reliability remains a major limitation.

The near-identical 8V traffic results for Raw LLM, Hybrid, and Hybrid + Safety are best explained by the evidence showing fallback dominance, very low provider success, zero visible postprocessor intervention, and zero safety overrides. That does **not** mean the three architectures are intrinsically equivalent; it means the distinctive LLM/postprocessing/safety stages were rarely exercised in the corrected formal evidence.

# 7 Limitations

## 1. Only 4V and 8V formal scenarios

The corrected formal evidence covers only two vehicle scales:

- 4 vehicles
- 8 vehicles

Any claim about 16V or higher-scale traffic is unsupported by the current evidence.

## 2. Only three seeds per controller-scale cell

Each controller-scale cell has only `n = 3` seeds.

That is sufficient for descriptive comparison, but not for strong inferential claims. The dissertation should therefore report means, standard deviations, and seed-level values rather than claim statistical significance unless separate evidence is added.

## 3. Low-density, single-intersection SUMO scope

The simulation design uses a single unsignalised intersection under low-density traffic assumptions.

This is useful for controlled comparison, but it limits generalisation to:

- denser traffic
- multiple intersections
- heterogeneous road layouts
- more realistic traffic interactions

## 4. External provider dependency

The live LLM path depends on an external Groq provider.

Provider failures are frequent and mostly rate-limit related. This is a major validity threat because the traffic result is not produced by an always-available model; it is produced by a pipeline that frequently falls back.

## 5. Fallback-heavy execution

Because provider success is low, most live requests fall back to deterministic handling. The dissertation must not describe the final traffic result as pure LLM performance.

The correct interpretation is pipeline-level behaviour under constrained live-provider availability.

## 6. Live LLM contribution cannot be cleanly isolated

The corrected evidence does not cleanly separate:

- raw model quality
- prompt effect
- parser effect
- fallback effect
- cooperative postprocessing
- safety layer behaviour

The trace is rich enough to show the pipeline structure, but not rich enough to isolate each component's causal contribution without extra ablation work.

## 7. Safety verifier insufficiently exercised

The formal evidence shows zero collisions and zero safety overrides, but also no meaningful activation of the safety verifier.

That means safety behaviour was operationally present but empirically under-exercised.

## 8. No real-world or hardware-in-the-loop validation

All evidence is simulation-based.

There is no physical robot, hardware-in-the-loop, or live-road validation. The dissertation therefore supports simulation-level claims only.

## 9. Historical formal_v2 8V execution defect

A historical execution-layer defect was discovered during post-experiment trace auditing:

- the nominal 8-vehicle `formal_v2` runs loaded the four-vehicle default SUMO configuration
- the raw traces therefore showed only 4 observed / departed / arrived vehicles
- those traces were excluded from the final dissertation analysis
- the corrected 8V evidence is taken from `formal_v4`

This should be presented as a scientific traceability correction, not hidden.

## 10. Limited postprocessor evidence

The valid corrected formal evidence does not show any visible postprocessor intervention.

That means the cooperative layer cannot be claimed to have improved traffic performance in the final evidence set.

## 11. Completion-rate saturation

Completion rate is `100%` across all valid runs, so it does not differentiate controllers. Waiting time, mean speed, and provider reliability are more informative.

## 12. Summary statement

The corrected dissertation is still defensible, but it must remain bounded by the tested scenarios and by the provider reliability threat. The results support a traceable pipeline-level comparison, not a universal control claim.

## 13. Operational waiting metric definition

The dissertation's waiting metric is an operational stop-like occupancy proxy derived from the recorded `speed_after_action < 0.1 m/s` condition. It is not a queueing-theory delay measure and should not be interpreted as a direct physical waiting-time estimate.

# 8 Conclusion and Future Work

## 1. What was built?

The dissertation built a structured LLM-assisted decision pipeline for unsignalised intersection control in SUMO. The architecture separates:

- raw LLM proposal
- validation
- deterministic interface handling
- cooperative postprocessing
- safety verification
- trace logging
- seeded formal experiment execution

The implementation was designed to keep raw, validated, postprocessed, and final decisions traceable in the logs.

## 2. What was evaluated?

The corrected evidence base combines:

- valid 4V evidence from `formal_v2`
- corrected 8V evidence from `formal_v4`

Across the corrected evidence, the dissertation evaluates:

- rule-based control
- raw LLM control
- hybrid control
- hybrid + safety control
- 4V and 8V scales
- three seeds per controller-scale cell

## 3. What was observed?

The corrected evidence supports four main observations:

1. The LLM-assisted pipeline shows lower waiting time and higher mean speed than the rule-based baseline in the tested scenarios.
2. Rule-based performance degrades substantially from 4V to 8V.
3. The LLM-assisted traffic-level metrics remain comparatively stable across the tested 4V-to-8V range.
4. Provider reliability remains weak, fallback-heavy, and rate-limit constrained.

## 4. What cannot be concluded?

The dissertation does **not** prove:

- pure LLM superiority
- general scalability to dense traffic
- real-world road validity
- safety superiority
- that the cooperative postprocessor materially changes traffic performance in the valid evidence
- that the provider path is sufficiently reliable for deployment

## 5. RQ summary

### RQ1
The LLM-assisted pipeline exhibited lower waiting time and higher mean speed than the rule-based baseline in the tested SUMO scenarios.

### RQ2
No clear traffic-performance advantage was observed for the hybrid architecture over the raw LLM architecture in the corrected evidence.

### RQ3
The safety layer was implemented and operationally present, but the formal evidence did not sufficiently exercise it.

### RQ4
Traffic-level robustness is visible from 4V to 8V, but provider-level reliability remains a major limitation.

## 6. Main contribution

The dissertation's main contribution is a reproducible and traceable comparison of controller architectures for unsignalised intersection control, together with an explicit analysis of how live-provider availability and fallback behaviour shape the final system behaviour.

That is a stronger and more defensible contribution than a claim of universal LLM superiority.

## 7. Future work

Future work should focus on evidence gaps that are genuinely supported by the current limitations:

- higher-density traffic
- 16V or larger-scale experiments
- additional intersection topologies
- more seeds
- local or self-hosted LLM comparison
- controlled fallback ablation
- scenarios that deliberately trigger the safety verifier
- real-time or hardware-in-the-loop validation
- stronger provider-reliability engineering

## 8. Final conclusion

The corrected evidence shows that a frozen, traceable LLM-assisted decision pipeline can be implemented and evaluated systematically in SUMO. It can outperform a rule-based baseline on the tested traffic metrics, and the corrected 8V evidence confirms that the observed traffic behaviour persists in the larger of the two tested scales.

At the same time, live-provider reliability remains a first-order validity threat, so the final dissertation claim must stay at the level of pipeline behaviour rather than pure LLM intelligence.

The intermediate `formal_v3` batch is excluded from the final dissertation evidence because two rule-based 8V runs did not complete all arrivals within the fixed termination window.

# References

1. **Dresner, K. and Stone, P. (2008).** *A Multiagent Approach to Autonomous Intersection Management.* Journal of Artificial Intelligence Research, 31, 591-656.

2. **Safarov, K. (2022).** *The impact of autonomous vehicles on traffic performance at an unregulated junction.* PhD thesis, University of Bristol.

3. **Huang, W., Abbeel, P., Pathak, D., and Mordatch, I. (2022).** *Language Models as Zero-Shot Planners: Extracting Actionable Knowledge for Embodied Agents.* arXiv preprint `arXiv:2201.07207v2`.

4. **Driess, D., Xia, F., Sajjadi, M. S. M., Lynch, C., Chowdhery, A., Ichter, B., Wahid, A., Tompson, J., Vuong, Q., Yu, T., Huang, W., Chebotar, Y., Sermanet, P., Duckworth, D., Levine, S., Vanhoucke, V., Hausman, K., Toussaint, M., Greff, K., Zeng, A., Mordatch, I., and Florence, P. (2023).** *PaLM-E: An Embodied Multimodal Language Model.* arXiv preprint `arXiv:2303.03378v1`.

5. **Cui, C., Ma, Y., Yang, Z., Zhou, Y., Liu, P., Lu, J., Li, L., Chen, Y., Panchal, J. H., Abdelraouf, A., Gupta, R., Han, K., and Wang, Z. (2025).** *Large Language Models for Autonomous Driving (LLM4AD): Concept, Benchmark, Experiments, and Challenges.* arXiv preprint `arXiv:2410.15281v3`.

6. **Hou, X., Wang, W., Yang, L., Lin, H., Feng, J., Min, H., and Zhao, X. (2025).** *DriveAgent: Multi-Agent Structured Reasoning with LLM and Multimodal Sensor Fusion for Autonomous Driving.* arXiv preprint `arXiv:2505.02123v1`.

7. **Dong, X., Li, J., Xie, J., Yi, Y., Jia, T., Fang, S., Tian, Y., and Hang, P. (2026).** *Large Language Model based Interactive Decision-Making for Autonomous Driving.* arXiv preprint `arXiv:2604.23513v1`.
