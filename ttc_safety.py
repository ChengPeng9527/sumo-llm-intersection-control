from __future__ import annotations

from common import CONFIG, estimate_time_to_intersection, is_in_control_zone
from src.safety.route_conflict import routes_conflict
from src.safety.tti_safety import detect_time_conflict


def verify_decisions(traci, vehicles, raw_decisions):
    vehicle_states = []
    for vid in vehicles:
        route_id = traci.vehicle.getRouteID(vid)
        speed = traci.vehicle.getSpeed(vid)
        vehicle_states.append(
            {
                "vehicle_id": vid,
                "route_id": route_id,
                "speed": speed,
                "distance_to_intersection": 0.0,
                "time_to_intersection": estimate_time_to_intersection(traci, vid),
                "inside_control_zone": is_in_control_zone(traci, vid),
            }
        )

    final_decisions = dict(raw_decisions)
    conflict_flags = {vid: False for vid in vehicles}

    controlled = [
        v for v in vehicle_states
        if v["inside_control_zone"] and raw_decisions.get(v["vehicle_id"]) == "PROCEED"
    ]
    priority = None
    if controlled:
        priority = min(controlled, key=lambda v: v["time_to_intersection"])

    for state in vehicle_states:
        vid = state["vehicle_id"]
        raw = raw_decisions.get(vid, "WAIT")

        if raw != "PROCEED":
            if not state["inside_control_zone"]:
                final_decisions[vid] = "FREE"
            else:
                final_decisions[vid] = raw
            continue

        if not state["inside_control_zone"]:
            final_decisions[vid] = "FREE"
            continue

        for other in vehicle_states:
            if other["vehicle_id"] == vid:
                continue
            if raw_decisions.get(other["vehicle_id"], "WAIT") != "PROCEED":
                continue
            if routes_conflict(state["route_id"], other["route_id"]) and detect_time_conflict(
                state["time_to_intersection"], other["time_to_intersection"]
            ):
                conflict_flags[vid] = True
                if not priority or vid != priority["vehicle_id"]:
                    final_decisions[vid] = "WAIT"
                break

    return final_decisions, conflict_flags
