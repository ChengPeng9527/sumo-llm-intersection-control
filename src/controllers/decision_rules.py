from __future__ import annotations

from src.llm.postprocessor import choose_priority_vehicle
from src.safety.candidate_groups import build_safe_candidate_groups
from src.safety.cooperative_comparator import compare_and_build_decisions


def baseline_decide(vehicle_states: list[dict]) -> dict[str, str]:
    decisions: dict[str, str] = {}
    priority = choose_priority_vehicle(vehicle_states)
    for state in vehicle_states:
        vid = state["vehicle_id"]
        if not state.get("inside_control_zone"):
            decisions[vid] = "FREE"
        elif priority is not None and vid == priority["vehicle_id"]:
            decisions[vid] = "PROCEED"
        else:
            decisions[vid] = "WAIT"
    return decisions


def cooperative_decide(
    vehicle_states: list[dict],
    routes_compatible_fn=None,
    candidate_groups: list[list[str]] | None = None,
) -> dict[str, str]:
    if candidate_groups is not None:
        decisions, _ = compare_and_build_decisions(vehicle_states, candidate_groups)
        return decisions

    generated_groups = build_safe_candidate_groups(vehicle_states)
    if generated_groups:
        decisions, _ = compare_and_build_decisions(vehicle_states, generated_groups)
        return decisions

    if routes_compatible_fn is None:
        def routes_compatible_fn(route_a: str, route_b: str) -> bool:
            return route_a == route_b

    decisions: dict[str, str] = {}
    priority = choose_priority_vehicle(vehicle_states)
    if priority is None:
        for state in vehicle_states:
            decisions[state["vehicle_id"]] = "FREE"
        return decisions

    priority_route = priority.get("route_id", "")
    for state in vehicle_states:
        vid = state["vehicle_id"]
        if not state.get("inside_control_zone"):
            decisions[vid] = "FREE"
        elif vid == priority["vehicle_id"]:
            decisions[vid] = "PROCEED"
        elif routes_compatible_fn(priority_route, state.get("route_id", "")):
            decisions[vid] = "PROCEED"
        else:
            decisions[vid] = "WAIT"
    return decisions
