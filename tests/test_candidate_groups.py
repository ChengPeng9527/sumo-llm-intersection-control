from __future__ import annotations

from itertools import combinations

from src.safety.candidate_groups import build_safe_candidate_groups
from src.safety.route_conflict import routes_conflict


def _build_state(vehicle_id: str, route_id: str, tti: float, inside: bool = True) -> dict:
    incoming_edge, outgoing_approach = route_id.split("_", 1)
    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "incoming_edge": incoming_edge,
        "outgoing_edge": f"-{outgoing_approach}",
        "movement": "UNKNOWN",
        "speed": 5.0,
        "distance_to_intersection": 10.0,
        "time_to_intersection": tti,
        "inside_control_zone": inside,
    }


def _group_is_safe(group: list[str], states_by_id: dict[str, dict]) -> bool:
    for veh_a, veh_b in combinations(group, 2):
        if routes_conflict(states_by_id[veh_a]["route_id"], states_by_id[veh_b]["route_id"]):
            return False
    return True


def test_conflicting_movement_pairs_are_rejected():
    assert routes_conflict("N_S", "E_W") is True
    assert routes_conflict("N_E", "E_S") is True


def test_compatible_movement_pairs_are_accepted():
    assert routes_conflict("N_W", "E_N") is False
    assert routes_conflict("N_W", "S_E") is False
    assert routes_conflict("N_S", "S_N") is False


def test_single_vehicle_candidate_generation_works():
    states = [_build_state("veh_1", "N_S", 2.0)]
    assert build_safe_candidate_groups(states) == [["veh_1"]]


def test_compatible_multi_vehicle_candidate_generation_works():
    states = [
        _build_state("veh_1", "N_W", 1.0),
        _build_state("veh_2", "E_N", 1.5),
        _build_state("veh_3", "S_E", 2.0),
        _build_state("veh_4", "W_S", 2.5),
        _build_state("veh_5", "N_S", 3.0),
    ]
    groups = build_safe_candidate_groups(states)
    state_by_id = {state["vehicle_id"]: state for state in states}

    assert ["veh_1", "veh_2", "veh_3", "veh_4"] in groups
    assert ["veh_5"] in groups
    assert all(_group_is_safe(group, state_by_id) for group in groups)


def test_candidate_generation_is_deterministic():
    states = [
        _build_state("veh_b", "E_N", 2.0),
        _build_state("veh_a", "N_W", 1.0),
        _build_state("veh_c", "W_S", 3.0),
    ]
    first = build_safe_candidate_groups(states)
    second = build_safe_candidate_groups(list(reversed(states)))

    assert first == second


def test_empty_or_minimal_states_are_handled_safely():
    assert build_safe_candidate_groups([]) == []
    assert build_safe_candidate_groups([_build_state("veh_1", "N_S", 1.0, inside=False)]) == []
    assert build_safe_candidate_groups([_build_state("veh_1", "N_S", 1.0), {"vehicle_id": "veh_2", "route_id": "INVALID", "inside_control_zone": True}]) == [["veh_1"]]


def test_existing_straight_route_behavior_is_not_broken():
    states = [
        _build_state("veh_1", "N_S", 1.0),
        _build_state("veh_2", "S_N", 1.2),
    ]
    groups = build_safe_candidate_groups(states)

    assert ["veh_1", "veh_2"] in groups
