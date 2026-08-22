from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VehicleState:
    vehicle_id: str
    route_id: str
    incoming_edge: str = ""
    outgoing_edge: str = ""
    movement: str = "UNKNOWN"
    route_direction: str = "unknown"
    speed: float = 0.0
    distance_to_intersection: float = 0.0
    time_to_intersection: float = 0.0
    waiting_time: float = 0.0
    inside_control_zone: bool = False
