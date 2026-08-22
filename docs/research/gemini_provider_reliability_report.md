# Gemini Provider Reliability Report

## Configuration

- Provider: `Gemini`
- Model: `gemini-3.6-flash`
- Execution mode: `RESILIENT_MULTI_PROVIDER`
- Provider chain: `Gemini` only

## Summary

### 1-Request Smoke

- provider success: 1/1
- parser success: 1/1
- provider-switch events: 0
- mean latency: 16339.84 ms
- median latency: 16339.84 ms
- total wall-clock: 16339.84 ms
- mean prompt tokens: 628
- mean completion tokens: 13
- mean total tokens: 832
- 429 count: 0
- 403 count: 0
- timeout count: 0

### 5-Request Smoke

- provider success: 4/5
- parser success: 4/5
- provider-switch events: 0
- mean latency: 15075.41 ms
- median latency: 13954.75 ms
- total wall-clock: 75377.07 ms
- mean prompt tokens: 628
- mean completion tokens: 13.5
- mean total tokens: 821
- 429 count: 0
- 403 count: 0
- timeout count: 0

### 10-Request Smoke

- provider success: 9/10
- parser success: 9/10
- provider-switch events: 0
- mean latency: 11861.16 ms
- median latency: 6754.83 ms
- total wall-clock: 118611.6 ms
- mean prompt tokens: 628
- mean completion tokens: 13.11
- mean total tokens: 867.78
- 429 count: 0
- 403 count: 0
- timeout count: 0

## Request Log

### 1-Request Rows

| request_id | provider_success | parser_success | http_status | retry_count | provider_switch_count | latency_ms | prompt_tokens | completion_tokens | total_tokens | exception_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemini_smoke_1_001 | True | True | 200 | 0 | 0 | 16328.0 | 628 | 13 | 832 |  |

### 5-Request Rows

| request_id | provider_success | parser_success | http_status | retry_count | provider_switch_count | latency_ms | prompt_tokens | completion_tokens | total_tokens | exception_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemini_smoke_5_001 | True | True | 200 | 0 | 0 | 11828.0 | 628 | 14 | 841 |  |
| gemini_smoke_5_002 | True | True | 200 | 0 | 0 | 2828.0 | 628 | 14 | 886 |  |
| gemini_smoke_5_003 | True | True | 200 | 0 | 0 | 13953.0 | 628 | 14 | 760 |  |
| gemini_smoke_5_004 | True | True | 200 | 0 | 0 | 16688.0 | 628 | 12 | 797 |  |
| gemini_smoke_5_005 | False | False | None | 0 | 0 | None | None | None | None | ProviderRequestError |

### 10-Request Rows

| request_id | provider_success | parser_success | http_status | retry_count | provider_switch_count | latency_ms | prompt_tokens | completion_tokens | total_tokens | exception_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemini_smoke_10_001 | True | True | 200 | 0 | 0 | 19922.0 | 628 | 14 | 934 |  |
| gemini_smoke_10_002 | False | False | None | 0 | 0 | None | None | None | None | ProviderRequestError |
| gemini_smoke_10_003 | True | True | 200 | 0 | 0 | 6234.0 | 628 | 12 | 816 |  |
| gemini_smoke_10_004 | True | True | 200 | 0 | 0 | 22938.0 | 628 | 14 | 837 |  |
| gemini_smoke_10_005 | True | True | 200 | 0 | 0 | 22437.0 | 628 | 12 | 829 |  |
| gemini_smoke_10_006 | True | True | 200 | 0 | 0 | 2829.0 | 628 | 14 | 881 |  |
| gemini_smoke_10_007 | True | True | 200 | 0 | 0 | 2015.0 | 628 | 14 | 854 |  |
| gemini_smoke_10_008 | True | True | 200 | 0 | 0 | 2328.0 | 628 | 12 | 842 |  |
| gemini_smoke_10_009 | True | True | 200 | 0 | 0 | 2547.0 | 628 | 12 | 907 |  |
| gemini_smoke_10_010 | True | True | 200 | 0 | 0 | 7281.0 | 628 | 14 | 910 |  |

## Gate

- verdict: `GEMINI_PROVIDER_NOT_READY`
