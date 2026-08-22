# Dissertation Outline v1

## Working Title

Design and Evaluation of a Safety-Constrained LLM-Based Cooperative Decision Framework for Autonomous Intersection Management.

## Recommended Structure

### 1. Introduction

- Problem context: unsignalized intersection control in SUMO.
- Motivation: traceable, safety-constrained use of an LLM in a multi-stage decision pipeline.
- Research questions and dissertation scope.
- Contribution summary.

### 2. Background and Related Work

- Autonomous intersection management.
- Rule-based traffic control.
- LLM-assisted decision support.
- Safety verification and cooperative decision layers.
- Traceability and reproducibility in experimental robotics systems.

### 3. Methodology

- System architecture.
- Canonical prompt and decision space.
- Provider, request configuration, and parser contract.
- Validation, cooperative post-processing, and safety verification.
- Logging and traceability design.

### 4. Experimental Design

- Formal experiment matrix.
- Vehicle counts, seeds, controllers, and scenario setup.
- Metrics and analysis plan.
- Provenance, freeze commit, and artifact layout.
- Validity threats built into the design.

### 5. Results

- Controller-level performance comparison.
- Provider reliability and parser success.
- Decision-flow evidence.
- Scalability analysis.

### 6. Discussion

- What the results actually support.
- Where the system is robust.
- Where fallback-dominance limits interpretation.
- Why safety did or did not materially change the measured outcomes.

### 7. Limitations and Threats to Validity

- Provider reliability instability.
- Sequential execution and order effects.
- Completion-rate ceiling effects.
- Scope limits of 4V and 8V formal v2.
- What cannot be claimed from the data.

### 8. Conclusion and Future Work

- Main evidence-backed conclusion.
- Recommended next technical and experimental steps.
- Potential extensions that are explicitly outside the frozen method.

## Why This Structure Fits the Current Evidence

The repository now contains a frozen method, a complete formal v2 dataset, and a large amount of traceable engineering evidence. That makes a conventional thesis structure suitable, but the chapter order should reflect evidence readiness:

1. method and experiment design are ready first,
2. results can be written directly from formal v2 evidence,
3. discussion and limitations should explicitly address provider reliability and fallback-heavy traces.

That is why the first draft should prioritize Methodology, Experimental Design, and Results before polishing the Introduction.
