# LLM Request Configuration Specification

## 1. Provider

Groq

## 2. Model

`openai/gpt-oss-20b`

## 3. Client/API Path

Current live LLM requests use the existing project path:

`raw_llm_controller.py` / `hybrid_llm_controller.py` / `hybrid_llm_safety_controller.py`
鈫?`src/controllers/decision_pipeline.py`
鈫?`client.chat.completions.create(...)`

The same shared request helper is also used by:

- `scripts/run_llm_parser_diagnostic.py`

## 4. Frozen Request Parameters

Frozen client parameters:

- `base_url = https://api.groq.com/openai/v1`
- `timeout = 30.0`
- `max_retries = 0`

Frozen completion parameters:

- `max_completion_tokens = 256`
- `reasoning_effort = low`

## 5. Why Each Parameter Is Frozen

- `base_url`: fixes the provider endpoint for the canonical Groq path.
- `timeout`: keeps technical network behavior reproducible across controllers.
- `max_retries`: avoids hidden retry behavior that could change latency and failure counts.
- `max_completion_tokens`: prevents truncation of the final decision output.
- `reasoning_effort`: matches the verified local successful request and keeps reasoning depth explicit.

## 6. Parameters Intentionally Left at Provider Defaults

The following are not explicitly set in the current canonical request helper:

- `temperature`
- `top_p`
- `seed`
- `reasoning_format`

Rationale:

- they are not required to produce the frozen JSON decision contract
- they would add extra tuning confound without evidence of benefit in this dissertation method
- they are not part of the currently verified minimal successful request

## 7. Reproducibility Implications

This freeze removes hidden client-default ambiguity from the live request path.

It makes the three LLM-bearing controllers share the same request-level settings and reduces version-sensitive behavior from the OpenAI client.

## 8. Cost / Latency Implications

- `max_completion_tokens = 256` keeps the request budget small.
- `reasoning_effort = low` is the lowest-cost reasoning setting that was verified to return a valid decision in local PowerShell testing.
- `timeout = 30.0` and `max_retries = 0` reduce hidden retry overhead and keep network behavior explicit.

## 9. Method Impact

This is an experiment-configuration freeze only.

It does not change:

- prompt content
- decision space
- parser semantics
- controller logic
- postprocessing
- safety logic
- SUMO scenario

## 10. Freeze Statement

All LLM-bearing formal experiment runs must use this request configuration unchanged:

- Raw LLM
- Hybrid
- Hybrid + Safety

If any material request parameter changes after formal experiment starts, the affected LLM-bearing runs must be rerun.


