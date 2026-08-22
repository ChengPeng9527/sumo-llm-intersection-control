# Provider 10-Request Smoke Report

## Scope
- Provider: Groq
- Model: `openai/gpt-oss-20b`
- Request format: canonical live provider client and canonical structured prompt
- Request count: 10 sequential requests
- Output directory: `results/diagnostics/provider_10_request_smoke_v1/`

## Results
- provider success count: 10/10
- parser success count: 10/10
- provider success rate: 100%
- parser success given provider success: 100%
- fallback count: 0
- 429 count: 0
- retry count sum: 1
- mean latency: 6328.292 ms
- median latency: 538.785 ms
- p95 latency: 50671.42 ms
- total wall-clock time: 63.285809 s
- actual requests/min: 9.4808
- actual tokens/min: 10136.8697
- mean total tokens/request: 1069.2
- estimated safe interval between requests: 8.019 s
- sustainable requests/min estimate: 7.4822
- sustainable tokens/min estimate: 8000.0

## Per-request Notes
- Full request-level trace is saved at `results/diagnostics/provider_10_request_smoke_v1/provider_10_request_smoke_trace.jsonl`.
- One request incurred a retry, but there were no 429 responses and no parser failures.

## Gate
- Provider success >= 90%: PASS
- Parser success given provider success >= 95%: PASS

## Verdict
- 10-request smoke: PASS
