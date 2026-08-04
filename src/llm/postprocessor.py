from __future__ import annotations

from src.safety.route_conflict import routes_compatible


def choose_priority_vehicle(vehicle_states: list[dict]) -> dict | None:
    controlled = [state for state in vehicle_states if state.get("inside_control_zone")]
    if not controlled:
        return None
    return min(controlled, key=lambda state: state.get("time_to_intersection", float("inf")))


def apply_interface_rule(
    trace: dict[str, dict],
    vehicle_states: list[dict],
    target_field: str,
) -> dict[str, dict]:
    updated = {vid: dict(entry) for vid, entry in trace.items()}
    for state in vehicle_states:
        vid = state["vehicle_id"]
        if state.get("inside_control_zone"):
            continue
        updated[vid][target_field] = "FREE"
        updated[vid]["outside_control_zone_rule_applied"] = True
        updated[vid]["decision_source"] = "DETERMINISTIC_INTERFACE_RULE"
    return updated


def apply_cooperative_postprocessing(
    trace: dict[str, dict],
    vehicle_states: list[dict],
) -> dict[str, dict]:
    updated = {vid: dict(entry) for vid, entry in trace.items()}
    priority_vehicle = choose_priority_vehicle(vehicle_states)
    if priority_vehicle is None:
        return updated

    priority_route = priority_vehicle.get("route_id", "")
    priority_vehicle_id = priority_vehicle["vehicle_id"]
    for state in vehicle_states:
        vid = state["vehicle_id"]
        if not state.get("inside_control_zone"):
            continue
        if updated[vid]["postprocessed_decision"] != "WAIT":
            continue
        if routes_compatible(priority_route, state.get("route_id", "")):
            updated[vid]["postprocessed_decision"] = "PROCEED"
            updated[vid]["postprocess_applied"] = True
            updated[vid]["postprocess_reason"] = f"compatible_with_priority:{priority_vehicle_id}"
            updated[vid]["decision_source"] = "COOPERATIVE_POSTPROCESSOR"
    return updated
