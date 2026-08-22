# Figure Data Audit v1  
  
Repository: D:\Sumo\sumo_train  
Evidence boundary: 4V = valid formal_v2; 8V = corrected formal_v4. 
  
## Figure 1 - Mean waiting time  
- Source files: results/formal_experiment/dissertation_formal_v2/summary.json and results/formal_experiment/dissertation_formal_v4/summary.json.  
- Exact runs included: 4V valid runs FE01_RULE_BASED_v4_seed1, FE01_RULE_BASED_v4_seed2, FE01_RULE_BASED_v4_seed3, FE04_RAW_LLM_v4_seed1_real, FE04_RAW_LLM_v4_seed2_real, FE04_RAW_LLM_v4_seed3_real, FE05_HYBRID_v4_seed1_real, FE05_HYBRID_v4_seed2_real, FE05_HYBRID_v4_seed3_real, FE06_HYBRID_SAFETY_v4_seed1_real, FE06_HYBRID_SAFETY_v4_seed2_real, FE06_HYBRID_SAFETY_v4_seed3_real; 8V corrected runs FE01_RULE_BASED_v8_seed1_v4, FE01_RULE_BASED_v8_seed2_v4, FE01_RULE_BASED_v8_seed3_v4, FE04_RAW_LLM_v8_seed1_v4_real, FE04_RAW_LLM_v8_seed2_v4_real, FE04_RAW_LLM_v8_seed3_v4_real, FE05_HYBRID_v8_seed1_v4_real, FE05_HYBRID_v8_seed2_v4_real, FE05_HYBRID_v8_seed3_v4_real, FE06_HYBRID_SAFETY_v8_seed1_v4_real, FE06_HYBRID_SAFETY_v8_seed2_v4_real, FE06_HYBRID_SAFETY_v8_seed3_v4_real.  
- Aggregation unit: one controller-scale cell; one run value per seed.  
- Aggregation formula: sample mean and sample SD over the run-level mean waiting time values.  
- Seed-level raw values: 4V Rule-based [82, 82, 82]; 4V Raw LLM [15, 15, 15]; 4V Hybrid [15, 15, 15]; 4V Hybrid + Safety [15, 15, 15]; 8V Rule-based [311, 86, 329.125]; 8V Raw LLM [12.875, 17.875, 15.125]; 8V Hybrid [12.875, 17.875, 15.125]; 8V Hybrid + Safety [12.875, 17.875, 15.125].  
- Plotted mean / SD: 4V Rule-based 82.000000 / 0.000000; 4V Raw LLM 15.000000 / 0.000000; 4V Hybrid 15.000000 / 0.000000; 4V Hybrid + Safety 15.000000 / 0.000000; 8V Rule-based 242.041667 / 135.439581; 8V Raw LLM 15.291667 / 2.504163; 8V Hybrid 15.291667 / 2.504163; 8V Hybrid + Safety 15.291667 / 2.504163.  
- Manuscript table value: same as the plotted means.  
- Figure == table == raw evidence: PASS. 
  
## Figure 2 - Mean speed  
- Source files: results/formal_experiment/dissertation_formal_v2/summary.json and results/formal_experiment/dissertation_formal_v4/summary.json.  
- Exact runs included: same run sets as Figure 1.  
- Aggregation unit: one controller-scale cell; one run value per seed.  
- Aggregation formula: sample mean and sample SD over the run-level mean speed values.  
- Seed-level raw values: 4V Rule-based [2.3097622930423896, 2.3097622930423896, 2.3097622930423896]; 4V Raw LLM [6.8025892176048055, 6.8025892176048055, 6.8025892176048055]; 4V Hybrid [6.8025892176048055, 6.8025892176048055, 6.8025892176048055]; 4V Hybrid + Safety [6.8025892176048055, 6.8025892176048055, 6.8025892176048055]; 8V Rule-based [0.654805928007573, 2.2552510688695557, 0.6584154336809727]; 8V Raw LLM [6.880360772144653, 6.2648633165096275, 6.65200275535317]; 8V Hybrid [6.880360772144653, 6.2648633165096275, 6.65200275535317]; 8V Hybrid + Safety [6.880360772144653, 6.2648633165096275, 6.65200275535317].  
- Plotted mean / SD: 4V Rule-based 2.309762 / 0.000000; 4V Raw LLM 6.802589 / 0.000000; 4V Hybrid 6.802589 / 0.000000; 4V Hybrid + Safety 6.802589 / 0.000000; 8V Rule-based 1.189491 / 0.922977; 8V Raw LLM 6.599076 / 0.311143; 8V Hybrid 6.599076 / 0.311143; 8V Hybrid + Safety 6.599076 / 0.311143.  
- Manuscript table value: same as the plotted means.  
- Figure == table == raw evidence: PASS. 
  
## Figure 3 - Provider success / fallback  
- Source files: results/formal_experiment/dissertation_formal_v2/summary.json and results/formal_experiment/dissertation_formal_v4/summary.json.  
- Exact runs included: 4V valid live-controller runs from formal_v2; 8V corrected live-controller runs from formal_v4.  
- Aggregation unit: pooled controller-scale cell counts; seed-level rates are reported separately for dispersion.  
- Aggregation formula: success rate = aggregate successes / aggregate attempts; fallback rate = aggregate fallbacks / aggregate attempts.  
- Seed-level raw values: 4V Raw LLM attempts [53, 53, 53], successes [10, 0, 0], fallbacks [43, 53, 53]; 4V Hybrid attempts [53, 53, 53], successes [9, 0, 0], fallbacks [44, 53, 53]; 4V Hybrid + Safety attempts [53, 53, 53], successes [9, 0, 0], fallbacks [44, 53, 53]; 8V Raw LLM attempts [290, 335, 303], successes [1, 1, 0], fallbacks [289, 334, 303]; 8V Hybrid attempts [290, 335, 303], successes [0, 1, 0], fallbacks [290, 334, 303]; 8V Hybrid + Safety attempts [290, 335, 303], successes [0, 0, 1], fallbacks [290, 335, 302].  
- Plotted mean / SD: 4V Raw LLM success 0.062893 / 0.088900; 4V Hybrid success 0.056604 / 0.080000; 4V Hybrid + Safety success 0.056604 / 0.080000; 8V Raw LLM success 0.002155 / 0.004400; 8V Hybrid success 0.001078 / 0.004400; 8V Hybrid + Safety success 0.001078 / 0.004400.  
- Manuscript table value: the current draft uses seed-level mean percentages for 8V, so the table is not yet aligned with the pooled-count rate.  
- Figure == table == raw evidence: FAIL. 
  
## Figure 4 - Provider latency  
- Source files: results/formal_experiment/dissertation_formal_v2/summary.json and results/formal_experiment/dissertation_formal_v4/summary.json.  
- Exact runs included: live-controller runs only; same run sets as Figure 3.  
- Aggregation unit: successful provider calls only, pooled within a controller-scale cell.  
- Aggregation formula: sample mean and sample SD over successful-call latency values.  
- Seed-level raw values: 4V Raw LLM [445.16], [543.54]; 4V Hybrid [1952.86]; 4V Hybrid + Safety [381.07]; 8V Raw LLM [445.16, 543.54]; 8V Hybrid [1952.86]; 8V Hybrid + Safety [381.07].  
- Plotted mean / SD: 4V Raw LLM 494.350000 / 69.565165; 4V Hybrid 1952.860000 / 0.000000; 4V Hybrid + Safety 381.070000 / 0.000000; 8V Raw LLM 494.350000 / 69.565165; 8V Hybrid 1952.860000 / 0.000000; 8V Hybrid + Safety 381.070000 / 0.000000.  
- Manuscript table value: latency uses successful calls only, so the plotted values and table values match.  
- Figure == table == raw evidence: PASS. 
