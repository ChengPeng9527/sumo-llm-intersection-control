from __future__ import annotations

from src.safety.route_conflict import routes_compatible


def mock_llm_decision(traffic_state: list[dict]) -> dict[str, str]:
    decisions: dict[str, str] = {}
    controlled = [v for v in traffic_state if v["inside_control_zone"]]

    if not controlled:
        for v in traffic_state:
            decisions[v["vehicle_id"]] = "FREE"
        return decisions

    priority = min(controlled, key=lambda v: v["time_to_intersection"])
    priority_route = priority["route_id"]
    for v in traffic_state:
        vid = v["vehicle_id"]
        if not v["inside_control_zone"]:
            decisions[vid] = "FREE"
        elif vid == priority["vehicle_id"] or routes_compatible(priority_route, v["route_id"]):
            decisions[vid] = "PROCEED"
        else:
            decisions[vid] = "WAIT"
    return decisions
