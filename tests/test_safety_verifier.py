import pytest

from src.safety.safety_verifier import verify_decisions


def test_verify_decisions_applies_priority_to_conflicting_vehicles():
    vehicle_states = [
        {
            "vehicle_id": "car0",
            "route_id": "N_S",
            "speed": 5.0,
            "distance_to_intersection": 10.0,
            "time_to_intersection": 2.0,
            "inside_control_zone": True,
        },
        {
            "vehicle_id": "car1",
            "route_id": "E_W",
            "speed": 5.0,
            "distance_to_intersection": 12.0,
            "time_to_intersection": 2.2,
            "inside_control_zone": True,
        },
    ]
    raw_decisions = {"car0": "PROCEED", "car1": "PROCEED"}

    final_decisions, conflict_flags, conflict_types, priority_reason = verify_decisions(
        vehicle_states,
        raw_decisions,
    )

    assert priority_reason == "min_tti:car0"
    assert final_decisions["car0"] == "PROCEED"
    assert final_decisions["car1"] == "WAIT"
    assert conflict_flags["car0"] is True
    assert conflict_flags["car1"] is True
    assert conflict_types["car0"] == "route_conflict"
    assert conflict_types["car1"] == "route_conflict"


def test_verify_decisions_frees_outside_control_zone():
    vehicle_states = [
        {
            "vehicle_id": "car0",
            "route_id": "N_S",
            "speed": 5.0,
            "distance_to_intersection": 60.0,
            "time_to_intersection": 10.0,
            "inside_control_zone": False,
        }
    ]
    raw_decisions = {"car0": "PROCEED"}

    final_decisions, conflict_flags, conflict_types, priority_reason = verify_decisions(
        vehicle_states,
        raw_decisions,
    )

    assert final_decisions["car0"] == "FREE"
    assert conflict_flags["car0"] is False
    assert conflict_types["car0"] == ""
    assert priority_reason == "no_priority_vehicle"


def _state(
    vehicle_id: str,
    route_id: str,
    time_to_intersection: float,
    *,
    inside_control_zone: bool = True,
) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "speed": 5.0,
        "distance_to_intersection": time_to_intersection * 5.0,
        "time_to_intersection": time_to_intersection,
        "inside_control_zone": inside_control_zone,
    }


def test_verify_decisions_preserves_compatible_opposite_straights():
    states = [
        _state("north", "N_S", 2.0),
        _state("south", "S_N", 2.1),
    ]

    final, flags, conflict_types, _ = verify_decisions(
        states,
        {"north": "PROCEED", "south": "PROCEED"},
    )

    assert final == {"north": "PROCEED", "south": "PROCEED"}
    assert flags == {"north": False, "south": False}
    assert conflict_types == {"north": "", "south": ""}


def test_verify_decisions_preserves_conflicting_routes_with_separated_tti():
    states = [
        _state("north", "N_S", 1.0),
        _state("east", "E_W", 10.0),
    ]

    final, flags, conflict_types, _ = verify_decisions(
        states,
        {"north": "PROCEED", "east": "PROCEED"},
    )

    assert final == {"north": "PROCEED", "east": "PROCEED"}
    assert flags == {"north": False, "east": False}
    assert conflict_types == {"north": "", "east": ""}


def test_verify_decisions_overrides_all_nonpriority_conflicting_proposals():
    states = [
        _state("north", "N_S", 1.0),
        _state("east", "E_W", 1.1),
        _state("south", "S_E", 1.2),
    ]

    final, flags, conflict_types, reason = verify_decisions(
        states,
        {"north": "PROCEED", "east": "PROCEED", "south": "PROCEED"},
    )

    assert reason == "min_tti:north"
    assert final == {"north": "PROCEED", "east": "WAIT", "south": "WAIT"}
    assert flags == {"north": True, "east": True, "south": True}
    assert conflict_types == {
        "north": "route_conflict",
        "east": "route_conflict",
        "south": "route_conflict",
    }


def test_verify_decisions_downgrades_free_inside_control_zone_to_wait():
    states = [_state("car0", "N_S", 2.0)]

    final, flags, conflict_types, reason = verify_decisions(states, {"car0": "FREE"})

    assert final == {"car0": "WAIT"}
    assert flags == {"car0": False}
    assert conflict_types == {"car0": ""}
    assert reason == "no_priority_vehicle"


def test_verify_decisions_preserves_free_outside_control_zone():
    states = [_state("car0", "N_S", 10.0, inside_control_zone=False)]

    final, flags, conflict_types, reason = verify_decisions(states, {"car0": "FREE"})

    assert final == {"car0": "FREE"}
    assert flags == {"car0": False}
    assert conflict_types == {"car0": ""}
    assert reason == "no_priority_vehicle"


def test_verify_decisions_defaults_missing_action_to_wait():
    states = [_state("car0", "N_S", 2.0)]

    final, flags, conflict_types, reason = verify_decisions(states, {})

    assert final == {"car0": "WAIT"}
    assert flags == {"car0": False}
    assert conflict_types == {"car0": ""}
    assert reason == "no_priority_vehicle"


def test_verify_decisions_treats_unknown_route_as_conservative_conflict():
    states = [
        _state("valid", "N_S", 1.0),
        _state("unknown", "INVALID_ROUTE", 1.1),
    ]

    final, flags, conflict_types, reason = verify_decisions(
        states,
        {"valid": "PROCEED", "unknown": "PROCEED"},
    )

    assert reason == "min_tti:valid"
    assert final == {"valid": "PROCEED", "unknown": "WAIT"}
    assert flags == {"valid": True, "unknown": True}
    assert conflict_types == {"valid": "route_conflict", "unknown": "route_conflict"}


def test_verify_decisions_rejects_malformed_state_with_expected_key_error():
    malformed = _state("car0", "N_S", 2.0)
    del malformed["inside_control_zone"]

    with pytest.raises(KeyError, match="inside_control_zone"):
        verify_decisions([malformed], {"car0": "PROCEED"})
