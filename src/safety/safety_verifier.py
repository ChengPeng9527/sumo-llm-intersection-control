from __future__ import annotations

from src.safety.route_conflict import routes_conflict
from src.safety.tti_safety import detect_time_conflict, determine_conflict_type


def verify_decisions(vehicle_states: list[dict], raw_decisions: dict[str, str]):
    final_decisions = dict(raw_decisions)
    conflict_flags: dict[str, bool] = {}
    conflict_types: dict[str, str] = {}

    proceed_candidates = [
        v for v in vehicle_states
        if raw_decisions.get(v["vehicle_id"]) == "PROCEED" and v["inside_control_zone"]
    ]
    priority_vehicle = None
    if proceed_candidates:
        priority_vehicle = min(proceed_candidates, key=lambda v: v["time_to_intersection"])

    if priority_vehicle:
        priority_reason = f"min_tti:{priority_vehicle['vehicle_id']}"
    else:
        priority_reason = "no_priority_vehicle"

    for state in vehicle_states:
        vid = state["vehicle_id"]
        raw = raw_decisions.get(vid, "WAIT")
        conflict = False
        conflict_type = ""

        if raw == "PROCEED" and not state["inside_control_zone"]:
            final_decisions[vid] = "FREE"
        elif raw != "PROCEED":
            final_decisions[vid] = "FREE" if (raw == "FREE" and not state["inside_control_zone"]) else "WAIT"
        else:
            for other in vehicle_states:
                other_id = other["vehicle_id"]
                if other_id == vid:
                    continue
                if raw_decisions.get(other_id, "WAIT") != "PROCEED":
                    continue
                if routes_conflict(state["route_id"], other["route_id"]) and detect_time_conflict(
                    state["time_to_intersection"], other["time_to_intersection"]
                ):
                    conflict = True
                    conflict_type = determine_conflict_type(state["route_id"], other["route_id"])
                    if priority_vehicle and vid != priority_vehicle["vehicle_id"]:
                        final_decisions[vid] = "WAIT"
                    break

        conflict_flags[vid] = conflict
        conflict_types[vid] = conflict_type

    return final_decisions, conflict_flags, conflict_types, priority_reason
