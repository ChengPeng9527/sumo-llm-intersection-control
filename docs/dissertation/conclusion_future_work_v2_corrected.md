# Corrected Conclusion and Future Work v2

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

## 1. What was built?

The dissertation built a structured LLM-assisted decision pipeline for unsignalised intersection control in SUMO. The architecture separates:

- raw LLM proposal
- validation
- deterministic interface handling
- cooperative postprocessing
- safety verification
- trace logging
- seeded formal experiment execution

The implementation was designed to keep raw, validated, postprocessed, and final decisions traceable in the logs.

## 2. What was evaluated?

The corrected evidence base combines:

- valid 4V evidence from `formal_v2`
- corrected 8V evidence from `formal_v4`

Across the corrected evidence, the dissertation evaluates:

- rule-based control
- raw LLM control
- hybrid control
- hybrid + safety control
- 4V and 8V scales
- three seeds per controller-scale cell

## 3. What was observed?

The corrected evidence supports four main observations:

1. The LLM-assisted pipeline shows lower waiting time and higher mean speed than the rule-based baseline in the tested scenarios.
2. Rule-based performance degrades substantially from 4V to 8V.
3. The LLM-assisted traffic-level metrics remain comparatively stable across the tested 4V-to-8V range.
4. Provider reliability remains weak, fallback-heavy, and rate-limit constrained.

## 4. What cannot be concluded?

The dissertation does **not** prove:

- pure LLM superiority
- general scalability to dense traffic
- real-world road validity
- safety superiority
- that the cooperative postprocessor materially changes traffic performance in the valid evidence
- that the provider path is sufficiently reliable for deployment

## 5. RQ summary

### RQ1
The LLM-assisted pipeline exhibited lower waiting time and higher mean speed than the rule-based baseline in the tested SUMO scenarios.

### RQ2
No clear traffic-performance advantage was observed for the hybrid architecture over the raw LLM architecture in the corrected evidence.

### RQ3
The safety layer was implemented and operationally present, but the formal evidence did not sufficiently exercise it.

### RQ4
Traffic-level robustness is visible from 4V to 8V, but provider-level reliability remains a major limitation.

## 6. Main contribution

The dissertation’s main contribution is a reproducible and traceable comparison of controller architectures for unsignalised intersection control, together with an explicit analysis of how live-provider availability and fallback behaviour shape the final system behaviour.

That is a stronger and more defensible contribution than a claim of universal LLM superiority.

## 7. Future work

Future work should focus on evidence gaps that are genuinely supported by the current limitations:

- higher-density traffic
- 16V or larger-scale experiments
- additional intersection topologies
- more seeds
- local or self-hosted LLM comparison
- controlled fallback ablation
- scenarios that deliberately trigger the safety verifier
- real-time or hardware-in-the-loop validation
- stronger provider-reliability engineering

## 8. Final conclusion

The corrected evidence shows that a frozen, traceable LLM-assisted decision pipeline can be implemented and evaluated systematically in SUMO. It can outperform a rule-based baseline on the tested traffic metrics, and the corrected 8V evidence confirms that the observed traffic behaviour persists in the larger of the two tested scales.

At the same time, live-provider reliability remains a first-order validity threat, so the final dissertation claim must stay at the level of pipeline behaviour rather than pure LLM intelligence.

The intermediate `formal_v3` batch is excluded from the final dissertation evidence because two rule-based 8V runs did not complete all arrivals within the fixed termination window.
