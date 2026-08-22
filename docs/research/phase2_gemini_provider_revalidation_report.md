# Phase 2 Step 6 Gemini Provider Revalidation Report

## Purpose and provider decision

Phase 2 designates Google Gemini as its sole canonical live provider. Groq remains available only for historical compatibility; its earlier Cloudflare HTTP 403 is provider-infrastructure context, not model-performance evidence, and was not retried in Step 6.

## Existing architecture reused

The existing `MultiProviderClient`, `GeminiProviderAdapter`, REST/optional SDK transport, provider diagnostics, Step 5 candidate selector, strict parser, deterministic comparator fallback, action conversion, and safety verifier are reused. No parallel provider framework or dependency was added.

The Gemini adapter already supported structured JSON, 60-second requests, token metadata, and historical `gemini-3.6-flash` validation. Step 6 adds only the missing Phase 2 freeze configuration and the ability to pass the Step 5 candidate-selection JSON schema through the existing adapter.

## Canonical configuration

- Provider: `Gemini`
- Model: `gemini-3.6-flash`
- Base URL: `https://generativelanguage.googleapis.com/v1beta`
- Execution mode: `RESEARCH_FIXED_PROVIDER`
- Provider chain: `Gemini` only
- Timeout: `60.0` seconds
- Maximum completion tokens: `512`
- Response MIME type: `application/json`
- Thinking level: `minimal`
- Candidate contract: exactly `{"selected_candidate_id":"<supplied_candidate_id>"}`
- Fallback: frozen Step 4 deterministic comparator over the same candidate set
- Final authority: existing deterministic safety verifier

The model choice follows the repository's existing successful Gemini structured-output evidence and was revalidated with two live candidate-selection requests. No model benchmark or prompt sweep was performed.

## Credential mechanism

The existing credential loader now supports provider-specific resolution. Step 6 requires `GEMINI_API_KEY`, either in the process environment or in an already supported credential file such as the user's `.codex/.env`. Live revalidation used a process-only `GEMINI_API_KEY`; no key was printed, hard-coded, or written to a credential file. The explicit project model and base URL freeze values were used.

## Request, output, and fallback contracts

Gemini receives the unchanged Step 5 privacy-minimised traffic snapshot, exact Step 3 candidate groups, and the same descriptive candidate features used for comparison with Step 4. The Gemini response schema restricts `selected_candidate_id` to the candidate IDs supplied in that request.

Malformed JSON, missing/unknown/multiple candidate IDs, and provider errors remain invalid. They invoke the Step 4 comparator over the same candidate set. Candidate-to-action conversion and downstream safety verification remain unchanged.

## Validation

- Focused Step 6 pytest: `10 passed`
- Directly affected provider/candidate regression pytest: `74 passed`
- Full pytest suite: `141 passed`
- Existing Step 5 candidate-selector behavior remains covered.
- Historical Groq client construction remains covered for compatibility.

Mock Gemini mechanisms:

- M1 valid selection: `a|b`, parser success, no fallback.
- M2 malformed response: fallback to `a|b` with `MALFORMED_JSON`.
- M3 unknown candidate: fallback to `a|b` with `UNKNOWN_CANDIDATE_ID`.
- M4 provider error: fallback to `a|b` with `PROVIDER_FAILURE`.
- M5 legal disagreement: Gemini mock selected `c`, comparator selected `a|b`, disagreement preserved without fallback.

Mock outcomes are implementation validation, not research results.

## Live revalidation and usage

- Live decision episodes: `2`
- Live request count: `2` (`1` request per tested decision episode)
- Live success count: `2/2` (`100%`), both HTTP `200` with finish reason `STOP`
- Live parser success: `2/2` (`100%`)
- Live fallback count: `0/2` (`0%`)
- Live latency: `1250.23 ms`, `1383.38 ms`; mean `1316.81 ms`
- Live prompt tokens: `1497`, `1334`; mean `1415.5` per request
- Live completion tokens: `15`, `19`; mean `17.0` per request
- Live total tokens: `1512`, `1353`; mean `1432.5` per request
- Deterministic agreement: `2`; disagreement: `0`
- Legal Gemini selections: `2/2`
- Safety interventions: `0`

Both requests exercised the complete traffic-state to safe-candidate generation, Gemini request, strict parsing, candidate-to-action conversion, and deterministic safety-verification path. The returned executable evidence was one strict candidate-selection JSON object per request, selecting `veh_e|veh_w` and `veh_e_right|veh_w_right` respectively. No raw navigation route, origin, destination, or route history was exposed to Gemini.

Reliable token usage was returned by Gemini and propagated through the existing provenance. Monetary cost was not calculated because no frozen pricing evidence exists in project configuration.

## Freeze status

`GEMINI_PROVIDER_FROZEN`

The single-provider configuration is frozen for subsequent Phase 2 work. Two low-count live requests demonstrated connectivity, structured candidate output, parser success, usage capture, unchanged deterministic fallback availability, and downstream safety verification. This smoke sample establishes operability, not comparative model superiority or traffic-performance evidence.

## Limitations and deferred work

- Two requests are sufficient only for provider smoke validation; they do not estimate long-run reliability or latency variance.
- Both live choices agreed with the deterministic comparator, so legal disagreement handling remains supported by mock validation rather than observed live evidence.
- No formal 8/12/16-vehicle experiment, prompt tuning, model comparison, monetary pricing calculation, or dissertation update was performed.
- The canonical Python executable required approved execution outside the sandbox; the existing Gemini REST transport was used because the optional Google SDK is not installed.
- Formal Phase 2 experiments remain deferred to a later authorized step.
