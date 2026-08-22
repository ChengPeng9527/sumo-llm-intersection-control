# Figure 3 Denominator Audit v1

Repository: `D:\Sumo\sumo_train`
Evidence boundary: 4V = valid `formal_v2`; 8V = corrected `formal_v4`.

## Semantics

- `provider_attempt_rows` counts rows with `provider_request_attempted = True`.
- `provider_success_rows` counts rows with `provider_request_success = True`.
- `fallback_rows` counts rows with `fallback_used = True`.
- In the final evidence boundary, `fallback_used == fallback_triggered == provider_failure_rows` for every live-provider row that was inspected.
- Figure 3 uses pooled counts across the three seed runs in each controller-scale cell.
- Rule-based is omitted because it has no live-provider path and therefore no provider attempts.

## Pooled counts

| Controller | Scale | Attempts | Successes | Success rate | Fallbacks | Fallback rate | Parser success given success |
|---|---|---:|---:|---:|---:|---:|---:|
| Raw LLM | 4V | 444 | 26 | 5.86% | 418 | 94.14% | 100% |
| Raw LLM | 8V | 928 | 2 | 0.22% | 926 | 99.78% | 100% |
| Hybrid | 4V | 444 | 22 | 4.95% | 422 | 95.05% | 100% |
| Hybrid | 8V | 928 | 1 | 0.11% | 927 | 99.89% | 100% |
| Hybrid + Safety | 4V | 444 | 22 | 4.95% | 422 | 95.05% | 100% |
| Hybrid + Safety | 8V | 928 | 1 | 0.11% | 927 | 99.89% | 100% |

## Population check

- formal_v4 headline: `provider_attempt_rows = 2784`, `provider_success_rows = 4`, `provider_failure_rows = 2780`, `fallback_rows = 2780`.
- Population: the three live-provider 8V cells only, with 928 attempts per cell.
- The headline does **not** include rule-based rows, because those rows have no live-provider requests.

## Verdict

- Figure 3 and Table 3 now share the same pooled denominator and the same live-provider population.
- READY_FOR_FINAL_FORMATTING
