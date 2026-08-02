from __future__ import annotations

from src.safety.route_conflict import routes_conflict, routes_compatible
from src.safety.tti_safety import detect_time_conflict, determine_conflict_type


def verify_decisions(vehicle_states: list[dict], raw_decisions: dict[str, str]):
    final_decisions = dict(raw_decisions)
    conflict_flags: dict[str, bool] = {}
    conflict_types: dict[str, str] = {}

    proceed_candidates = [v for v in vehicle_states if raw_decisions.get(v["vehicle_id"]) == "PROCEED" and v["inside_control_zone"]]
    priority_vehicle = None
    if proceed_candidates:
        priority_vehicle = min(proceed_candidates, key=lambda v: v["time_to_intersection"])

    for state in vehicle_states:
        vid = state["vehicle_id"]
        raw = raw_decisions.get(vid, "WAIT")
        conflict = False
        ctype = ""

        if raw == "PROCEED" and state["inside_control_zone"]:
            for other in vehicle_states:
                other_id = other["vehicle_id"]
                if other_id == vid:
                    continue
                other_raw = raw_decisions.get(other_id, "WAIT")
                if other_raw != "PROCEED":
                    continue
                if routes_conflict(state["route_id"], other["route_id"]) and detect_time_conflict(
                    state["time_to_intersection"], other["time_to_intersection"]
                ):
                    conflict = True
                    ctype = determine_conflict_type(state["route_id"], other["route_id"])
                    break

            if conflict and priority_vehicle and vid != priority_vehicle["vehicle_id"]:
                final_decisions[vid] = "WAIT"

        if raw != "PROCEED" and raw != "FREE":
            final_decisions[vid] = "WAIT"

        if not state["inside_control_zone"] and raw == "PROCEED":
            final_decisions[vid] = "FREE"

        conflict_flags[vid] = conflict
        conflict_types[vid] = ctype

    return final_decisions, conflict_flags, conflict_types
