from __future__ import annotations

import os
from pathlib import Path

from src.common.config import load_project_config
from src.common.logging_schema import FIELDNAMES
from src.common.metrics import (
    build_event,
    calculate_summary as _calculate_summary,
    empty_record,
    route_direction_from_route_id,
    run_artifact_paths,
    write_run_artifacts,
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


def get_env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _credential_candidate_paths() -> list[Path]:
    paths: list[Path] = []
    for env_name in ("GROQ_CREDENTIAL_FILE", "LLM_CREDENTIAL_FILE"):
        raw_path = os.getenv(env_name, "")
        if raw_path:
            paths.append(Path(raw_path))
    for user_env in (os.getenv("USERPROFILE", ""), os.getenv("HOME", "")):
        if user_env:
            paths.append(Path(user_env) / ".codex" / ".env")
    paths.extend([
        Path.home() / ".codex" / ".env",
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / ".codex" / ".env",
    ])
    return paths


def resolve_llm_api_key() -> str:
    for name in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "CEREBRAS_API_KEY"):
        value = os.getenv(name, "")
        if value:
            return value
    for candidate in _credential_candidate_paths():
        env_values = _load_env_file(candidate)
        for name in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "CEREBRAS_API_KEY"):
            value = env_values.get(name, "")
            if value:
                return value
    return ""


def resolve_sumo_config_path(scenario_id: str | None = None) -> Path:
    explicit = os.getenv("SUMO_CONFIG_PATH", "")
    if explicit:
        return Path(explicit)
    if scenario_id:
        scenario_path = PROJECT_ROOT / "simulation" / "generated_routes" / scenario_id / "simulation.sumocfg"
        if scenario_path.exists():
            return scenario_path
    return Path(CONFIG["sumo_config_path"])


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
        vehicle_count=extra.get("vehicle_count", 4),
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
        llm_raw_decision=extra.get("llm_raw_decision", raw_decision),
        validated_llm_decision=extra.get("validated_llm_decision", raw_decision),
        postprocessed_decision=extra.get("postprocessed_decision", raw_decision),
        final_decision=final_decision,
        conflict_detected=conflict,
        conflict_type=extra.get("conflict_type", ""),
        priority_reason=extra.get("priority_reason", ""),
        outside_control_zone_rule_applied=extra.get("outside_control_zone_rule_applied", False),
        postprocess_applied=extra.get("postprocess_applied", False),
        postprocess_reason=extra.get("postprocess_reason", ""),
        safety_override=extra.get("safety_override", raw_decision != final_decision),
        safety_reason=extra.get("safety_reason", ""),
        decision_source=extra.get("decision_source", "FALLBACK"),
        llm_called=extra.get("llm_called", False),
        llm_mode=extra.get("llm_mode", "mock"),
        llm_model=extra.get("llm_model", ""),
        request_id=extra.get("request_id", ""),
        request_simulation_step=extra.get("request_simulation_step", None),
        http_attempt_id=extra.get("http_attempt_id", None),
        prompt_hash=extra.get("prompt_hash", ""),
        request_started_at=extra.get("request_started_at", ""),
        request_finished_at=extra.get("request_finished_at", ""),
        llm_response_time_ms=extra.get("llm_response_time_ms", 0.0),
        finish_reason=extra.get("finish_reason", ""),
        prompt_tokens=extra.get("prompt_tokens", None),
        completion_tokens=extra.get("completion_tokens", None),
        total_tokens=extra.get("total_tokens", None),
        reasoning_tokens=extra.get("reasoning_tokens", None),
        visible_completion_tokens=extra.get("visible_completion_tokens", None),
        json_parse_success=extra.get("json_parse_success", False),
        retry_count=extra.get("retry_count", 0),
        request_attempt_count=extra.get("request_attempt_count", None),
        request_pacing_delay_ms=extra.get("request_pacing_delay_ms", None),
        retry_after_seconds=extra.get("retry_after_seconds", None),
        rate_limit_limit_tokens=extra.get("rate_limit_limit_tokens", None),
        rate_limit_remaining_tokens=extra.get("rate_limit_remaining_tokens", None),
        rate_limit_reset_tokens_seconds=extra.get("rate_limit_reset_tokens_seconds", None),
        rate_limit_limit_requests=extra.get("rate_limit_limit_requests", None),
        rate_limit_remaining_requests=extra.get("rate_limit_remaining_requests", None),
        rate_limit_reset_requests_seconds=extra.get("rate_limit_reset_requests_seconds", None),
        fallback_used=extra.get("fallback_used", False),
        provider_request_attempted=extra.get("provider_request_attempted", False),
        provider_request_success=extra.get("provider_request_success", False),
        requested_provider=extra.get("requested_provider", ""),
        requested_model=extra.get("requested_model", ""),
        actual_provider=extra.get("actual_provider", ""),
        actual_model=extra.get("actual_model", ""),
        provider_switch_count=extra.get("provider_switch_count", 0),
        provider_chain=extra.get("provider_chain", ()),
        provider_failure_reason=extra.get("provider_failure_reason", ""),
        provider_success=extra.get("provider_success", False),
        provider_name=extra.get("provider_name", ""),
        model_name=extra.get("model_name", ""),
        http_status=extra.get("http_status", None),
        response_object_type=extra.get("response_object_type", ""),
        response_content_present=extra.get("response_content_present", False),
        response_content_length=extra.get("response_content_length", 0),
        response_content_redacted=extra.get("response_content_redacted", ""),
        parser_input_present=extra.get("parser_input_present", False),
        parser_input_length=extra.get("parser_input_length", 0),
        parser_input_redacted=extra.get("parser_input_redacted", ""),
        parser_success=extra.get("parser_success", False),
        parser_action=extra.get("parser_action", ""),
        parser_failure_reason=extra.get("parser_failure_reason", ""),
        fallback_triggered=extra.get("fallback_triggered", False),
        fallback_reason=extra.get("fallback_reason", ""),
        exception_type=extra.get("exception_type", ""),
        exception_message_redacted=extra.get("exception_message_redacted", ""),
        latency_ms=extra.get("latency_ms", extra.get("llm_response_time_ms", 0.0)),
        departed=extra.get("departed", False),
        arrived=extra.get("arrived", False),
        collision=extra.get("collision", False),
    )


def apply_decision(traci, veh_id, decision):
    if decision == "WAIT":
        traci.vehicle.setSpeed(veh_id, 0)
    else:
        # Hand control back to SUMO so the vehicle follows normal car-following logic.
        traci.vehicle.setSpeed(veh_id, -1)


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
    print(f"Vehicle count: {summary.get('vehicle_count', 0)}")
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
        "vehicle_count": kwargs.get("vehicle_count", 4),
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
        "termination_reason": kwargs.get("termination_reason", ""),
    }


def resolve_sumo_termination_reason(
    *,
    simulation_step: int,
    simulation_steps: int,
    expected_remaining: int,
    arrived_count: int,
    target_vehicle_count: int | None = None,
) -> str | None:
    if expected_remaining <= 0:
        if target_vehicle_count is not None and arrived_count >= target_vehicle_count:
            return "ALL_VEHICLES_COMPLETED"
        return "SUMO_NO_EXPECTED_VEHICLES"
    if simulation_step + 1 >= simulation_steps:
        return "MAX_HORIZON_REACHED"
    return None
