from __future__ import annotations

from src.common.config import load_project_config
from src.safety.route_conflict import routes_conflict, routes_compatible


CONFIG = load_project_config()
TTC_THRESHOLD = float(CONFIG["tti_threshold_seconds"])


def detect_time_conflict(my_tti: float, other_tti: float) -> bool:
    if my_tti == float("inf") or other_tti == float("inf"):
        return False
    return abs(my_tti - other_tti) < TTC_THRESHOLD


def determine_conflict_type(route_a: str, route_b: str) -> str:
    if routes_compatible(route_a, route_b):
        return "compatible"
    if routes_conflict(route_a, route_b):
        return "route_conflict"
    return "unknown"
