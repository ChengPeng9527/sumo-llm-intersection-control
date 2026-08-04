from types import SimpleNamespace

import baseline_controller
import cooperative_controller

from src.controllers.decision_pipeline import apply_safety_filter, build_decision_trace


def _build_state(vehicle_id: str, route_id: str, tti: float, inside: bool) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "speed": 5.0,
        "distance_to_intersection": 10.0,
        "time_to_intersection": tti,
        "inside_control_zone": inside,
    }


def test_safety_verifier_downgrades_unsafe_proceed_to_wait():
    traffic_state = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "E_W", 1.1, True),
    ]
    trace = build_decision_trace(
        traffic_state,
        {"car0": "PROCEED", "car1": "PROCEED"},
        {"car0": "PROCEED", "car1": "PROCEED"},
        {"llm_called": True},
    )
    trace = apply_safety_filter(trace, traffic_state)

    assert trace["car0"]["final_decision"] == "PROCEED"
    assert trace["car1"]["final_decision"] == "WAIT"
    assert trace["car1"]["safety_override"] is True
    assert trace["car1"]["safety_reason"] != ""


def test_safety_verifier_never_upgrades_wait_to_proceed():
    traffic_state = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "E_W", 1.1, True),
    ]
    trace = build_decision_trace(
        traffic_state,
        {"car0": "PROCEED", "car1": "WAIT"},
        {"car0": "PROCEED", "car1": "WAIT"},
        {"llm_called": True},
    )
    trace = apply_safety_filter(trace, traffic_state)

    assert trace["car1"]["final_decision"] == "WAIT"
    assert trace["car1"]["safety_override"] is False


def test_baseline_behavior_is_not_broken(monkeypatch):
    monkeypatch.setattr(baseline_controller, "is_in_control_zone", lambda _traci, vid: vid != "outside")
    monkeypatch.setattr(baseline_controller, "distance_to_center", lambda _traci, vid: {"car0": 2.0, "car1": 4.0, "outside": 100.0}[vid])

    class FakeVehicleAPI:
        def getSpeed(self, vid):
            return {"car0": 5.0, "car1": 5.0, "outside": 5.0}[vid]

        def getPosition(self, vid):
            return (0.0, 0.0)

    fake_traci = SimpleNamespace(vehicle=FakeVehicleAPI())
    monkeypatch.setattr(baseline_controller, "traci", fake_traci)

    decisions = baseline_controller.decide(["car0", "car1", "outside"])

    assert decisions["car0"] == "PROCEED"
    assert decisions["car1"] == "WAIT"
    assert decisions["outside"] == "FREE"


def test_cooperative_behavior_is_not_broken(monkeypatch):
    monkeypatch.setattr(cooperative_controller, "is_in_control_zone", lambda _traci, vid: vid != "outside")
    monkeypatch.setattr(cooperative_controller, "distance_to_center", lambda _traci, vid: {"car0": 2.0, "car1": 4.0, "outside": 100.0}[vid])
    monkeypatch.setattr(cooperative_controller, "get_vehicle_route", lambda _traci, vid: {"car0": "N_S", "car1": "E_W", "outside": "W_E"}[vid])

    class FakeVehicleAPI:
        def getSpeed(self, vid):
            return {"car0": 5.0, "car1": 5.0, "outside": 5.0}[vid]

        def getPosition(self, vid):
            return (0.0, 0.0)

    fake_traci = SimpleNamespace(vehicle=FakeVehicleAPI())
    monkeypatch.setattr(cooperative_controller, "traci", fake_traci)

    decisions = cooperative_controller.decide(["car0", "car1", "outside"])

    assert decisions["car0"] == "PROCEED"
    assert decisions["car1"] == "WAIT"
    assert decisions["outside"] == "FREE"
