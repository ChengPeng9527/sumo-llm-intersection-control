# Research Design v1

## Working Title

Design and Evaluation of a Safety-Constrained LLM-Based Cooperative Decision Framework for Autonomous Intersection Management.

## Research Context

This project studies an unsignalized four-way intersection in SUMO. The codebase now separates the decision stack into:

1. Raw LLM decision generation
2. Cooperative post-processing
3. Deterministic safety verification

The current implementation supports baseline, cooperative, raw LLM, hybrid, and hybrid-plus-safety controllers, with both mock and real LLM modes.

## Problem Statement

The main practical problem is not whether an LLM can emit a JSON action, but whether a traceable decision pipeline can combine:

- structured vehicle state,
- cooperative reasoning,
- deterministic safety enforcement, and
- reproducible logging

without losing control over safety or making the final behavior opaque.

## Research Gap

The repository currently contains engineering evidence that the pipeline runs end to end, but formal experimental evidence for the dissertation question is still incomplete. The present gap is the lack of a full, controlled, multi-seed evaluation that compares:

- rule-based control,
- raw LLM control,
- hybrid LLM plus cooperative post-processing,
- hybrid LLM plus safety verification

under a consistent experimental protocol.

## Main Research Question

Can an LLM-assisted hybrid decision framework improve cooperative decision making at unsignalized intersections while maintaining deterministic safety?

## Sub-Research Questions

RQ1. Can an LLM generate usable high-level cooperative decisions for vehicles at an unsignalized intersection?

RQ2. Does cooperative post-processing improve the robustness and efficiency of raw LLM decisions?

RQ3. Does deterministic safety verification provide additional safety benefits, and what efficiency trade-offs does it introduce?

RQ4. How does the proposed framework behave as traffic complexity or vehicle scale increases?

RQ5. How much influence does the LLM retain over the final decisions after validation, cooperative post-processing, and safety verification?

## Research Hypotheses

H1. Raw LLM decisions will be usable, but not consistently robust enough to serve as the final control layer without validation.

H2. Cooperative post-processing will reduce unnecessary waiting and improve agreement with compatible traffic flows.

H3. Deterministic safety verification will reduce unsafe final actions, but may introduce conservative overrides.

H4. As vehicle count increases, the gap between raw LLM behavior and the hybrid pipeline will become more visible in efficiency and intervention metrics.

H5. The final decision source will shift away from raw LLM output in a measurable subset of cases because validation, cooperation, and safety each can alter the action.

## Research Objectives

1. Define a reproducible decision pipeline with traceable stages.
2. Preserve the distinction between raw, validated, postprocessed, and final decisions.
3. Establish a clear evaluation protocol with explicit baselines and metrics.
4. Use evidence from both engineering validation and formal experiments.
5. Support dissertation writing with auditable artifacts rather than narrative-only claims.

## Proposed Method

The implemented method is:

1. Build a structured prompt from the current vehicle state and route conflict matrix.
2. Send the prompt to a live or mock provider.
3. Parse the raw provider response into per-vehicle actions.
4. Normalize invalid or missing actions to WAIT.
5. Apply a deterministic interface rule so that vehicles outside the control zone become FREE.
6. Apply cooperative post-processing so compatible vehicles may be promoted from WAIT to PROCEED.
7. Apply deterministic safety verification so conflicting actions can be downgraded.
8. Log all intermediate and final decisions separately.

## Baselines

The repo already supports these comparison points:

- Baseline rule controller
- Cooperative rule controller
- Raw LLM controller
- Hybrid LLM controller
- Hybrid LLM plus safety controller

## Expected Contributions

The current work can support the following dissertation claims, provided the final experimental evidence supports them:

- a reproducible decision pipeline with separated stages,
- a traceable comparison between raw LLM, cooperative logic, and safety verification,
- a formal evaluation specification for SUMO-based intersection control,
- engineering evidence that the live provider path, parser, postprocessor, and safety trace all work together.

This document does not claim novelty by itself.

## Scope

- SUMO-based unsignalized four-way intersection.
- Vehicle counts already represented in the repository: 4, 8, and 16.
- Controllers already represented in the repository: baseline, cooperative, raw LLM, hybrid, and hybrid plus safety.
- Provider modes already represented in the repository: mock and real.

## Exclusions

The current design does not include:

- signalized intersections,
- multi-intersection networks,
- lane-changing research beyond the current controller scope,
- new prompt redesign,
- new safety rule design,
- new cooperative rule design,
- large-scale uncontrolled traffic expansion,
- unsupported novelty claims.

## Research Workflow

1. Generate scenario.
2. Run controller.
3. Record raw, validated, postprocessed, and final decisions.
4. Aggregate metrics.
5. Compare controller modes.
6. Separate engineering validation from formal experiment evidence.

## Current Progress

Implemented and validated in code:

- raw / hybrid / hybrid+safety pipeline separation,
- structured prompt builder,
- response parser,
- cooperative postprocessor,
- deterministic safety verifier,
- unified logging schema,
- pytest coverage for pipeline behavior,
- SUMO smoke validation,
- one live Groq revalidation request with the current pipeline.

## Remaining Work

1. Run the formal experimental matrix under a controlled protocol.
2. Aggregate results into dissertation-ready tables and figures.
3. Separate historical evidence from current Phase 18 evidence in the final write-up.
4. Decide, with supervision, whether any additional baselines are needed.
5. Write the Results and Discussion sections using only evidence-backed claims.

## Research-Design Freeze Statement

This research design is frozen with respect to:

- research questions,
- hypotheses,
- controller definitions,
- prompt structure,
- model choice,
- cooperative rules,
- safety rules,
- primary metrics,
- experiment matrix,
- statistical plan.

Only confirmed bugs, logging defects, execution defects, or evidence-generation errors should change the frozen design, and any such change must be recorded together with its behavioral impact and rerun requirement.
