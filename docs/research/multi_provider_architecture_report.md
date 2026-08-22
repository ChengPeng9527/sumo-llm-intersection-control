# Multi-Provider Architecture Report

## Summary

The live LLM layer has been refactored into a multi-provider adapter architecture with provenance-aware diagnostics, while preserving the existing Groq compatibility path for the default research-fixed configuration.

Implemented components:

- `LLMProvider`-style request interface via `MultiProviderClient.request(messages, request_config, request_context)`
- `ProviderResponse` with requested/actual provider provenance fields
- Groq adapter built on the existing Groq-compatible client
- OpenRouter adapter using the OpenAI-compatible `/chat/completions` endpoint
- Gemini adapter using the official Gemini REST API, with optional SDK support when available
- Optional Cerebras adapter using an OpenAI-compatible endpoint template
- Independent limiter state per provider
- Provenance fields recorded in diagnostics and CSV schema

## Provider Matrix

| Provider | Model | API compatibility | Free / trial status | Sanity success | Latency | Parser success |
| --- | --- | --- | --- | --- | --- | --- |
| Groq | `openai/gpt-oss-20b` | OpenAI-compatible Groq API | Paid / key-based; configured in this workspace | FAIL | 92 ms | FAIL |
| Gemini | `gemini-2.5-flash` | Official Gemini API / SDK | Not configured in this workspace | SKIPPED | N/A | N/A |
| OpenRouter | `openai/gpt-oss-20b` | OpenAI-compatible OpenRouter endpoint | Not configured in this workspace | SKIPPED | N/A | N/A |
| Cerebras | `llama-4-scout-17b-16e-instruct` | Optional OpenAI-compatible endpoint template | Not configured in this workspace | SKIPPED | N/A | N/A |

## Live Sanity Check

Configured keys in the current environment:

- `GROQ_API_KEY`: present
- `GEMINI_API_KEY`: absent
- `OPENROUTER_API_KEY`: absent
- `CEREBRAS_API_KEY`: absent

Groq 1-request sanity check result:

- `provider_request_success`: `false`
- `parser_success`: `false`
- `provider_name`: `Groq`
- `model_name`: `openai/gpt-oss-20b`
- `request_id`: `dfc52b0bf51a46d2a7adba8c9e569af7`
- `http_attempt_id`: `1`
- `request_started_at`: `2026-08-18T11:17:30.528+00:00`
- `request_finished_at`: `2026-08-18T11:17:30.620+00:00`
- observed wall-clock latency: about `92 ms`
- failure type: `GroqHTTPError`
- failure reason: Cloudflare `403` / `Error 1010: Access denied` / `browser_signature_banned`

Interpretation:

- The adapter architecture itself is in place and unit-tested.
- The only configured provider in this workspace still cannot complete a live request because Groq blocks the current browser/network signature.
- No other provider could be live-checked because no API keys are configured.

## Tests

Passed locally:

- `pytest -q tests/test_provider_architecture.py tests/test_llm_diagnostics.py tests/test_metrics.py`
  - 18 passed
- `pytest -q tests/test_live_provider_client.py tests/test_llm_request_config.py`
  - 14 passed
- `python -m py_compile` on all touched provider/diagnostic modules and tests
  - passed

## Files Changed

- `src/llm/provider_architecture.py`
- `src/llm/request_config.py`
- `src/llm/diagnostics.py`
- `src/common/logging_schema.py`
- `src/common/metrics.py`
- `tests/test_provider_architecture.py`

## Verdict

`MULTI_PROVIDER_LAYER_INCOMPLETE`

Reason: the architecture and tests are in place, but live validation is not complete because Groq remains blocked in this environment and Gemini / OpenRouter / Cerebras are not configured with API keys.
