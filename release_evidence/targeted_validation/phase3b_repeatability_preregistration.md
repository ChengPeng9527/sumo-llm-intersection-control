# Supplementary RQ-S1 Fixed-State Repeatability Preregistration

## Question and boundary

**Primary question:** Does the distribution of Gemini candidate selections vary
repeatably across controlled waiting conditions?  This separately labelled
supplementary study reuses the Phase3B1-R2 fixed S3-12V template and formal
candidate-selection path.  It does not modify or reinterpret frozen Phase 1,
Phase 2, or Phase3B1-R2 evidence.

It is not designed to find an exact threshold, prove fairness, or prove
planner superiority.

## Registered matrix

| Condition | Two-STRAIGHT aggregate waiting | Independent logical requests |
| --- | ---: | ---: |
| `W08` | 8 s | 5 |
| `W19` | 19 s | 5 |
| `W20` | 20 s | 5 |
| `W24` | 24 s | 5 |

The maximum is 20 experimental logical requests: `W08_R1` through `W24_R5`.
An invalid request is retained and is never replaced or repeated.  One bounded
connectivity request may precede the experiment but is outside the 20-request
budget.  If it fails, all 20 entries are `NOT_RUN`.

## Frozen input and generation configuration

The candidate set, state template, prompt, parser, comparator, candidate
semantics, legal filtering, provider/model, and generation settings remain
unchanged.  Only the two opposite-STRAIGHT vehicles receive the registered
waiting value, divided equally.

- Provider/model: Google Gemini / `gemini-3.6-flash`
- Timeout: 60 s; maximum output tokens: 512
- Response: `application/json` and `responseJsonSchema` requiring exactly one
  supplied legal `selected_candidate_id`
- `temperature`, `top_p`, `top_k`, and `seed`:
  `NOT_EXPLICITLY_CONFIGURED`

Thus the study measures repeatability under the actual current pipeline,
including any provider-side defaults; it does not claim an explicitly fixed
generation seed.

## Provenance, outputs, and interpretation

Persist condition, replicate, waiting value, candidate IDs/hash, selected ID,
selection class, legality, provider/parser/fallback fields, latency, sanitised
raw output, timestamp, prompt hash, generation configuration, and provider
attempt count.  A request is `VALID` only with provider success, parser
success, no fallback, and a legal selection.  Valid selections are `R4`, `S2`,
or `OTHER_LEGAL`; all others are `INVALID`.

Report per-condition R4/S2/OTHER_LEGAL/INVALID counts and rates plus the full
20-request sequence.  Classification is fixed in advance:

- `REPEATABLE_ORDERED_SHIFT`: lower waiting mainly R4 and higher waiting mainly
  S2, with an ordered overall direction.
- `PARTIAL_REPEATABILITY`: a waiting-related shift with mixed replicates.
- `NO_CLEAR_REPEATABILITY`: no stable waiting-related distribution pattern.
- `INCONCLUSIVE`: insufficient valid decisions.

With five requests per condition, all uncertainty reporting is descriptive;
no strong inferential or generalisation claim is permitted.
