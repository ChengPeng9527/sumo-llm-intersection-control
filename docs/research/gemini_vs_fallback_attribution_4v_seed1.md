# Gemini vs Fallback Attribution 4V Seed1

## Scope
This note compares three existing 4V seed1 artifacts without rerunning experiments:
- Rule-based 4V seed1
- Fallback-only 4V seed1
- Genuine-live Gemini Raw LLM 4V seed1

The comparison is descriptive only. No significance tests are claimed.

## Evidence Sources
- [Rule-based run metadata](/D:/Sumo/sumo_train/results/raw/FE01_RULE_BASED_v4_seed1/run_metadata.json)
- [Rule-based step records](/D:/Sumo/sumo_train/results/raw/FE01_RULE_BASED_v4_seed1/step_records.csv)
- [Fallback-only step records](/D:/Sumo/sumo_train/results/raw/FB_ONLY_v4_seed1_mock/step_records.csv)
- [Fallback-only ablation report](/D:/Sumo/sumo_train/docs/research/fallback_only_ablation_report.md)
- [Genuine Gemini step records](/D:/Sumo/sumo_train/results/raw/GEMINI_RAW_LLM_4V_S1_PILOT_v4_seed1_gemini5_real/step_records.csv)
- [Genuine Gemini pilot log](/D:/Sumo/sumo_train/results/raw/GEMINI_RAW_LLM_4V_S1_PILOT_v4_seed1_gemini5_real/pilot_stdout.log)
- [Historical raw LLM step records](/D:/Sumo/sumo_train/results/raw/GEMINI_RAW_LLM_4V_S1_PILOT_v4_seed1_real/step_records.csv)

## Comparison Table
| Controller | Operational waiting | Mean speed | Completion rate | Throughput | Collision count | Episode duration | Final action distribution |
|---|---:|---:|---:|---:|---:|---:|---|
| Rule-based 4V seed1 | 82.0 | 2.3098 m/s | 100% | 4 | 0 | 114 steps | WAIT 276, PROCEED 104, FREE 54 |
| Fallback-only 4V seed1 | 11.0 | 7.5839 m/s | 100% | 4 | 0 | 52 steps | PROCEED 70, FREE 50, WAIT 12 |
| Genuine-live Gemini Raw LLM 4V seed1 | 11.0 | 7.5839 m/s | 100% | 4 | 0 | 52 steps | PROCEED 70, FREE 50, WAIT 12 |

## Gemini Attribution Details
- Logical provider requests: 53
- Successful requests: 53/53
- Parser success: 53/53
- Fallback rate: 0/53
- Request provenance: complete
- Vehicle rows: 132
- LLM_RAW rows: 82
- Deterministic interface rows: 50
- LLM_RAW final-action share: 82/132 = 62.1%
- Deterministic interface share: 50/132 = 37.9%

## Direct Attribution Questions
1. Fallback-only compared with Rule-based: the fallback-only controller is substantially better.
   - Operational waiting drops from 82.0 to 11.0 steps, a reduction of 71.0 steps or about 86.6%.
   - Mean speed rises from 2.3098 m/s to 7.5839 m/s, an increase of 5.2741 m/s or about 228.4%.
2. Genuine Gemini compared with Fallback-only: no further traffic improvement is visible in this single seed.
   - Waiting is unchanged at 11.0 steps.
   - Mean speed is unchanged at 7.5839 m/s.
   - Final action distribution is identical.
3. Genuine Gemini vs historical fallback-heavy Raw LLM:
   - Traffic metrics are identical.
   - Final action distribution is identical.
   - The difference is provenance attribution: the historical run attributes the same 82 rows to fallback, whereas the genuine-live run attributes them to successful LLM output.
4. The evidence supports the claim that fallback contributes substantially.
   - The fallback-only controller already recovers almost all of the traffic benefit relative to the rule-based baseline.
5. The evidence does not show an additional traffic benefit from live Gemini beyond fallback-only in this single-seed comparison.
   - The live provider changes attribution, not the observed traffic outcome.

## Interpretation
The cleanest reading is that the traffic advantage in this 4V seed1 setting is dominated by the deterministic fallback / interface layer.

Live Gemini participation is real and provenance is now complete, but in this seed it does not change the final action distribution or the traffic metrics relative to fallback-only.

## Verdict
ATTRIBUTION_FALLBACK_DOMINANT
