from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VehicleState:
    vehicle_id: str
    route_id: str
    route_direction: str
    speed: float
    distance_to_intersection: float
    time_to_intersection: float
    inside_control_zone: bool
