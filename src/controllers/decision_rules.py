from __future__ import annotations

from src.llm.postprocessor import choose_priority_vehicle


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
) -> dict[str, str]:
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
