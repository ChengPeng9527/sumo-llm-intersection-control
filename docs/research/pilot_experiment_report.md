# Pilot Experiment Report

## Pilot Objective

Validate the full four-controller experiment chain before formal dissertation evaluation.

This pilot is not intended to produce dissertation conclusions. It is a readiness check for:

- one fixed scenario
- one fixed seed
- four controllers
- one controlled execution path
- one consistent logging schema
- one live Groq provider path for the LLM-bearing controllers

## Frozen Configuration

The pilot configuration is frozen as follows:

- scenario density: low
- vehicle count: 4
- seed: 1
- route set: the existing four route ids
- SUMO version: the repository's configured SUMO installation
- Python: the repository's configured Python 3.10 interpreter
- LLM provider: Groq
- provider base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- decision interval: 1

## Controller Definitions

The pilot uses four controllers:

1. Rule-based
2. Raw LLM
3. Hybrid
4. Hybrid + Safety

The first controller is deterministic and should not send live LLM requests.
The other three controllers are expected to use the same live Groq provider settings.

## Scenario Definition

The pilot scenario is a single low-density, four-vehicle scenario generated from the existing scenario generator.

The key requirements are:

- same routes
- same seed
- same vehicle count
- same termination condition
- same SUMO network
- same controller interface

## Execution Environment

Repository evidence shows:

- `pytest` passes with 30 tests
- SUMO smoke validation passed
- live Groq revalidation passed
- the decision pipeline is frozen and traceable

Current preflight environment check:

- `GROQ_API_KEY`: missing in the current PowerShell session

Because the pilot uses a live Groq path for three controllers, the live pilot cannot start from the current session.

## Data Outputs

The designated output root is:

`results/pilot/dissertation_pilot_v1/`

Expected pilot outputs if the live pilot is allowed to run:

- `pilot_config.json`
- `pilot_summary.csv`
- `pilot_summary.json`
- `decision_flow_summary.csv`
- `request_cost_summary.json`
- `runtime_summary.json`
- `pilot_verification.json`
- controller subdirectories for:
  - `rule_based`
  - `raw_llm`
  - `hybrid`
  - `hybrid_safety`

## Schema Consistency

The pilot is designed to keep the same unified schema already used in the repository:

- raw decision
- validated decision
- postprocessed decision
- final decision
- decision source
- safety override
- parser success
- fallback usage
- latency

This is already supported by the current logging schema and unit tests.

## Metric Readiness

The pilot can collect the following ready metrics:

- completion rate
- throughput
- mean waiting time
- mean speed
- episode duration
- collision count
- parser success count
- fallback count
- latency
- safety override count
- decision distribution
- postprocessor intervention count
- decision agreement
- decision flow

## LLM Request Cost

If the pilot were allowed to run with the current fixed configuration:

- baseline requests: 0
- raw LLM requests: one per simulation step
- hybrid requests: one per simulation step
- hybrid + safety requests: one per simulation step

Because the pilot uses the low-density 4-vehicle scenario and the current scenario generator sets the duration to 240 seconds for low density, the expected request count is approximately:

- raw LLM: 240 requests
- hybrid: 240 requests
- hybrid + safety: 240 requests
- total live requests: 720

This is an estimate from repository configuration, not a measured pilot result.

## Runtime

Exact pilot runtime is not available because the live pilot was not started.

The repository does provide one live revalidation latency point and a working pipeline, but that is not enough to claim an exact pilot runtime.

## Failures and Anomalies

Current preflight failure:

- `PILOT_BLOCKED_NO_SAFE_CREDENTIAL`

Reason:

- `GROQ_API_KEY` is missing in the current PowerShell session, so the live pilot cannot safely start.

No algorithmic failure has been observed from the pilot code itself at this stage.

## SUMO Control Limitations

The pilot does not replace SUMO dynamics.

SUMO still controls:

- vehicle motion
- lane geometry
- car-following
- native collision avoidance
- native right-of-way behavior

The project controller only controls the high-level action command and trace logging.

## Remaining Minor Fixes

No controller redesign is required.

The only remaining operational requirement before a live pilot is:

- provide a safe live Groq credential in the current session

## Formal Experiment Readiness

This pilot was intended to validate the execution chain, not to produce dissertation conclusions.

Because the live pilot cannot yet start from the current session, the formal experiment phase should still be treated as pending pilot completion.

## Final Verdict

**PILOT_BLOCKED_NO_SAFE_CREDENTIAL**

The repository is structurally ready for the pilot runner, but the current session does not expose `GROQ_API_KEY`, so the live pilot must wait until a safe credential is available.
