# Parser Compatibility Patch Report

## Scope

This report documents the parser compatibility fix that was validated against real Groq responses.

The fix was intentionally limited to parser compatibility behavior only:

- prompt unchanged
- model unchanged
- controller strategies unchanged
- postprocessor unchanged
- safety rules unchanged
- fallback policy unchanged
- decision space unchanged

## Motivation

The live diagnostic evidence showed that real provider responses could appear in multiple supported shapes, including:

- JSON
- markdown-wrapped JSON

The parser needed to handle those shapes without changing the dissertation method.

## Live Revalidation Result

The minimal live diagnostic completed successfully with:

- provider: `Groq`
- base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- request count: `3`
- provider request success count: `3`
- parser success count: `3`
- fallback count: `0`
- response shapes observed: `JSON`, `MARKDOWN_WRAPPED_JSON`

## Evidence Path

`results/diagnostics/llm_parser_diagnostic/`

## Interpretation

The parser compatibility patch is live revalidated.

This means the parser can now correctly handle the supported real response shapes seen in the diagnostic run, without relaxing the ambiguity rules or altering the controller method.

## Verdict

**PARSER_PATCH_LIVE_REVALIDATED**
