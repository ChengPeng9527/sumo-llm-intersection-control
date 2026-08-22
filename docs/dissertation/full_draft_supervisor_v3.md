# Dissertation Supervisor Draft v3

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

This draft is the corrected supervisor-facing version of the dissertation. It uses only the final evidence boundary:

- valid 4V evidence from `results/formal_experiment/dissertation_formal_v2/`
- corrected 8V evidence from `results/formal_experiment/dissertation_formal_v4/`
- corrected literature audit from the local reference archive

It does not use the invalid nominal 8V `formal_v2` traces and does not use `formal_v3` as final evidence.

## 1. Introduction

Unsignalised intersection coordination remains a difficult control problem because multiple vehicles may approach the same conflict space with competing priorities, partially overlapping routes, and limited room for conservative control. In simulation-based autonomous intersection management, a controller must balance traffic efficiency, safety, and traceability without turning the system into an opaque black box (Dresner and Stone, 2008; Safarov, 2022).

This dissertation investigates whether a structured LLM-assisted decision pipeline can support cooperative decision-making at an unsignalised intersection while preserving deterministic fallback behaviour, cooperative post-processing, and safety verification.

The motivation is practical as well as methodological. In many LLM-based control demonstrations, the model is treated as if it were the whole controller. That makes it difficult to separate the model's contribution from validation logic, rule-based fallback, cooperative heuristics, and safety checks. The present project addresses that issue by making the decision pipeline explicit and auditable.

## 2. Literature Review / Background

[SEE `docs/dissertation/literature_review_v2_final.md`]

## 3. Methodology / System Design

The implemented system is a staged pipeline rather than a single black-box LLM controller. The frozen architecture separates:

1. structured prompt construction,
2. live-provider request handling,
3. response parsing,
4. validation of the parsed action,
5. cooperative post-processing,
6. deterministic safety verification,
7. trace logging of raw, intermediate, and final decisions.

The repository supports four controller variants:

- `rule_based`
- `raw_llm`
- `hybrid`
- `hybrid_safety`

These controllers share the same frozen scenario family and the same canonical decision space:

- `PROCEED`
- `WAIT`
- `FREE`

The canonical prompt is `P1_BASELINE`, and the frozen live LLM configuration is:

- provider: Groq
- base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- max completion tokens: `256`
- reasoning effort: `low`
- timeout: `30.0`
- max retries: `0`

The logging schema retains raw, validated, postprocessed, and final decisions separately, together with provider metadata such as finish reason, token usage, parser success, fallback status, and latency. This makes it possible to interpret the experiment at the pipeline level rather than as pure model output.

## 4. Experimental Design

The formal experiment uses a frozen matrix of:

- 4 controllers
- 2 vehicle scales: 4V and 8V
- 3 seeds

This yields 24 planned runs.

The corrected dissertation evidence base is:

- valid 4V evidence from `formal_v2`
- corrected 8V evidence from `formal_v4`

The invalid nominal 8V `formal_v2` traces are excluded because trace auditing showed that the four-vehicle default SUMO configuration was loaded instead of the generated 8V scenario configuration. The intermediate `formal_v3` batch is also excluded because two rule-based 8V runs did not complete all arrivals within the fixed termination window.

The formal experiment evaluates the following outcome families:

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

## 5. Results

### 5.1 Experimental validity

- Valid 4V evidence: 12 runs, 4 observed / departed / arrived vehicles per run, 0 collisions.
- Corrected 8V evidence: 12 runs, 8 observed / departed / arrived vehicles per run, 0 collisions.
- Corrected dissertation evidence base: 24 valid runs total.

### 5.2 Core traffic findings

- Rule-based 4V: waiting `82.0` steps, speed `2.3098 m/s`
- LLM-assisted 4V: waiting `15.0` steps, speed `6.8026 m/s`
- Rule-based 8V: waiting `242.0417` steps, speed `1.1895 m/s`
- LLM-assisted 8V: waiting `15.2917` steps, speed `6.5991 m/s`

The corrected evidence supports a cautious descriptive claim that the LLM-assisted pipeline exhibited lower waiting time and higher mean speed than the rule-based baseline in the tested SUMO scenarios.

### 5.3 Provider reliability

Provider reliability remains the main validity threat. In the corrected evidence, provider success is low and fallback-heavy, especially in the 8V cells. Successful responses used `finish_reason = stop` and finite token usage, but the overall success rate remains very small relative to total attempts.

The dissertation therefore must interpret the traffic result as pipeline-level behaviour rather than pure model performance.

### 5.4 Decision-flow behaviour

The valid corrected evidence contains no visible cooperative postprocessor intervention and no safety override. The trace schema nevertheless preserves these stages, which is important for interpretability and for future ablation work.

## 6. Discussion

The corrected evidence supports a cautious claim that the LLM-assisted pipeline can improve traffic efficiency relative to the rule-based baseline in the tested SUMO scenarios. However, the result must be interpreted as pipeline-level behaviour because the live provider is fallback-heavy.

The corrected evidence does not show a clear traffic-performance advantage for hybrid over raw LLM, and it does not show any visible safety improvement from the safety layer. The most important limitation is provider reliability.

The safety layer is present and traceable, but the evaluated scenarios did not sufficiently exercise it. The cooperative stage is implemented, but the valid formal evidence does not show that it changes traffic outcomes in a measurable way.

The most defensible scaling statement is limited to the tested range: within the evaluated low-density 4V and 8V SUMO scenarios, the LLM-assisted pipeline remained operational and showed comparatively stable traffic-level performance, while provider reliability remained a first-order limitation.

## 7. Limitations

The dissertation remains limited by:

- only 4V and 8V formal scenarios,
- three seeds per controller-scale cell,
- low-density, single-intersection SUMO scope,
- external provider dependency,
- fallback-heavy execution,
- insufficient safety-layer exercise,
- no real-world or hardware-in-the-loop validation,
- no evidence for 16V or larger-scale generalisation.

The corrected evidence does not cleanly separate raw model quality, prompt effect, parser effect, fallback effect, cooperative post-processing, and safety-layer behaviour. The trace is rich enough to show the pipeline structure, but not rich enough to isolate each component's causal contribution without extra ablation work.

## 8. Conclusion and Future Work

The dissertation shows that a frozen, traceable LLM-assisted decision pipeline can be implemented and evaluated systematically in SUMO. It can outperform a rule-based baseline on the tested traffic metrics, and the corrected 8V evidence confirms that the observed traffic behaviour persists in the larger of the two tested scales.

At the same time, live-provider reliability remains a first-order validity threat, so the final dissertation claim must stay at the level of pipeline behaviour rather than pure LLM intelligence.

Future work should focus on evidence gaps that are genuinely supported by the current limitations:

- higher-density traffic,
- 16V or larger-scale experiments,
- additional intersection topologies,
- more seeds,
- local or self-hosted LLM comparison,
- controlled fallback ablation,
- scenarios that deliberately trigger the safety verifier,
- real-time or hardware-in-the-loop validation,
- stronger provider-reliability engineering.

## 9. References

[SEE `docs/dissertation/references_v2_final.md`]
