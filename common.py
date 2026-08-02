from __future__ import annotations

from pathlib import Path

from src.common.config import load_project_config
from src.common.logging_schema import FIELDNAMES
from src.common.metrics import (
    calculate_summary as _calculate_summary,
    empty_record,
    route_direction_from_route_id,
    write_csv,
    write_json,
    write_jsonl,
)


CONFIG = load_project_config()
PROJECT_ROOT = Path(CONFIG["project_root"])
RESULT_DIR = str(CONFIG["results_dir_path"])
INTERSECTION_CENTER = (
    float(CONFIG["intersection_center"]["x"]),
    float(CONFIG["intersection_center"]["y"]),
)
CONTROL_RADIUS = float(CONFIG["control_radius"])
MAX_SPEED = float(CONFIG["max_speed"])
STOP_SPEED = float(CONFIG["stop_speed"])
TTC_THRESHOLD = float(CONFIG["tti_threshold_seconds"])


def ensure_result_dir():
    Path(RESULT_DIR).mkdir(parents=True, exist_ok=True)


def distance_to_center(traci, veh_id):
    x, y = traci.vehicle.getPosition(veh_id)
    cx, cy = INTERSECTION_CENTER
    return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5


def is_in_control_zone(traci, veh_id):
    return distance_to_center(traci, veh_id) < CONTROL_RADIUS


def estimate_time_to_intersection(traci, veh_id):
    speed = traci.vehicle.getSpeed(veh_id)
    dist = distance_to_center(traci, veh_id)
    if speed < STOP_SPEED:
        return float("inf")
    return dist / speed


def get_vehicle_route(traci, veh_id):
    try:
        return traci.vehicle.getRouteID(veh_id)
    except Exception:
        return "unknown"


def create_record(
    experiment_id,
    controller,
    scenario,
    seed,
    step,
    traci,
    veh_id,
    raw_decision,
    final_decision,
    conflict=False,
    **extra,
):
    route_id = get_vehicle_route(traci, veh_id)
    speed_before = float(traci.vehicle.getSpeed(veh_id))
    tti = estimate_time_to_intersection(traci, veh_id)
    in_zone = is_in_control_zone(traci, veh_id)
    speed_after = float(extra.get("speed_after_action", speed_before))

    return empty_record(
        run_id=extra.get("run_id", f"{experiment_id}_{seed}"),
        experiment_id=experiment_id,
        controller=controller,
        controller_version=extra.get("controller_version", "v1"),
        safety_enabled=extra.get("safety_enabled", False),
        scenario_id=scenario,
        density=extra.get("density", "unknown"),
        seed=seed,
        simulation_step=step,
        simulation_time_seconds=extra.get("simulation_time_seconds", float(step)),
        vehicle_id=veh_id,
        route_id=route_id,
        route_direction=route_direction_from_route_id(route_id),
        speed_before_action=speed_before,
        speed_after_action=speed_after,
        distance_to_intersection=distance_to_center(traci, veh_id),
        time_to_intersection=tti,
        inside_control_zone=in_zone,
        raw_decision=raw_decision,
        final_decision=final_decision,
        conflict_detected=conflict,
        conflict_type=extra.get("conflict_type", ""),
        safety_override=raw_decision != final_decision,
        llm_called=extra.get("llm_called", False),
        llm_mode=extra.get("llm_mode", "mock"),
        llm_model=extra.get("llm_model", ""),
        llm_response_time_ms=extra.get("llm_response_time_ms", 0.0),
        json_parse_success=extra.get("json_parse_success", False),
        retry_count=extra.get("retry_count", 0),
        fallback_used=extra.get("fallback_used", False),
        departed=extra.get("departed", False),
        arrived=extra.get("arrived", False),
        collision=extra.get("collision", False),
    )


def apply_decision(traci, veh_id, decision):
    if decision == "WAIT":
        traci.vehicle.setSpeed(veh_id, 0)
    else:
        traci.vehicle.setSpeed(veh_id, MAX_SPEED)


def write_records(output_csv, records):
    write_csv(output_csv, records, FIELDNAMES)


def calculate_summary(records, all_seen_vehicles=None, run_metadata=None):
    summary = _calculate_summary(records, run_metadata=run_metadata)
    if all_seen_vehicles is not None:
        summary["vehicles_observed"] = len(list(all_seen_vehicles))
    return summary


def print_summary(title, summary, output_csv):
    print(f"=== {title} ===")
    print(f"Vehicles observed: {summary.get('vehicles_observed', 0)}")
    print(f"Departed: {summary.get('departed', 0)}")
    print(f"Arrived: {summary.get('arrived', 0)}")
    print(f"Throughput: {summary.get('throughput', 0)}")
    print(f"Completion rate: {summary.get('completion_rate', 0):.2%}")
    print(f"Average waiting time per vehicle: {summary.get('mean_waiting_time', 0):.2f} steps")
    print(f"Average speed: {summary.get('mean_speed', 0):.2f} m/s")
    print(f"TTC conflict events: {summary.get('tti_conflict_event_count', 0)}")
    print(f"Safety overrides: {summary.get('safety_override_count', 0)}")
    print(f"Saved: {output_csv}")


def build_run_metadata(**kwargs):
    return {
        "run_id": kwargs.get("run_id", ""),
        "controller": kwargs.get("controller", ""),
        "safety_enabled": kwargs.get("safety_enabled", False),
        "scenario_id": kwargs.get("scenario_id", ""),
        "density": kwargs.get("density", ""),
        "seed": kwargs.get("seed", 0),
        "start_time": kwargs.get("start_time", ""),
        "end_time": kwargs.get("end_time", ""),
        "git_commit": kwargs.get("git_commit", ""),
        "config_hash": kwargs.get("config_hash", ""),
        "routes_hash": kwargs.get("routes_hash", ""),
        "network_hash": kwargs.get("network_hash", ""),
        "prompt_version": kwargs.get("prompt_version", ""),
        "llm_mode": kwargs.get("llm_mode", "mock"),
        "llm_model": kwargs.get("llm_model", ""),
        "status": kwargs.get("status", "pending"),
    }
