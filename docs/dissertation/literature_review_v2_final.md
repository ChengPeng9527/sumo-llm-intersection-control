# Literature Review v2 Final

This literature review is written against the recovered local reference archive and the corrected dissertation evidence boundary. It focuses on the seven papers recovered from `C:\Users\Admin\Desktop\References\` and uses them only for the claims they actually support.

## 2.1 Autonomous intersection management and unsignalised junction control

Autonomous intersection management frames the junction as a shared coordination problem rather than a pure vehicle-dynamics problem. Dresner and Stone (2008) are the most important foundational reference in the recovered archive because they show that intersection performance depends on the access policy governing a conflict space. Their reservation-based framing makes two points that remain relevant for this dissertation. First, a controller must decide who may proceed into the junction. Second, the policy itself needs to be visible and auditable if performance is to be compared fairly.

Safarov (2022) extends that logic to an unregulated junction context. His thesis shows that traffic performance depends not only on infrastructure but also on the behavioural assumptions encoded in the vehicle model. This is directly relevant to the present SUMO dissertation because the project also evaluates a policy-driven junction rather than a signalised system. The key lesson is that interaction style matters: a single conservative participant can alter flow efficiency in a shared conflict space.

Taken together, these sources support a conservative background claim: unsignalised junctions are coordination problems in which policy design, behavioural assumptions, and access ordering all matter. They also show that efficiency and safety have always been joint concerns in the intersection-management literature.

## 2.2 Cooperative and multi-agent decision-making

The intersection literature already implies that a single isolated vehicle decision is rarely enough. Vehicles influence one another through a shared conflict space, so the unit of analysis is the interaction among multiple participants, not just one vehicle in isolation.

The present dissertation makes that interaction visible through a staged decision pipeline. The controller is not a black box. Instead, the method separates prompt construction, live-provider proposal, parsing, validation, deterministic fallback, cooperative post-processing, and safety verification. That design is consistent with the recovered literature because the literature repeatedly treats policy, access ordering, and safety as distinct from raw motion generation.

The cooperative aspect is therefore not presented as an abstract claim that the model is "cooperative" in itself. It is presented as a bounded control stage that may alter the final decision when local traffic conditions permit it. The literature supports that separation because it shows that coordination is an explicit policy problem, not an emergent property that can be assumed from a fluent model output.

## 2.3 Language models as planners and embodied reasoners

Huang et al. (2022) provide the clearest justification for using language models in a constrained planning role. Their zero-shot planner framing shows that an LLM can generate high-level action structure, but it also exposes a key limitation: a semantically plausible plan is not automatically executable. That distinction matters for this dissertation because the SUMO controller does not need a prose explanation. It needs a bounded, simulator-ready action object that can be parsed and validated.

PaLM-E (Driess et al., 2023) strengthens the same point from the embodied multimodal side. The paper links language reasoning with grounded sensor-like inputs, showing that language models become more useful when they are coupled to a structured view of the world rather than detached text alone. The present dissertation adopts that lesson at a simpler scale by converting the traffic scene into a canonical structured prompt instead of asking the model to infer the state from loosely phrased text.

The combined lesson is straightforward: language models are most defensible in embodied settings when they are treated as one stage in a constrained, grounded pipeline. They are not treated as self-sufficient controllers.

## 2.4 Large language models for autonomous driving

The autonomous-driving literature makes the relevance of LLMs more concrete. LLM4AD (Cui et al., 2025) frames language models as potentially useful across several parts of the driving stack, but it also emphasises challenges such as latency, trust, transparency, deployment constraints, safety, and privacy. These are not side issues. They are part of why a dissertation on LLM-assisted control must evaluate reliability as well as traffic outcome.

DriveAgent (Hou et al., 2025) contributes a more modular view of the same space. Its structured reasoning pipeline separates different reasoning functions rather than treating the model as a monolithic decision maker. That modularity is conceptually close to the present dissertation because the current project also uses a separated decision pipeline with explicit intermediate stages.

Dong et al. (2026) are perhaps the closest recovered paper to the current project in spirit. Their interactive decision-making work treats the driving scene as an explicit decision problem under safety constraints and uses a structured representation before invoking the LLM. That design move is important because it shows that the field is already moving toward traceable interaction-aware architectures rather than pure free-form generation.

## 2.5 Reliability, safety, and hybrid pipeline design

Across the recovered archive, reliability and safety appear as recurring constraints on LLM use. Huang et al. (2022) show that output can be plausible but not executable. LLM4AD (Cui et al., 2025) identifies operational challenges that remain open. Dong et al. (2026) build safety constraints into the decision process itself. The shared implication is that raw model output is not enough in a safety-relevant setting.

This is the justification for the dissertation's hybrid architecture. By separating raw proposal, parser validation, deterministic fallback, cooperative post-processing, and safety verification, the system allows each stage to be observed independently. That is not merely an engineering preference. It is an experimental necessity if the dissertation wants to know where a failure or decision came from.

The literature also supports using provider reliability as an empirical variable rather than hidden infrastructure noise. If a live provider is unreliable, then the final traffic behaviour is the behaviour of the pipeline under constrained provider availability. That is precisely why the dissertation logs provider success, parser success, fallback rate, latency, post-processing, and safety intervention.

## 2.6 Research gap

The recovered literature is coherent, but it is fragmented across problem settings. Dresner and Stone (2008) show why intersection coordination matters. Safarov (2022) shows that unregulated-junction performance depends on behavioural assumptions. Huang et al. (2022) show that language models can produce plans but need semantic translation to be executable. PaLM-E (Driess et al., 2023) shows that embodied reasoning benefits from grounding. LLM4AD (Cui et al., 2025), DriveAgent (Hou et al., 2025), and Dong et al. (2026) show that LLMs are increasingly relevant to driving, but they also make reliability, safety, latency, and simulation-to-reality transfer central concerns.

What is still missing is a controlled comparison that brings these ingredients together inside one frozen pipeline. The present dissertation is narrower than "can LLMs be used in autonomous driving?" and narrower than "can autonomous intersection management improve efficiency?" It asks whether a structured LLM-assisted decision pipeline can be compared fairly with deterministic alternatives under the same SUMO unsignalised-intersection scenario while tracking traffic outcomes, provider reliability, parser success, fallback behaviour, latency, and downstream interventions.

That gap is methodological as much as topical. The literature supports the ingredients individually, but not the exact combination of frozen prompt, frozen request configuration, deterministic fallback, cooperative post-processing, and safety verification that this dissertation evaluates. From that gap, the research questions follow naturally:

- **RQ1:** Does the LLM-assisted architecture change traffic efficiency relative to rule-based control?
- **RQ2:** Does cooperative post-processing change raw LLM behaviour in a measurable way?
- **RQ3:** Does deterministic safety verification change the final decision path, and is any safety-efficiency trade-off observable?
- **RQ4:** Does the system remain stable when the scenario scales from four vehicles to eight vehicles?

These questions are grounded in the recovered literature, but they are not answered by it. That makes them appropriate dissertation questions rather than retrospective confirmations.
