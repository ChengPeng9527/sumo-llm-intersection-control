from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .logging_schema import FIELDNAMES, EVENT_FIELDS
from .config import load_project_config


CONFIG = load_project_config()
RESULTS_DIR = CONFIG["results_dir_path"]


def ensure_results_dir() -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR


def route_direction_from_route_id(route_id: str) -> str:
    mapping = {
        "N_S": "north_south",
        "S_N": "south_north",
        "E_W": "east_west",
        "W_E": "west_east",
    }
    return mapping.get(route_id, "unknown")


def empty_record(**overrides):
    record = {name: None for name in FIELDNAMES}
    record.update(
        {
            "run_id": overrides.get("run_id", ""),
            "experiment_id": overrides.get("experiment_id", ""),
            "controller": overrides.get("controller", ""),
            "controller_version": overrides.get("controller_version", "v1"),
            "safety_enabled": overrides.get("safety_enabled", False),
            "scenario_id": overrides.get("scenario_id", ""),
            "density": overrides.get("density", ""),
            "seed": overrides.get("seed", 0),
            "simulation_step": overrides.get("simulation_step", 0),
            "simulation_time_seconds": overrides.get("simulation_time_seconds", 0.0),
            "vehicle_id": overrides.get("vehicle_id", ""),
            "route_id": overrides.get("route_id", ""),
            "route_direction": overrides.get("route_direction", "unknown"),
            "speed_before_action": overrides.get("speed_before_action", 0.0),
            "speed_after_action": overrides.get("speed_after_action", 0.0),
            "distance_to_intersection": overrides.get("distance_to_intersection", 0.0),
            "time_to_intersection": overrides.get("time_to_intersection", 0.0),
            "inside_control_zone": overrides.get("inside_control_zone", False),
            "raw_decision": overrides.get("raw_decision", "WAIT"),
            "final_decision": overrides.get("final_decision", "WAIT"),
            "conflict_detected": overrides.get("conflict_detected", False),
            "conflict_type": overrides.get("conflict_type", ""),
            "safety_override": overrides.get("safety_override", False),
            "llm_called": overrides.get("llm_called", False),
            "llm_mode": overrides.get("llm_mode", "mock"),
            "llm_model": overrides.get("llm_model", ""),
            "llm_response_time_ms": overrides.get("llm_response_time_ms", 0.0),
            "json_parse_success": overrides.get("json_parse_success", False),
            "retry_count": overrides.get("retry_count", 0),
            "fallback_used": overrides.get("fallback_used", False),
            "departed": overrides.get("departed", False),
            "arrived": overrides.get("arrived", False),
            "collision": overrides.get("collision", False),
        }
    )
    return record


def build_event(**overrides):
    event = {name: None for name in EVENT_FIELDS}
    event.update(
        {
            "run_id": overrides.get("run_id", ""),
            "event_type": overrides.get("event_type", ""),
            "simulation_step": overrides.get("simulation_step", 0),
            "simulation_time_seconds": overrides.get("simulation_time_seconds", 0.0),
            "vehicle_id": overrides.get("vehicle_id", ""),
            "details": overrides.get("details", ""),
        }
    )
    return event


def write_csv(path: Path | str, rows: Iterable[dict], fieldnames: list[str]) -> None:
    ensure_results_dir()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path | str, data: dict) -> None:
    ensure_results_dir()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_jsonl(path: Path | str, rows: Iterable[dict]) -> None:
    ensure_results_dir()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def calculate_summary(records: list[dict], run_metadata: dict | None = None) -> dict:
    if not records:
        return {}

    total_rows = len(records)
    vehicles = sorted({r["vehicle_id"] for r in records if r.get("vehicle_id")})
    departed = sum(1 for r in records if r.get("departed"))
    arrived = sum(1 for r in records if r.get("arrived"))
    collisions = sum(1 for r in records if r.get("collision"))
    overrides = sum(1 for r in records if r.get("safety_override"))
    tti_conflicts = sum(1 for r in records if r.get("conflict_detected"))
    speeds = [float(r.get("speed_after_action") or 0.0) for r in records]
    waits = [1 for r in records if float(r.get("speed_after_action") or 0.0) < float(CONFIG["stop_speed"])]

    proceed = sum(1 for r in records if r.get("final_decision") == "PROCEED")
    wait = sum(1 for r in records if r.get("final_decision") == "WAIT")
    free = sum(1 for r in records if r.get("final_decision") == "FREE")

    summary = {
        "vehicles_observed": len(vehicles),
        "departed": departed,
        "arrived": arrived,
        "throughput": arrived,
        "completion_rate": arrived / departed if departed else 0.0,
        "mean_speed": sum(speeds) / len(speeds),
        "mean_waiting_time": sum(waits) / len(vehicles) if vehicles else 0.0,
        "stopped_time_steps": len(waits),
        "stop_episode_count": len(waits),
        "collision_count": collisions,
        "tti_conflict_event_count": tti_conflicts,
        "safety_override_count": overrides,
        "safety_override_rate": overrides / total_rows if total_rows else 0.0,
        "proceed_count": proceed,
        "wait_count": wait,
        "free_count": free,
    }
    if run_metadata:
        summary.update(
            {
                "run_id": run_metadata.get("run_id", ""),
                "controller": run_metadata.get("controller", ""),
                "density": run_metadata.get("density", ""),
                "seed": run_metadata.get("seed", 0),
            }
        )
    return summary
