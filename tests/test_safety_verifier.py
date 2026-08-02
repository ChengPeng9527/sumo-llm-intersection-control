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
