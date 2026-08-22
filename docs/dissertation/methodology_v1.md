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
