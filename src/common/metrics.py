from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .logging_schema import EVENT_FIELDS, FIELDNAMES
from .config import load_project_config
from src.safety.route_semantics import describe_route_id


CONFIG = load_project_config()
RESULTS_DIR = CONFIG["results_dir_path"]
RAW_RESULTS_DIR = RESULTS_DIR / "raw"
SUMMARIES_DIR = RESULTS_DIR / "summaries"
FIGURES_DIR = RESULTS_DIR / "figures"


def ensure_results_dir() -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR


def run_artifact_paths(run_id: str) -> dict[str, Path]:
    run_dir = RAW_RESULTS_DIR / run_id
    return {
        "run_dir": run_dir,
        "step_records": run_dir / "step_records.csv",
        "run_metadata": run_dir / "run_metadata.json",
        "events": run_dir / "events.jsonl",
        "decision_records": run_dir / "decision_records.jsonl",
        "summary": run_dir / "summary.json",
    }


def route_direction_from_route_id(route_id: str) -> str:
    try:
        semantics = describe_route_id(route_id)
    except ValueError:
        return "unknown"
    mapping = {
        "N": "north",
        "E": "east",
        "S": "south",
        "W": "west",
    }
    incoming = mapping.get(semantics.incoming_edge, "unknown")
    outgoing = mapping.get(semantics.outgoing_edge.lstrip("-"), "unknown")
    return f"{incoming}_{outgoing}"


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
            "vehicle_count": overrides.get("vehicle_count", 4),
            "seed": overrides.get("seed", 0),
            "simulation_step": overrides.get("simulation_step", 0),
            "simulation_time_seconds": overrides.get("simulation_time_seconds", 0.0),
            "vehicle_id": overrides.get("vehicle_id", ""),
            "route_id": overrides.get("route_id", ""),
            "incoming_edge": overrides.get("incoming_edge", ""),
            "outgoing_edge": overrides.get("outgoing_edge", ""),
            "movement": overrides.get("movement", "UNKNOWN"),
            "route_direction": overrides.get("route_direction", "unknown"),
            "speed_before_action": overrides.get("speed_before_action", 0.0),
            "speed_after_action": overrides.get("speed_after_action", 0.0),
            "distance_to_intersection": overrides.get("distance_to_intersection", 0.0),
            "time_to_intersection": overrides.get("time_to_intersection", 0.0),
            "waiting_time": overrides.get("waiting_time", 0.0),
            "inside_control_zone": overrides.get("inside_control_zone", False),
            "raw_decision": overrides.get("raw_decision", "WAIT"),
            "llm_raw_decision": overrides.get("llm_raw_decision", "MISSING"),
            "validated_llm_decision": overrides.get("validated_llm_decision", "WAIT"),
            "postprocessed_decision": overrides.get("postprocessed_decision", "WAIT"),
            "final_decision": overrides.get("final_decision", "WAIT"),
            "conflict_detected": overrides.get("conflict_detected", False),
            "conflict_type": overrides.get("conflict_type", ""),
            "priority_reason": overrides.get("priority_reason", ""),
            "outside_control_zone_rule_applied": overrides.get("outside_control_zone_rule_applied", False),
            "postprocess_applied": overrides.get("postprocess_applied", False),
            "postprocess_reason": overrides.get("postprocess_reason", ""),
            "candidate_groups": overrides.get("candidate_groups", ()),
            "candidate_ranking": overrides.get("candidate_ranking", ()),
            "selected_candidate_id": overrides.get("selected_candidate_id", ""),
            "selected_vehicle_ids": overrides.get("selected_vehicle_ids", ()),
            "candidate_selection_reason": overrides.get("candidate_selection_reason", ""),
            "llm_raw_output": overrides.get("llm_raw_output", ""),
            "llm_candidate_id": overrides.get("llm_candidate_id", ""),
            "deterministic_candidate_id": overrides.get("deterministic_candidate_id", ""),
            "candidate_agreement": overrides.get("candidate_agreement", None),
            "candidate_disagreement": overrides.get("candidate_disagreement", False),
            "fallback_selected_candidate": overrides.get("fallback_selected_candidate", ""),
            "final_selected_candidate": overrides.get("final_selected_candidate", ""),
            "selection_source": overrides.get("selection_source", ""),
            "safety_intervened": overrides.get("safety_intervened", False),
            "safety_override": overrides.get("safety_override", False),
            "safety_reason": overrides.get("safety_reason", ""),
            "decision_source": overrides.get("decision_source", "FALLBACK"),
            "llm_called": overrides.get("llm_called", False),
            "llm_branch_entered": overrides.get("llm_branch_entered", False),
            "live_provider_gate_entered": overrides.get("live_provider_gate_entered", False),
            "live_provider_enabled": overrides.get("live_provider_enabled", False),
            "credential_available": overrides.get("credential_available", False),
            "live_client_constructed": overrides.get("live_client_constructed", False),
            "provider_call_function_entered": overrides.get("provider_call_function_entered", False),
            "provider_request_kwargs_built": overrides.get("provider_request_kwargs_built", False),
            "provider_request_attempted": overrides.get("provider_request_attempted", False),
            "provider_request_skipped": overrides.get("provider_request_skipped", False),
            "provider_skip_reason": overrides.get("provider_skip_reason", ""),
            "fallback_trigger_reason": overrides.get("fallback_trigger_reason", ""),
            "llm_mode": overrides.get("llm_mode", "mock"),
            "llm_model": overrides.get("llm_model", ""),
            "request_id": overrides.get("request_id", ""),
            "request_simulation_step": overrides.get("request_simulation_step", None),
            "http_attempt_id": overrides.get("http_attempt_id", None),
            "prompt_hash": overrides.get("prompt_hash", ""),
            "request_started_at": overrides.get("request_started_at", ""),
            "request_finished_at": overrides.get("request_finished_at", ""),
            "llm_response_time_ms": overrides.get("llm_response_time_ms", 0.0),
            "finish_reason": overrides.get("finish_reason", ""),
            "prompt_tokens": overrides.get("prompt_tokens", None),
            "completion_tokens": overrides.get("completion_tokens", None),
            "total_tokens": overrides.get("total_tokens", None),
            "reasoning_tokens": overrides.get("reasoning_tokens", None),
            "visible_completion_tokens": overrides.get("visible_completion_tokens", None),
            "json_parse_success": overrides.get("json_parse_success", False),
            "retry_count": overrides.get("retry_count", 0),
            "request_attempt_count": overrides.get("request_attempt_count", None),
            "request_pacing_delay_ms": overrides.get("request_pacing_delay_ms", None),
            "retry_after_seconds": overrides.get("retry_after_seconds", None),
            "rate_limit_limit_tokens": overrides.get("rate_limit_limit_tokens", None),
            "rate_limit_remaining_tokens": overrides.get("rate_limit_remaining_tokens", None),
            "rate_limit_reset_tokens_seconds": overrides.get("rate_limit_reset_tokens_seconds", None),
            "rate_limit_limit_requests": overrides.get("rate_limit_limit_requests", None),
            "rate_limit_remaining_requests": overrides.get("rate_limit_remaining_requests", None),
            "rate_limit_reset_requests_seconds": overrides.get("rate_limit_reset_requests_seconds", None),
            "fallback_used": overrides.get("fallback_used", False),
            "provider_request_attempted": overrides.get("provider_request_attempted", False),
            "provider_request_success": overrides.get("provider_request_success", False),
            "requested_provider": overrides.get("requested_provider", ""),
            "requested_model": overrides.get("requested_model", ""),
            "actual_provider": overrides.get("actual_provider", ""),
            "actual_model": overrides.get("actual_model", ""),
            "provider_switch_count": overrides.get("provider_switch_count", 0),
            "provider_chain": overrides.get("provider_chain", ()),
            "provider_failure_reason": overrides.get("provider_failure_reason", ""),
            "provider_success": overrides.get("provider_success", False),
            "provider_name": overrides.get("provider_name", ""),
            "model_name": overrides.get("model_name", ""),
            "http_status": overrides.get("http_status", None),
            "response_object_type": overrides.get("response_object_type", ""),
            "response_content_present": overrides.get("response_content_present", False),
            "response_content_length": overrides.get("response_content_length", 0),
            "response_content_redacted": overrides.get("response_content_redacted", ""),
            "parser_input_present": overrides.get("parser_input_present", False),
            "parser_input_length": overrides.get("parser_input_length", 0),
            "parser_input_redacted": overrides.get("parser_input_redacted", ""),
            "parser_success": overrides.get("parser_success", False),
            "parser_action": overrides.get("parser_action", ""),
            "parser_failure_reason": overrides.get("parser_failure_reason", ""),
            "fallback_triggered": overrides.get("fallback_triggered", False),
            "fallback_reason": overrides.get("fallback_reason", ""),
            "exception_type": overrides.get("exception_type", ""),
            "exception_message_redacted": overrides.get("exception_message_redacted", ""),
            "latency_ms": overrides.get("latency_ms", 0.0),
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


def write_run_artifacts(run_id: str, records: list[dict], events: list[dict], metadata: dict) -> dict[str, Path]:
    paths = run_artifact_paths(run_id)
    paths["run_dir"].mkdir(parents=True, exist_ok=True)
    write_csv(paths["step_records"], records, FIELDNAMES)
    write_json(paths["run_metadata"], metadata)
    write_jsonl(paths["events"], events)
    return paths


def calculate_summary(records: list[dict], run_metadata: dict | None = None) -> dict:
    if not records:
        return {}

    total_rows = len(records)
    vehicles = sorted({r["vehicle_id"] for r in records if r.get("vehicle_id")})
    departed = run_metadata.get("departed_count") if run_metadata else None
    arrived = run_metadata.get("arrived_count") if run_metadata else None
    collisions = run_metadata.get("collision_count") if run_metadata else None
    overrides = sum(1 for r in records if r.get("safety_override"))
    tti_conflicts = sum(1 for r in records if r.get("conflict_detected"))
    speeds = [float(r.get("speed_after_action") or 0.0) for r in records]
    waits = [1 for r in records if float(r.get("speed_after_action") or 0.0) < float(CONFIG["stop_speed"])]

    proceed = sum(1 for r in records if r.get("final_decision") == "PROCEED")
    wait = sum(1 for r in records if r.get("final_decision") == "WAIT")
    free = sum(1 for r in records if r.get("final_decision") == "FREE")

    summary = {
        "vehicles_observed": len(vehicles),
        "departed": departed if departed is not None else sum(1 for r in records if r.get("departed")),
        "arrived": arrived if arrived is not None else sum(1 for r in records if r.get("arrived")),
        "throughput": arrived if arrived is not None else sum(1 for r in records if r.get("arrived")),
        "completion_rate": (arrived / departed) if departed else 0.0,
        "mean_speed": sum(speeds) / len(speeds),
        "mean_waiting_time": sum(waits) / len(vehicles) if vehicles else 0.0,
        "stopped_time_steps": len(waits),
        "stop_episode_count": len(waits),
        "collision_count": collisions if collisions is not None else sum(1 for r in records if r.get("collision")),
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
                "vehicle_count": run_metadata.get("vehicle_count", len(vehicles)),
                "seed": run_metadata.get("seed", 0),
            }
        )
    return summary
