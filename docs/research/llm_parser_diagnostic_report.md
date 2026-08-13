# LLM Parser Diagnostic Report

## Purpose

Run a minimal live Groq diagnostic to verify the current parser contract against real provider responses.

This diagnostic is a compatibility check, not a formal experiment.

## Diagnostic Configuration

- provider: `Groq`
- base URL: `https://api.groq.com/openai/v1`
- model: `openai/gpt-oss-20b`
- request count: `3`
- input size: minimal one-vehicle diagnostic input

## Observed Response Shapes

The live responses included:

- `JSON`
- `MARKDOWN_WRAPPED_JSON`

## Diagnostic Outcome

- provider request success count: `3`
- response content present count: `3`
- parser success count: `3`
- fallback count: `0`
- unique parser failure reasons: none

## Trace Evidence

Each diagnostic request produced a parsed decision trace with:

- provider connected
- response received
- parser success
- validated decision
- final decision
- logging success

## Evidence Path

`results/diagnostics/llm_parser_diagnostic/`

## Verdict

**PARSER_PATCH_LIVE_REVALIDATED**
