from __future__ import annotations

from common import CONFIG, estimate_time_to_intersection, is_in_control_zone
from src.safety.safety_verifier import verify_decisions as _verify_vehicle_states


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

    return _verify_vehicle_states(vehicle_states, raw_decisions)
