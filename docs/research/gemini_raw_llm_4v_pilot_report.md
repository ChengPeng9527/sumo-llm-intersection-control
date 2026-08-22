# Gemini Raw LLM 4V Pilot Report

## 1. Summary
- Run directory: `D:\Sumo\sumo_train\results\raw\GEMINI_RAW_LLM_4V_S1_PILOT_BILLING_REAL_v4_seed1_real`
- Scenario: `formal_low_v4_seed1`
- Vehicle count: `4`
- Seed: `1`
- Termination reason: `ALL_VEHICLES_COMPLETED`
- Departed / arrived: `4` / `4`
- Collision count: `0`
- Provider request success: `44/53` (`83.02%`)
- Parser success: `44/53` (`100.0%` given provider success)
- Fallback count: `9/53` (`16.98%`)
- 429 / 403 / timeout: `0` / `0` / `0`
- Finish reason counts: `{'STOP': 44, '': 9}`
- MAX_TOKENS count: `0`
- Mean / median / max latency (ms): `18445.72` / `20136.89` / `60073.81`
- Mean prompt / completion / total tokens: `649.623` / `41.453` / `691.075`
- Total tokens: `36627`
- Provider switch count: `0`
- Residual SUMO processes: `0`

## 2. Request-Level Evidence
The table below is grouped by unique simulation step, which is the unique request unit in this pilot trace. Each request fans out to one or more vehicle rows. Request identifiers, HTTP attempt identifiers, prompt hashes, and request timestamps are present as columns in the trace schema but are blank in this run, so `simulation_step` is the reliable request key in the saved artifact.

| Step | Provider success | Parser success | Fallback | Finish | Latency ms | Prompt tok | Completion tok | Total tok | Decision source(s) |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | yes | yes | no | STOP | 24233.33 | 621 | 20 | 641 | DETERMINISTIC_INTERFACE_RULE:1 |
| 1 | yes | yes | no | STOP | 31723.66 | 622 | 20 | 642 | DETERMINISTIC_INTERFACE_RULE:1 |
| 2 | yes | yes | no | STOP | 30469.61 | 622 | 33 | 655 | DETERMINISTIC_INTERFACE_RULE:1 |
| 3 | yes | yes | no | STOP | 29581.43 | 621 | 33 | 654 | DETERMINISTIC_INTERFACE_RULE:1 |
| 4 | yes | yes | no | STOP | 28761.94 | 622 | 20 | 642 | DETERMINISTIC_INTERFACE_RULE:1 |
| 5 | yes | yes | no | STOP | 22330.55 | 650 | 21 | 671 | LLM_RAW:1 |
| 6 | no | no | yes | EMPTY | 951.28 | 0 | 0 | 0 | DETERMINISTIC_INTERFACE_RULE:1, FALLBACK:1 |
| 7 | no | no | yes | EMPTY | 1518.93 | 0 | 0 | 0 | DETERMINISTIC_INTERFACE_RULE:1, FALLBACK:1 |
| 8 | no | no | yes | EMPTY | 1325.64 | 0 | 0 | 0 | DETERMINISTIC_INTERFACE_RULE:1, FALLBACK:1 |
| 9 | no | no | yes | EMPTY | 960.41 | 0 | 0 | 0 | DETERMINISTIC_INTERFACE_RULE:1, FALLBACK:1 |
| 10 | no | no | yes | EMPTY | 3276.28 | 0 | 0 | 0 | DETERMINISTIC_INTERFACE_RULE:1, FALLBACK:1 |
| 11 | no | no | yes | EMPTY | 5688.63 | 0 | 0 | 0 | DETERMINISTIC_INTERFACE_RULE:2, FALLBACK:1 |
| 12 | no | no | yes | EMPTY | 20136.89 | 0 | 0 | 0 | DETERMINISTIC_INTERFACE_RULE:2, FALLBACK:1 |
| 13 | no | no | yes | EMPTY | 60073.81 | 0 | 0 | 0 | DETERMINISTIC_INTERFACE_RULE:2, FALLBACK:1 |
| 14 | no | no | yes | EMPTY | 12860.50 | 0 | 0 | 0 | DETERMINISTIC_INTERFACE_RULE:1, FALLBACK:2 |
| 15 | yes | yes | no | STOP | 32636.84 | 829 | 53 | 882 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:2 |
| 16 | yes | yes | no | STOP | 10886.08 | 830 | 74 | 904 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:2 |
| 17 | yes | yes | no | STOP | 19882.70 | 830 | 74 | 904 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:2 |
| 18 | yes | yes | no | STOP | 27891.69 | 836 | 54 | 890 | LLM_RAW:3 |
| 19 | yes | yes | no | STOP | 28294.94 | 931 | 70 | 1001 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:3 |
| 20 | yes | yes | no | STOP | 20663.40 | 930 | 95 | 1025 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:3 |
| 21 | yes | yes | no | STOP | 22625.55 | 921 | 94 | 1015 | DETERMINISTIC_INTERFACE_RULE:2, LLM_RAW:2 |
| 22 | yes | yes | no | STOP | 34994.04 | 923 | 69 | 992 | DETERMINISTIC_INTERFACE_RULE:2, LLM_RAW:2 |
| 23 | yes | yes | no | STOP | 2475.53 | 920 | 69 | 989 | DETERMINISTIC_INTERFACE_RULE:2, LLM_RAW:2 |
| 24 | yes | yes | no | STOP | 6187.62 | 923 | 69 | 992 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:3 |
| 25 | yes | yes | no | STOP | 33043.82 | 928 | 70 | 998 | DETERMINISTIC_INTERFACE_RULE:2, LLM_RAW:2 |
| 26 | yes | yes | no | STOP | 29449.19 | 930 | 70 | 1000 | DETERMINISTIC_INTERFACE_RULE:2, LLM_RAW:2 |
| 27 | yes | yes | no | STOP | 3348.02 | 930 | 70 | 1000 | DETERMINISTIC_INTERFACE_RULE:2, LLM_RAW:2 |
| 28 | yes | yes | no | STOP | 32016.05 | 931 | 70 | 1001 | DETERMINISTIC_INTERFACE_RULE:2, LLM_RAW:2 |
| 29 | yes | yes | no | STOP | 24059.94 | 838 | 75 | 913 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:2 |
| 30 | yes | yes | no | STOP | 1402.96 | 833 | 60 | 893 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:2 |
| 31 | yes | yes | no | STOP | 2022.92 | 833 | 54 | 887 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:2 |
| 32 | yes | yes | no | STOP | 10314.67 | 834 | 75 | 909 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:2 |
| 33 | yes | yes | no | STOP | 31102.76 | 738 | 38 | 776 | LLM_RAW:2 |
| 34 | yes | yes | no | STOP | 30555.91 | 738 | 55 | 793 | LLM_RAW:2 |
| 35 | yes | yes | no | STOP | 1488.60 | 738 | 38 | 776 | LLM_RAW:2 |
| 36 | yes | yes | no | STOP | 21590.95 | 738 | 55 | 793 | LLM_RAW:2 |
| 37 | yes | yes | no | STOP | 14306.58 | 738 | 38 | 776 | LLM_RAW:2 |
| 38 | yes | yes | no | STOP | 16904.65 | 738 | 38 | 776 | LLM_RAW:2 |
| 39 | yes | yes | no | STOP | 2552.04 | 738 | 38 | 776 | LLM_RAW:2 |
| 40 | yes | yes | no | STOP | 12650.15 | 738 | 38 | 776 | LLM_RAW:2 |
| 41 | yes | yes | no | STOP | 34746.16 | 748 | 38 | 786 | LLM_RAW:2 |
| 42 | yes | yes | no | STOP | 1650.73 | 748 | 38 | 786 | LLM_RAW:2 |
| 43 | yes | yes | no | STOP | 22494.55 | 748 | 38 | 786 | LLM_RAW:2 |
| 44 | yes | yes | no | STOP | 27753.52 | 747 | 38 | 785 | LLM_RAW:2 |
| 45 | yes | yes | no | STOP | 12977.18 | 748 | 38 | 786 | LLM_RAW:2 |
| 46 | yes | yes | no | STOP | 10614.07 | 749 | 38 | 787 | LLM_RAW:2 |
| 47 | yes | yes | no | STOP | 11517.58 | 750 | 38 | 788 | LLM_RAW:2 |
| 48 | yes | yes | no | STOP | 11378.04 | 743 | 37 | 780 | DETERMINISTIC_INTERFACE_RULE:1, LLM_RAW:1 |
| 49 | yes | yes | no | STOP | 29088.87 | 714 | 36 | 750 | DETERMINISTIC_INTERFACE_RULE:2 |
| 50 | yes | yes | no | STOP | 28920.39 | 715 | 36 | 751 | DETERMINISTIC_INTERFACE_RULE:2 |
| 51 | yes | yes | no | STOP | 14408.92 | 715 | 36 | 751 | DETERMINISTIC_INTERFACE_RULE:2 |
| 52 | yes | yes | no | STOP | 24832.67 | 713 | 36 | 749 | DETERMINISTIC_INTERFACE_RULE:2 |

## 3. Decision Behaviour
- Final vehicle-row decision source counts: `{'DETERMINISTIC_INTERFACE_RULE': 50, 'LLM_RAW': 72, 'FALLBACK': 10}`
- Raw decision distribution: `{'FREE': 50, 'PROCEED': 70, 'WAIT': 12}`
- Validated decision distribution: `{'FREE': 50, 'PROCEED': 70, 'WAIT': 12}`
- Postprocessed decision distribution: `{'FREE': 50, 'PROCEED': 70, 'WAIT': 12}`
- Final executed decision distribution: `{'FREE': 50, 'PROCEED': 70, 'WAIT': 12}`
- Postprocessor intervention count: `0`
- Safety override count: `0`
- Validated -> postprocessed change count: `0`
- Postprocessed -> final change count: `0`
- Successful Gemini-origin final control decisions: `72` vehicle-row actions
- Deterministic interface-rule final actions: `50` vehicle-row actions
- Fallback final actions: `10` vehicle-row actions

## 4. Traffic and Lifecycle
- Average waiting time per vehicle: `11.00` steps
- Average speed: `7.58 m/s`
- Throughput: `4`
- Episode termination reason: `ALL_VEHICLES_COMPLETED`
- Residual `sumo.exe` / `sumo-gui.exe`: `0`

## 5. Verdict
- Verdict: `GEMINI_RAW_LLM_4V_PILOT_NOT_READY`

## 6. Interpretation
- The pilot completed normally and all 4 vehicles departed and arrived.
- The live Gemini path produced successful request-level completions for 44/53 requests, with 9 request-level fallbacks.
- The trace shows no 429, 403, or timeout errors in this pilot.
- The main blocker is reliability, not SUMO lifecycle: provider success and fallback rate do not yet meet the pilot gate.
- The trace also leaves request_id/http_attempt_id/prompt_hash/timestamp fields blank in the saved step records, so request traceability is incomplete even though the run is otherwise traceable by simulation step.
