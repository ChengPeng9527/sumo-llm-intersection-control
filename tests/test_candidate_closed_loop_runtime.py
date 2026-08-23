from __future__ import annotations

from src.controllers.candidate_runtime import (
    DETERMINISTIC_CANDIDATE,
    GEMINI_CANDIDATE,
    CandidateGrantController,
    PlannerDecision,
)
from src.controllers.decision_pipeline import (
    execute_cooperative_comparator_pipeline,
    execute_llm_candidate_selector_pipeline,
)


def _state(
    vehicle_id: str,
    route_id: str,
    *,
    inside: bool = True,
    waiting: float = 0.0,
    distance: float = 10.0,
) -> dict:
    incoming, outgoing = route_id.split("_")
    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "incoming_edge": incoming,
        "outgoing_edge": f"-{outgoing}",
        "movement": "STRAIGHT",
        "speed": 4.0,
        "distance_to_intersection": distance,
        "time_to_intersection": distance / 4.0,
        "waiting_time": waiting,
        "inside_control_zone": inside,
    }


class _SafetyGuard:
    def __init__(self, blocked_vehicle_id: str = ""):
        self.blocked_vehicle_id = blocked_vehicle_id
        self.calls = 0

    def __call__(self, trace, vehicle_states):
        self.calls += 1
        guarded = {vehicle_id: dict(entry) for vehicle_id, entry in trace.items()}
        if self.blocked_vehicle_id in guarded:
            entry = guarded[self.blocked_vehicle_id]
            if entry.get("final_decision") == "PROCEED":
                entry["final_decision"] = "WAIT"
                entry["safety_override"] = True
                entry["safety_intervened"] = True
                entry["safety_reason"] = "test_dynamic_safety"
        return guarded


class _DeterministicPlanner:
    def __init__(self, safety):
        self.safety = safety
        self.calls = 0

    def __call__(self, states, groups, decision_epoch, simulation_step, simulation_time):
        self.calls += 1
        return PlannerDecision(
            trace=execute_cooperative_comparator_pipeline(
                states,
                groups,
                safety_guard_fn=self.safety,
            )
        )


def _controller(planner_mode=DETERMINISTIC_CANDIDATE, *, timeout=45.0, safety=None, planner=None):
    safety = safety or _SafetyGuard()
    planner = planner or _DeterministicPlanner(safety)
    return CandidateGrantController(
        planner_mode=planner_mode,
        planner_fn=planner,
        safety_guard_fn=safety,
        run_id="run-1",
        scenario_id="scenario-1",
        vehicle_count=2,
        seed=7,
        grant_timeout_seconds=timeout,
    ), planner, safety


def test_candidate_planner_modes_initialize():
    deterministic, _, _ = _controller(DETERMINISTIC_CANDIDATE)
    gemini, _, _ = _controller(GEMINI_CANDIDATE)

    assert deterministic.planner_mode == DETERMINISTIC_CANDIDATE
    assert gemini.planner_mode == GEMINI_CANDIDATE


def test_active_grant_persists_and_planner_is_not_called_each_update():
    controller, planner, _ = _controller()
    states = [_state("a", "N_S", waiting=5), _state("b", "E_W", waiting=1)]

    first = controller.update(states, simulation_step=0, simulation_time=0.0)
    second = controller.update(states, simulation_step=1, simulation_time=1.0)

    assert first.grant_started is True
    assert second.grant_started is False
    assert planner.calls == 1
    assert controller.active_grant is not None
    assert controller.active_grant.vehicle_ids == ("a",)
    assert second.trace["a"]["final_decision"] == "PROCEED"
    assert second.trace["b"]["final_decision"] == "WAIT"


def test_grant_clears_after_selected_vehicle_leaves_scope_and_new_epoch_starts():
    controller, planner, _ = _controller()
    initial = [_state("a", "N_S", waiting=5), _state("b", "E_W", waiting=1)]
    controller.update(initial, simulation_step=0, simulation_time=0.0)

    cleared = controller.update(
        [_state("a", "N_S", inside=False), _state("b", "E_W", waiting=2)],
        simulation_step=2,
        simulation_time=2.0,
    )

    assert cleared.grant_ended is True
    assert cleared.grant_clearance_reason == "ALL_GRANTED_VEHICLES_LEFT_CONTROL_SCOPE"
    assert cleared.decision_epoch_started is True
    assert planner.calls == 2
    assert controller.active_grant is not None
    assert controller.active_grant.vehicle_ids == ("b",)
    assert controller.completed_decision_records[0]["grant_end_time"] == 2.0


def test_grant_timeout_clears_without_immediate_reselection():
    controller, planner, _ = _controller(timeout=2.0)
    states = [_state("a", "N_S", waiting=5), _state("b", "E_W", waiting=1)]
    controller.update(states, simulation_step=0, simulation_time=0.0)

    timed_out = controller.update(states, simulation_step=2, simulation_time=2.0)

    assert timed_out.grant_ended is True
    assert timed_out.grant_clearance_reason == "GRANT_TIMEOUT"
    assert timed_out.decision_epoch_started is False
    assert planner.calls == 1
    assert controller.active_grant is None
    assert controller.completed_decision_records[0]["grant_clearance_reason"] == "GRANT_TIMEOUT"


def test_gemini_is_called_once_per_grant_and_fallback_selection_receives_grant():
    safety = _SafetyGuard()
    provider_calls = 0

    def planner(states, groups, decision_epoch, simulation_step, simulation_time):
        nonlocal provider_calls

        def malformed_provider(prompt):
            nonlocal provider_calls
            provider_calls += 1
            return "not json"

        return PlannerDecision(
            trace=execute_llm_candidate_selector_pipeline(
                states,
                groups,
                malformed_provider,
                provider_name="Gemini",
                model_name="gemini-3.6-flash",
                llm_mode="real",
                safety_guard_fn=safety,
            )
        )

    controller, _, _ = _controller(GEMINI_CANDIDATE, safety=safety, planner=planner)
    states = [_state("a", "N_S", waiting=5), _state("b", "E_W", waiting=1)]
    controller.update(states, simulation_step=0, simulation_time=0.0)
    controller.update(states, simulation_step=1, simulation_time=1.0)

    assert provider_calls == 1
    assert controller.active_grant is not None
    assert controller.active_grant.vehicle_ids == ("a",)
    record = controller.active_grant.decision_record
    assert record["fallback_used"] is True
    assert record["fallback_reason"] == "MALFORMED_JSON"
    assert record["grant_source"] == "DETERMINISTIC_FALLBACK"


def test_safety_remains_downstream_during_active_grant_without_cancelling_it():
    safety = _SafetyGuard(blocked_vehicle_id="a")
    controller, planner, _ = _controller(safety=safety)
    states = [_state("a", "N_S", waiting=5), _state("b", "E_W", waiting=1)]

    first = controller.update(states, simulation_step=0, simulation_time=0.0)
    second = controller.update(states, simulation_step=1, simulation_time=1.0)

    assert first.trace["a"]["final_decision"] == "WAIT"
    assert second.trace["a"]["final_decision"] == "WAIT"
    assert second.trace["a"]["safety_intervened"] is True
    assert planner.calls == 1
    assert controller.active_grant is not None


def test_canonical_decision_record_persists_required_local_inputs_and_actions():
    controller, _, _ = _controller()
    states = [
        dict(_state("a", "N_S", waiting=5, distance=12), origin="private", route_history=["private"]),
        _state("b", "E_W", waiting=1, distance=18),
    ]
    controller.update(states, simulation_step=3, simulation_time=3.0)
    controller.finish(simulation_step=5, simulation_time=5.0)

    record = controller.decision_records[0]
    required = {
        "run_id",
        "scenario_id",
        "vehicle_count",
        "seed",
        "planner",
        "decision_epoch",
        "simulation_time",
        "candidate_set",
        "candidate_features",
        "privacy_minimised_vehicle_inputs",
        "deterministic_candidate_id",
        "selected_candidate_id",
        "selection_source",
        "grant_vehicle_ids",
        "grant_start_time",
        "grant_end_time",
        "grant_clearance_reason",
        "safety_interventions_during_grant",
        "executed_actions",
        "request_parameters",
        "prompt_hash",
        "canonical_prompt_reconstruction_data",
    }
    assert required.issubset(record)
    local = record["privacy_minimised_vehicle_inputs"][0]
    assert local["waiting_time"] == 5
    assert local["distance_to_intersection"] == 12
    assert "origin" not in local
    assert "route_history" not in local
    assert record["executed_actions"]
