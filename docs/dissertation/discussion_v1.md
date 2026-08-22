# Discussion v1

## 1. Discussion framing

This discussion separates four kinds of statements:

- **OBSERVED RESULT**: what the formal v2 artifacts actually show
- **INTERPRETATION**: the most defensible meaning of the result
- **LIMITATION**: what the result does not establish
- **SPECULATION**: a possible explanation that is not directly proven

The dissertation should preserve that separation throughout the chapter.

## 2. RQ1: What can the results actually support?

**OBSERVED RESULT**

- The LLM-assisted architecture has lower waiting time (`15` steps) and higher mean speed (`6.80 m/s`) than rule-based control (`82` steps, `2.31 m/s`) in the formal v2 scenarios.
- Completion rate is `100%` for every controller and scale, so completion does not differentiate the systems.

**INTERPRETATION**

- Under the evaluated low-density settings, the LLM-assisted decision pipeline appears more flow-friendly than the deterministic baseline.

**LIMITATION**

- The formal v2 data do not prove that the LLM alone caused the improvement.
- The live-provider path is fallback-heavy, so the observed traffic advantage belongs to the pipeline, not to a pure model-only controller.

**SPECULATION**

- The structured prompt plus cooperative pipeline may have encouraged more permissive decisions in compatible traffic conditions.

## 3. Why is waiting time lower for the LLM-assisted architecture?

**OBSERVED RESULT**

- LLM-assisted runs have much lower waiting time than rule-based runs in both 4V and 8V formal v2 cells.

**INTERPRETATION**

- The LLM-assisted pipeline is less conservative than the rule-based baseline in this low-density scenario.
- The raw and hybrid controllers both include a decision pipeline that can produce `PROCEED` more readily than the baseline interface rule.

**LIMITATION**

- Because provider success is low, especially at 8V, the result cannot be treated as strong evidence about the intrinsic quality of the model?s decisions.

**SPECULATION**

- Some of the observed difference may come from cooperative promotion of compatible flows and from the way fallback handling maps uncertain states into executable actions.

## 4. Does the advantage really come from the LLM?

**OBSERVED RESULT**

- Provider success is only `109 / 2664` across formal v2.
- Most live provider attempts fail and therefore fall back.

**INTERPRETATION**

- The observed performance advantage cannot be attributed solely to direct LLM decisions.
- The system performance is better described as a pipeline effect: the prompt, parser, validation, interface rules, fallback policy, and the occasional live LLM success all contribute.

**LIMITATION**

- The current evidence does not isolate the LLM contribution cleanly enough to claim that the LLM itself is responsible for the entire performance gap.

## 5. RQ2: Why did hybrid not clearly improve traffic metrics?

**OBSERVED RESULT**

- Hybrid and raw LLM have the same completion rate and collision count.
- Hybrid does not improve the traffic metrics in a way that is visible in the aggregate formal v2 table.
- Cooperative post-processing is rare: only `1` intervention across the full formal v2 dataset.

**INTERPRETATION**

- The cooperative layer exists, but it is not exercised often enough in formal v2 to materially change the aggregate traffic metrics.

**LIMITATION**

- A sparse intervention count makes it hard to argue that cooperative post-processing is a strong effect in this dataset.

**SPECULATION**

- The provider reliability ceiling may be the real bottleneck; if the live LLM is unavailable most of the time, the cooperative layer has little opportunity to reshape the trajectory.

## 6. RQ2 / RQ4: What does the 8V reliability difference mean?

**OBSERVED RESULT**

- Raw LLM 8V has only `3` provider successes out of `444` attempts.
- Hybrid and hybrid+safety each have `18` provider successes out of `444` attempts at 8V.

**INTERPRETATION**

- The hybrid architecture appears more robust than raw LLM at 8V.
- The raw path is the most fragile live-provider configuration in the formal v2 dataset.

**LIMITATION**

- The improvement remains modest relative to the total number of failed attempts, so it should not be overstated.

**SPECULATION**

- The different reliability profiles may reflect execution-order sensitivity or load sensitivity in the live-provider path.

## 7. RQ3: How should safety override = 0 be interpreted?

**OBSERVED RESULT**

- Safety overrides are zero across all formal v2 runs.
- Collisions are also zero across all formal v2 runs.

**INTERPRETATION**

- The safety layer was available and verified, but formal v2 did not require it to change any action.
- The data therefore support a statement of verified safety plumbing, not a measurable safety-efficiency trade-off.

**LIMITATION**

- Zero safety overrides do not prove that the safety verifier is unnecessary.
- They only show that the current low-density dataset did not force it to intervene.

**SPECULATION**

- The low-density scenario may simply be too conservative to activate the safety layer often.

## 8. RQ4: How strong is the scalability claim?

**OBSERVED RESULT**

- The formal v2 dataset covers only `4V` and `8V`.
- Traffic metrics are stable across these two scales in the low-density setting.
- Raw provider reliability worsens markedly at `8V`.

**INTERPRETATION**

- The system appears to remain operational across the tested low-density scales, but the live provider path becomes less reliable as scale increases.

**LIMITATION**

- There is no formal v2 evidence for `16V`.
- There is no basis for a broad scalability claim beyond the tested low-density range.

**SPECULATION**

- A denser or more congested scenario would likely magnify the reliability bottleneck, but that remains untested here.

## 9. Provider reliability as a validity threat

**OBSERVED RESULT**

- All `2555` failures are recorded as `RateLimitError`.
- The artifacts do not preserve HTTP status for those failed requests.

**INTERPRETATION**

- Provider reliability is the main validity threat in formal v2.
- The dissertation must treat provider availability as part of the system under evaluation, not as a noise source that can be ignored.

**LIMITATION**

- Because the failure artifacts do not expose HTTP status, the exact provider-side mechanism cannot be proven beyond the recorded exception type.

**SPECULATION**

- The difference between smoke-style success and formal-sweep failure may be explained by load, repetition, or provider throttling over time.

## 10. What the study really proves

**OBSERVED RESULT**

- The formal v2 experiment is complete, reproducible, collision-free, and traceable.
- The LLM-assisted pipeline shows lower waiting time than the rule-based baseline in the tested low-density scenarios.
- Live-provider reliability is weak and uneven, especially for raw LLM at 8V.

**INTERPRETATION**

- The dissertation can legitimately claim that the staged architecture works and that, under the tested scenarios, the LLM-assisted pipeline is associated with better traffic efficiency.

**LIMITATION**

- The study does not prove pure LLM superiority.
- It does not prove a safety trade-off.
- It does not prove general scalability to denser or larger scenarios.

**SPECULATION**

- The most plausible story is that the architecture is useful as a decision pipeline, but its LLM component is currently too unreliable to stand alone.

## 11. Recommended discussion sentence

> The formal v2 evidence suggests that a structured LLM-assisted decision pipeline can reduce waiting time relative to a rule-based baseline in the evaluated low-density scenarios, but the result is mediated by substantial provider fallback and therefore should be interpreted as pipeline-level behavior rather than a demonstration of intrinsic LLM superiority.
