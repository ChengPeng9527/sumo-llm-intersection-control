# Corrected Limitations v2

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

This limitations chapter is written against the corrected evidence base: valid 4V from `formal_v2` and corrected 8V from `formal_v4`.

## 1. Only 4V and 8V formal scenarios

The corrected formal evidence covers only two vehicle scales:

- 4 vehicles
- 8 vehicles

Any claim about 16V or higher-scale traffic is unsupported by the current evidence.

## 2. Only three seeds per controller-scale cell

Each controller-scale cell has only `n = 3` seeds.

That is sufficient for descriptive comparison, but not for strong inferential claims. The dissertation should therefore report means, standard deviations, and seed-level values rather than claim statistical significance unless separate evidence is added.

## 3. Low-density, single-intersection SUMO scope

The simulation design uses a single unsignalised intersection under low-density traffic assumptions.

This is useful for controlled comparison, but it limits generalisation to:

- denser traffic
- multiple intersections
- heterogeneous road layouts
- more realistic traffic interactions

## 4. External provider dependency

The live LLM path depends on an external Groq provider.

Provider failures are frequent and mostly rate-limit related. This is a major validity threat because the traffic result is not produced by an always-available model; it is produced by a pipeline that frequently falls back.

## 5. Fallback-heavy execution

Because provider success is low, most live requests fall back to deterministic handling. The dissertation must not describe the final traffic result as pure LLM performance.

The correct interpretation is pipeline-level behavior under constrained live-provider availability.

## 6. Live LLM contribution cannot be cleanly isolated

The corrected evidence does not cleanly separate:

- raw model quality
- prompt effect
- parser effect
- fallback effect
- cooperative postprocessing
- safety layer behaviour

The trace is rich enough to show the pipeline structure, but not rich enough to isolate each component’s causal contribution without extra ablation work.

## 7. Safety verifier insufficiently exercised

The formal evidence shows zero collisions and zero safety overrides, but also no meaningful activation of the safety verifier.

That means safety behaviour was operationally present but empirically under-exercised.

## 8. No real-world or hardware-in-the-loop validation

All evidence is simulation-based.

There is no physical robot, hardware-in-the-loop, or live-road validation. The dissertation therefore supports simulation-level claims only.

## 9. Historical formal_v2 8V execution defect

A historical execution-layer defect was discovered during post-experiment trace auditing:

- the nominal 8-vehicle `formal_v2` runs loaded the four-vehicle default SUMO configuration
- the raw traces therefore showed only 4 observed / departed / arrived vehicles
- those traces were excluded from the final dissertation analysis
- the corrected 8V evidence is taken from `formal_v4`

This should be presented as a scientific traceability correction, not hidden.

## 10. Limited postprocessor evidence

The valid corrected formal evidence does not show any visible postprocessor intervention.

That means the cooperative layer cannot be claimed to have improved traffic performance in the final evidence set.

## 11. Completion-rate saturation

Completion rate is `100%` across all valid runs, so it does not differentiate controllers. Waiting time, mean speed, and provider reliability are more informative.

## 12. Summary statement

The corrected dissertation is still defensible, but it must remain bounded by the tested scenarios and by the provider reliability threat. The results support a traceable pipeline-level comparison, not a universal control claim.

## 13. Operational waiting metric definition

The dissertation's waiting metric is an operational stop-like occupancy proxy derived from the recorded `speed_after_action < 0.1 m/s` condition. It is not a queueing-theory delay measure and should not be interpreted as a direct physical waiting-time estimate.
