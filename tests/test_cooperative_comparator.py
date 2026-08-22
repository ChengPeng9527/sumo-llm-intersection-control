from src.controllers.decision_pipeline import execute_cooperative_comparator_pipeline
from src.safety.candidate_groups import build_safe_candidate_groups
from src.safety.cooperative_comparator import (
    build_decisions_from_selection,
    select_candidate_group,
)
from src.safety.route_conflict import routes_conflict


def _state(vehicle_id, route_id, *, waiting=0.0, tti=5.0, inside=True):
    incoming, outgoing = route_id.split("_")
    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "incoming_edge": incoming,
        "outgoing_edge": f"-{outgoing}",
        "waiting_time": waiting,
        "time_to_intersection": tti,
        "inside_control_zone": inside,
    }


def test_larger_compatible_group_beats_smaller_group():
    states = [_state("a", "N_S"), _state("b", "S_N"), _state("c", "E_W")]
    result = select_candidate_group(states, [["a"], ["a", "b"]])
    assert result.selected_vehicle_ids == ("a", "b")


def test_higher_aggregate_waiting_wins_equal_size_groups():
    states = [
        _state("a", "N_S", waiting=2),
        _state("b", "S_N", waiting=2),
        _state("c", "E_W", waiting=1),
        _state("d", "W_E", waiting=4),
    ]
    result = select_candidate_group(states, [["a", "b"], ["c", "d"]])
    assert result.selected_vehicle_ids == ("c", "d")


def test_maximum_waiting_then_arrival_break_remaining_ties():
    states = [
        _state("a", "N_S", waiting=2, tti=4),
        _state("b", "S_N", waiting=3, tti=5),
        _state("c", "E_W", waiting=1, tti=1),
        _state("d", "W_E", waiting=4, tti=3),
    ]
    assert select_candidate_group(states, [["a", "b"], ["c", "d"]]).selected_vehicle_ids == ("c", "d")

    states[2]["waiting_time"] = 2
    states[3]["waiting_time"] = 3
    assert select_candidate_group(states, [["a", "b"], ["c", "d"]]).selected_vehicle_ids == ("c", "d")


def test_final_tie_is_stable_and_selection_uses_a_safe_step3_group():
    states = [_state("a", "N_S", tti=3), _state("b", "S_N", tti=3), _state("c", "E_W", tti=3)]
    groups = build_safe_candidate_groups(states)
    results = [select_candidate_group(list(reversed(states)), groups) for _ in range(5)]

    assert all(result.selected_vehicle_ids == results[0].selected_vehicle_ids for result in results)
    assert list(results[0].selected_vehicle_ids) in groups
    selected_states = [state for state in states if state["vehicle_id"] in results[0].selected_vehicle_ids]
    assert all(
        not routes_conflict(left["route_id"], right["route_id"])
        for index, left in enumerate(selected_states)
        for right in selected_states[index + 1 :]
    )


def test_action_conversion_and_safety_filter_remain_downstream():
    states = [
        _state("a", "N_S", inside=True),
        _state("b", "E_W", inside=True),
        _state("outside", "W_E", inside=False),
    ]
    assert build_decisions_from_selection(states, ["a"]) == {
        "a": "PROCEED",
        "b": "WAIT",
        "outside": "FREE",
    }

    trace = execute_cooperative_comparator_pipeline(states, [["a"], ["b"]])
    assert trace["a"]["postprocessed_decision"] == "PROCEED"
    assert trace["a"]["final_decision"] == "PROCEED"
    assert trace["b"]["postprocessed_decision"] == "WAIT"
    assert trace["outside"]["final_decision"] == "FREE"
    assert trace["a"]["selected_candidate_id"] == "a"
    assert trace["a"]["candidate_ranking"]
