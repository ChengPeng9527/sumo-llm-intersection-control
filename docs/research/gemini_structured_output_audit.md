# Gemini Structured Output Audit

## Scope

- Provider: `Gemini`
- Model: `gemini-3.6-flash`
- Timeout: `60.0 s`
- Request budget: `max_completion_tokens = 512`
- Thinking: `minimal`
- Structured output: `responseMimeType = application/json`, `responseJsonSchema` enabled

## Root Cause

- The earlier Gemini requests were reaching `MAX_TOKENS` because the adapter was only setting `maxOutputTokens` and `responseMimeType`, while leaving Gemini's structured schema and thinking control unspecified.
- The live responses were returning only partial JSON fragments, so the parser could not complete the canonical decision-object parse.

## Old Gemini Request Configuration

- `model = gemini-3.6-flash`
- `maxOutputTokens = 512`
- `responseMimeType = application/json`
- `responseJsonSchema = omitted`
- `thinkingConfig = omitted`
- `temperature`, `topP`, `candidateCount = not explicitly set`

## New Gemini Request Configuration

- `model = gemini-3.6-flash`
- `maxOutputTokens = 512`
- `responseMimeType = application/json`
- `responseJsonSchema = canonical decisions object schema`
- `thinkingConfig = {"thinkingLevel": "minimal"}`
- `temperature`, `topP`, `candidateCount = not explicitly set`

## Live Results

- `gemini_structured_001`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`1479.11 ms`, prompt_tokens=`903`, completion_tokens=`62`, total_tokens=`965`, thoughts_token_count=`None`
- `gemini_structured_002`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`1714.08 ms`, prompt_tokens=`903`, completion_tokens=`87`, total_tokens=`990`, thoughts_token_count=`None`
- `gemini_structured_003`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`22191.5 ms`, prompt_tokens=`903`, completion_tokens=`87`, total_tokens=`990`, thoughts_token_count=`None`
- `gemini_structured_004`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`13628.83 ms`, prompt_tokens=`903`, completion_tokens=`62`, total_tokens=`965`, thoughts_token_count=`None`
- `gemini_structured_005`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`18415.7 ms`, prompt_tokens=`903`, completion_tokens=`62`, total_tokens=`965`, thoughts_token_count=`None`
- `gemini_structured_006`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`30813.03 ms`, prompt_tokens=`903`, completion_tokens=`62`, total_tokens=`965`, thoughts_token_count=`None`
- `gemini_structured_007`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`1941.61 ms`, prompt_tokens=`903`, completion_tokens=`87`, total_tokens=`990`, thoughts_token_count=`None`
- `gemini_structured_008`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`8485.69 ms`, prompt_tokens=`903`, completion_tokens=`62`, total_tokens=`965`, thoughts_token_count=`None`
- `gemini_structured_009`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`15432.42 ms`, prompt_tokens=`903`, completion_tokens=`62`, total_tokens=`965`, thoughts_token_count=`None`
- `gemini_structured_010`: provider_success=`True`, parser_success=`True`, finish_reason=`STOP`, http_status=`200`, latency=`13868.41 ms`, prompt_tokens=`903`, completion_tokens=`62`, total_tokens=`965`, thoughts_token_count=`None`

## Summary

- provider success: `10/10`
- parser success: `10/10`
- MAX_TOKENS: `0`
- HTTP 429: `0`
- HTTP 403: `0`
- timeout: `0`
- mean latency: `12797.04 ms`
- median latency: `13748.62 ms`
- total wall-clock time: `127971.44 ms`

## Diagnostics

- provider_switch_count remained `0` on every request.
- fallback_triggered remained `false` on every request.
- `thoughts_token_count` is preserved when the response metadata exposes it.

## Tests

- `tests/test_provider_architecture.py`
- `tests/test_llm_request_config.py`
- `python -m py_compile` on the touched source files

## Verdict

- `GEMINI_STRUCTURED_OUTPUT_READY`
