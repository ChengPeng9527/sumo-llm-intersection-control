# Successful LLM Effect Audit

## Scope
This audit examines whether successful provider calls in the formal evidence produce a visible traffic effect beyond the deterministic fallback path.

## Evidence Sources
- `results/formal_experiment/dissertation_formal_v2`
- `results/formal_experiment/dissertation_formal_v4`
- Valid evidence scope:
  - formal_v2 4V runs only
  - formal_v4 corrected 8V runs only

## Repository Evidence

### Request and execution pipeline
- File: `src/llm/request_config.py`
  - provider: Groq
  - model: `openai/gpt-oss-20b`
  - max tokens: 256
  - reasoning effort: low
  - timeout: 30 seconds
  - max retries: 0
- File: `src/controllers/decision_pipeline.py`
  - if the real provider call fails, the pipeline falls back to `mock_llm_decision(...)`
  - if the pipeline is not in real-provider mode, it also uses the same fallback policy

### Valid formal evidence summary
- Total rows scanned across valid formal evidence: 11,917
- Controller row counts:
  - BaselineRule: 7,801
  - RawLLMController: 1,372
  - HybridLLMController: 1,372
  - HybridLLMSafetyController: 1,372
- Successful provider rows:
  - `provider_request_success == true`: 74 rows
  - those rows had `fallback_used == false`, `postprocess_applied == false`, and `safety_override == false`

### Successful provider events
- Unique successful provider events: 32
- Controller breakdown:
  - RawLLMController: 12
  - HybridLLMController: 10
  - HybridLLMSafetyController: 10
- File / trace concentration:
  - most successful events occurred in formal_v2 4V data
  - only a small remainder occurred in formal_v4 8V data

## Observed Behaviour
The successful provider events do not show a robust, separable traffic effect that is distinct from the fallback policy:
- the successful events are sparse
- they are heavily concentrated in one seed
- they do not provide enough repeated evidence to support a stable provider-specific traffic advantage

The safe interpretation is that the formal evidence does not justify claiming provider success as the main source of the dissertation's traffic improvement.

## Confidence
Moderate to high. The trace evidence is strong enough to reject an "LLM-alone superiority" claim, but not strong enough to quantify a precise provider-specific uplift.
