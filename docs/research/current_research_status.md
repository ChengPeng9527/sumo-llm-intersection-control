# Current Research Status

## Dissertation Goal

Evaluate whether an LLM-assisted hybrid decision framework can improve cooperative decision making at an unsignalized intersection while preserving deterministic safety.

## Current Method

The current method is a separated decision pipeline:

1. prompt builder
2. live or mock provider
3. response parser
4. validation
5. cooperative post-processing
6. deterministic safety verification
7. logging and trace output

## Completed Work

- Phase 18 decision pipeline separation is implemented.
- Raw, hybrid, and hybrid+safety controller paths exist.
- Structured prompt building is implemented.
- Response parsing is implemented.
- Cooperative post-processing is implemented.
- Safety verification is implemented.
- Unified logging and trace fields are implemented.
- Pipeline unit tests pass.
- Mock SUMO smoke validation passed.
- One live Groq revalidation request passed through the current pipeline.

## Engineering Validation

The repository currently has:

- `pytest`: 30 passed
- SUMO smoke: passed
- live revalidation: passed

This is engineering validation, not yet a full dissertation-scale experimental evaluation.

## Current Evidence

Current phase 18 evidence:

- smoke summary under `results/phase18_smoke/phase18_sumo_smoke/`
- live revalidation under `results/phase18_live_revalidation/`
- phase 18 report and metadata under `docs/phases/phase_18/`
- pilot runner and preflight report under `scripts/run_dissertation_pilot.py` and `docs/research/pilot_experiment_report.md`

Historical evidence:

- phase 17 live LLM results
- historical 4V, 8V, and 16V run directories under `results/raw/`

## Formal Experiment Status

Formal experiments are not yet complete.

The repository has the machinery to run them, but the current state is still a mixture of:

- engineering evidence,
- smoke evidence,
- historical experiment evidence,
- one current live revalidation.

## Primary Research Risks

1. Overstating engineering validation as formal evaluation.
2. Mixing historical live LLM evidence with the current Phase 18 revalidation.
3. Using incomplete historical result directories as if they were dissertation-grade evidence.
4. Expanding the experiment matrix faster than the evidence can support.
5. Treating safety and cooperation as performance improvements without reporting their trade-offs.

## Current Blockers

- Formal experiment sweep is still pending.
- Some historical result directories have metadata inconsistencies and should not be used directly as final evidence.
- The current live revalidation is a single-request engineering check rather than a statistical experiment.
- The live pilot is blocked in this PowerShell session because `GROQ_API_KEY` is missing.

## Next Unique Task

Provide a safe live Groq credential, then run the fixed pilot before any formal dissertation sweep.

## Status Statement

Research design is substantially complete; engineering validation is complete; the pilot runner is prepared; the live pilot is currently blocked by missing credentials; formal experimental evaluation is not yet complete.
