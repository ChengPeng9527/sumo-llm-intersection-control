# Dissertation Supervisor Draft v2

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

This draft integrates the corrected evidence base:

- valid 4V evidence from `formal_v2`
- corrected 8V evidence from `formal_v4`
- corrected results, discussion, limitations, and conclusion

## 1. Introduction

This dissertation investigates whether a structured LLM-assisted decision pipeline can support unsignalised intersection control in SUMO. The research is motivated by the practical question of whether LLM-based decision support can be combined with deterministic validation, cooperative postprocessing, and safety verification to produce a reproducible controller architecture for traffic simulation.

The problem is not simply whether an LLM can emit an action. The more relevant question is whether a full pipeline can convert uncertain live-provider outputs into executable vehicle-level decisions while remaining traceable and comparable against rule-based control.

The dissertation therefore studies a pipeline with explicit stages for raw proposal, validation, deterministic interface handling, cooperative postprocessing, safety verification, and logging.

## 2. Literature Review

[LITERATURE REVIEW TO BE COMPLETED AFTER SOURCE AUDIT]

The literature review should connect unsignalised intersection control, cooperative traffic coordination, LLM-assisted decision-making, and reliability/fallback concerns.

## 3. Methodology

### 3.1 System design

The implemented system separates the control stack into:

- prompt construction
- live-provider request handling
- structured response parsing
- deterministic validation
- cooperative postprocessing
- safety verification
- trace logging

### 3.2 Operational definitions

- `completion_rate = arrived_count / departed_count`
- `throughput = arrived_count`
- `mean_waiting_time = count(speed_after_action < 0.1 m/s) / unique vehicle count`
- `mean_speed = mean(speed_after_action)`

### 3.3 Evidence traceability

The logging schema retains raw, validated, postprocessed, and final decisions separately, together with provider metadata such as finish reason, token usage, parser success, fallback status, and latency.

### 3.4 Final evidence provenance

- Final 4V source: `results/formal_experiment/dissertation_formal_v2/`
- Final 8V source: `results/formal_experiment/dissertation_formal_v4/`
- Excluded from final results: `formal_v2` nominal 8V and `formal_v3`

## 4. Experimental Design

The corrected formal experiment uses a frozen matrix of four controllers, two vehicle scales, and three seeds. The corrected dissertation evidence base is:

- `formal_v2` valid 4V
- `formal_v4` corrected 8V

The invalid nominal 8V `formal_v2` traces are excluded.

## 5. Corrected Results

### 5.1 Experimental validity

- valid 4V: 12 runs, 4 vehicles observed / departed / arrived, 0 collisions
- corrected 8V: 12 runs, 8 vehicles observed / departed / arrived, 0 collisions

### 5.2 Core traffic findings

- rule-based 4V: waiting `82.0` steps, speed `2.3098 m/s`
- LLM-assisted 4V: waiting `15.0` steps, speed `6.8026 m/s`
- rule-based 8V: waiting `242.0417` steps, speed `1.1895 m/s`
- LLM-assisted 8V: waiting `15.2917` steps, speed `6.5991 m/s`

### 5.3 Provider reliability

Provider success remains low and fallback-heavy. The 8V corrected evidence shows particularly weak provider availability, with success rates around `0.3%–0.6%` for the LLM-bearing controllers.

### 5.4 Decision-flow behaviour

The valid corrected evidence contains no visible cooperative postprocessor intervention and no safety override. The trace schema nevertheless preserves these stages, which is important for interpretability.

## 6. Corrected Discussion

The corrected evidence supports a cautious claim that the LLM-assisted pipeline can improve traffic efficiency relative to the rule-based baseline in the tested SUMO scenarios. However, the traffic result must be interpreted as pipeline-level behavior because the live provider is fallback-heavy.

The corrected evidence does not show a clear traffic-performance advantage for hybrid over raw LLM, and it does not show any visible safety improvement from the safety layer. The most important limitation is provider reliability.

## 7. Corrected Limitations

The dissertation remains limited by:

- only 4V and 8V scenarios
- three seeds per cell
- low-density single-intersection SUMO scope
- external provider dependency
- fallback-heavy execution
- insufficient safety-layer exercise
- no real-world or HIL validation

The historical nominal 8V `formal_v2` defect should be presented transparently as an execution-layer issue that was corrected before final analysis.

## 8. Corrected Conclusion

The dissertation shows that a frozen, traceable LLM-assisted decision pipeline can be implemented and evaluated systematically in SUMO. It can outperform a rule-based baseline on the tested traffic metrics, and the corrected 8V evidence confirms that the observed traffic behaviour persists in the larger of the two tested scales.

At the same time, live-provider reliability remains a first-order validity threat, so the final dissertation claim must stay at the level of pipeline behaviour rather than pure LLM intelligence.

## 9. Tables and figures

### Tables

- **Table 1**: experimental configuration and evidence boundary.
- **Table 2**: traffic performance by controller and scale.
- **Table 3**: provider/parser/fallback reliability.
- **Table 4**: decision-source / postprocessor / safety behaviour.

### Figures

- **Figure 1**: mean waiting time by controller and scale.
- **Figure 2**: mean speed by controller and scale.
- **Figure 3**: provider success and fallback rate by LLM controller and scale.
- **Figure 4**: provider latency by controller and scale.

## 10. References

[REFERENCES TO BE FINALISED AFTER FINAL LITERATURE AUDIT; see `docs/dissertation/references_v1.md` and `docs/dissertation/existing_literature_audit_v2.md`]
