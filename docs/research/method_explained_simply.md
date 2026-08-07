# Method Explained Simply

## 1. What happens when a car gets near the intersection?

The system checks the current traffic state for each vehicle:

- how fast it is moving,
- how far it is from the intersection,
- how long it will take to reach the intersection,
- whether it is inside the control zone.

## 2. What does the LLM see?

The LLM sees a structured prompt built from:

- the vehicle state,
- the route conflict matrix,
- simple policy hints,
- instructions to return JSON only.

## 3. What actions can the LLM output?

The LLM can only choose:

- `PROCEED`
- `WAIT`
- `FREE`

## 4. What does validation do?

Validation makes sure the output is usable.

- invalid or missing actions become `WAIT`,
- actions are normalized into a standard uppercase form,
- the raw provider text is kept separate from the validated decision.

## 5. Why can the cooperative postprocessor change the decision?

The cooperative postprocessor looks for compatible vehicles near the same priority flow.

If a vehicle is waiting but is compatible with the current priority vehicle, the postprocessor may promote it to `PROCEED`.

This is how the system tries to avoid unnecessary waiting.

## 6. Why can the safety verifier change the decision again?

The safety verifier checks for route conflict and time conflict.

If two vehicles would create a conflict, the safety layer can downgrade one of them to `WAIT`.

This layer is deterministic and is meant to stop unsafe outcomes.

## 7. What does SUMO do at the end?

SUMO executes the final action on the vehicle.

The controller does not replace SUMO's physics or traffic model. It only decides the high-level action.

## 8. What is the difference between raw, hybrid, and hybrid + safety?

- `raw`: the validated LLM decision is used as the final decision.
- `hybrid`: the cooperative postprocessor can promote compatible waiting vehicles.
- `hybrid + safety`: the cooperative decision is checked again by the safety layer before execution.

## 9. Why did the live revalidation sometimes show a raw decision of MISSING but still end with PROCEED?

That means the provider response was received, but the parser did not find a direct valid action for the vehicle in the expected key format.

The system then normalized the action to `WAIT`, the cooperative postprocessor promoted it to `PROCEED` because the route was compatible, and the safety layer did not override it.

## 10. What roles do the LLM, postprocessor, and safety layer play?

- The LLM proposes a decision.
- The postprocessor tries to make the decision more cooperative.
- The safety layer makes sure the final action stays conservative when required.

## Simple Summary

The project is not trying to let the LLM control everything by itself. It is trying to make the LLM one part of a larger decision pipeline that is easier to inspect, safer to run, and easier to evaluate.
