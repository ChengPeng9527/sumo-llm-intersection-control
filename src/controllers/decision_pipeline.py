from __future__ import annotations

import json
import time
from pathlib import Path

import traci

from common import (
    CONFIG,
    apply_decision,
    build_event,
    build_run_metadata,
    calculate_summary,
    create_record,
    distance_to_center,
    estimate_time_to_intersection,
    get_vehicle_route,
    is_in_control_zone,
    print_summary,
    run_artifact_paths,
    write_run_artifacts,
)
from src.llm.fallback_policy import mock_llm_decision
from src.llm.postprocessor import apply_cooperative_postprocessing, apply_interface_rule
from src.llm.prompt_builder import build_structured_prompt
from src.llm.response_parser import parse_llm_response_details
from src.safety.route_conflict import routes_compatible, validate_conflict_matrix
from ttc_safety import verify_decisions

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


def build_traffic_state(vehicles: list[str]) -> list[dict]:
    state: list[dict] = []
    for vid in vehicles:
        state.append(
            {
                "vehicle_id": vid,
                "route_id": get_vehicle_route(traci, vid),
                "speed": round(traci.vehicle.getSpeed(vid), 2),
                "distance_to_intersection": round(distance_to_center(traci, vid), 2),
                "time_to_intersection": round(estimate_time_to_intersection(traci, vid), 2),
                "inside_control_zone": is_in_control_zone(traci, vid),
            }
        )
    return state


def build_policy_hints(traffic_state: list[dict]) -> dict:
    controlled = [state for state in traffic_state if state.get("inside_control_zone")]
    priority_route = ""
    priority_vehicle_id = ""
    compatible_routes: list[str] = []
    if controlled:
        priority_vehicle = min(controlled, key=lambda state: state.get("time_to_intersection", float("inf")))
        priority_route = priority_vehicle.get("route_id", "")
        priority_vehicle_id = priority_vehicle["vehicle_id"]
        compatible_routes = [
            state.get("route_id", "")
            for state in controlled
            if priority_route and routes_compatible(priority_route, state.get("route_id", ""))
        ]
    return {
        "priority_vehicle_id": priority_vehicle_id,
        "priority_route_id": priority_route,
        "controlled_vehicle_count": len(controlled),
        "compatible_routes_with_priority": compatible_routes,
    }


def build_decision_trace(
    traffic_state: list[dict],
    llm_raw_decisions: dict[str, str],
    validated_llm_decisions: dict[str, str],
    llm_meta: dict,
) -> dict[str, dict]:
    trace: dict[str, dict] = {}
    for state in traffic_state:
        vid = state["vehicle_id"]
        raw_action = llm_raw_decisions.get(vid, "MISSING")
        validated_action = validated_llm_decisions.get(vid, "WAIT")
        decision_source = "LLM_RAW" if raw_action in {"PROCEED", "WAIT", "FREE"} else "FALLBACK"
        trace[vid] = {
            "llm_raw_decision": raw_action,
            "validated_llm_decision": validated_action,
            "postprocessed_decision": validated_action,
            "final_decision": validated_action,
            "outside_control_zone_rule_applied": False,
            "postprocess_applied": False,
            "postprocess_reason": "",
            "safety_override": False,
            "safety_reason": "",
            "decision_source": decision_source,
            "conflict_detected": False,
            "conflict_type": "",
            "priority_reason": "",
            "llm_called": llm_meta.get("llm_called", False),
            "llm_mode": llm_meta.get("llm_mode", "mock"),
            "llm_model": llm_meta.get("llm_model", ""),
            "llm_response_time_ms": llm_meta.get("llm_response_time_ms", 0.0),
            "json_parse_success": llm_meta.get("json_parse_success", False),
            "fallback_used": llm_meta.get("fallback_used", False),
        }
        base_source = llm_meta.get("decision_source", "FALLBACK")
        if raw_action not in {"PROCEED", "WAIT", "FREE"}:
            base_source = "FALLBACK"
        trace[vid]["decision_source"] = base_source
    return trace


def apply_safety_filter(trace: dict[str, dict], vehicle_states: list[dict]) -> dict[str, dict]:
    updated = {vid: dict(entry) for vid, entry in trace.items()}
    postprocessed = {vid: entry["postprocessed_decision"] for vid, entry in updated.items()}
    final_decisions, conflict_flags, conflict_types, priority_reason = verify_decisions(vehicle_states, postprocessed)
    for state in vehicle_states:
        vid = state["vehicle_id"]
        updated[vid]["final_decision"] = final_decisions.get(vid, updated[vid]["postprocessed_decision"])
        updated[vid]["conflict_detected"] = conflict_flags.get(vid, False)
        updated[vid]["conflict_type"] = conflict_types.get(vid, "")
        updated[vid]["priority_reason"] = priority_reason
        if updated[vid]["final_decision"] != updated[vid]["postprocessed_decision"]:
            updated[vid]["safety_override"] = True
            updated[vid]["safety_reason"] = conflict_types.get(vid, "") or priority_reason or "safety_downgrade"
            updated[vid]["decision_source"] = "SAFETY_VERIFIER"
        else:
            updated[vid]["safety_override"] = False
            updated[vid]["safety_reason"] = ""
    return updated


def build_real_llm_client(llm_mode: str, api_key: str, base_url: str):
    if llm_mode != "real":
        return None
    if not api_key or OpenAI is None:
        return None
    return OpenAI(base_url=base_url, api_key=api_key)


def get_llm_response_text(
    *,
    llm_mode: str,
    llm_model: str,
    client,
    prompt: str,
    traffic_state: list[dict],
) -> tuple[str, dict]:
    if llm_mode == "real" and client is not None:
        start_time = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[{"role": "user", "content": prompt}],
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return (
                response.choices[0].message.content or "",
                {
                    "llm_called": True,
                    "llm_model": llm_model,
                    "llm_response_time_ms": round(elapsed_ms, 2),
                    "json_parse_success": True,
                    "fallback_used": False,
                    "llm_mode": llm_mode,
                    "decision_source": "LLM_RAW",
                },
            )
        except Exception:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            fallback_response = json.dumps({"decisions": mock_llm_decision(traffic_state)})
            return (
                fallback_response,
                {
                    "llm_called": True,
                    "llm_model": llm_model,
                    "llm_response_time_ms": round(elapsed_ms, 2),
                    "json_parse_success": False,
                    "fallback_used": True,
                    "llm_mode": llm_mode,
                    "decision_source": "FALLBACK",
                },
            )

    fallback_response = json.dumps({"decisions": mock_llm_decision(traffic_state)})
    return (
        fallback_response,
        {
            "llm_called": False,
            "llm_model": llm_model if llm_mode == "real" else "",
            "llm_response_time_ms": 0.0,
            "json_parse_success": True,
            "fallback_used": False,
            "llm_mode": llm_mode,
            "decision_source": "FALLBACK",
        },
    )


def run_pipeline_controller(
    *,
    experiment_id: str,
    controller_name: str,
    stage_mode: str,
    scenario: str,
    vehicle_count: int,
    seed: int,
    sumo_binary: Path,
    sumo_config: Path,
    simulation_steps: int,
    llm_mode: str,
    llm_decision_interval: int,
    llm_model: str,
    llm_base_url: str,
    llm_api_key: str,
    prompt_version: str = "v2",
) -> None:
    if stage_mode not in {"raw", "hybrid", "hybrid_safety"}:
        raise ValueError(f"Unsupported stage mode: {stage_mode}")

    client = build_real_llm_client(llm_mode, llm_api_key, llm_base_url)
    run_id = f"{experiment_id}_v{vehicle_count}_seed{seed}_{llm_mode}"
    artifacts = run_artifact_paths(run_id)
    output_csv = artifacts["step_records"]

    traci.start([str(sumo_binary), "-c", str(sumo_config), "--start"])
    records = []
    events = []
    all_seen_vehicles = set()
    departed_seen = set()
    arrived_seen = set()
    cached_llm_raw: dict[str, str] = {}
    cached_validated: dict[str, str] = {}
    cached_llm_meta = {
        "llm_called": False,
        "llm_model": "",
        "llm_response_time_ms": 0.0,
        "json_parse_success": True,
        "fallback_used": False,
        "llm_mode": llm_mode,
        "decision_source": "FALLBACK",
    }

    for step in range(simulation_steps):
        traci.simulationStep()
        departed_ids = list(traci.simulation.getDepartedIDList())
        arrived_ids = list(traci.simulation.getArrivedIDList())
        simulation_time = step * CONFIG["simulation_step_length"]
        for vid in departed_ids:
            if vid not in departed_seen:
                departed_seen.add(vid)
                events.append(
                    build_event(
                        run_id=run_id,
                        event_type="departed",
                        simulation_step=step,
                        simulation_time_seconds=simulation_time,
                        vehicle_id=vid,
                        details="vehicle entered the simulation",
                    )
                )
        for vid in arrived_ids:
            if vid not in arrived_seen:
                arrived_seen.add(vid)
                events.append(
                    build_event(
                        run_id=run_id,
                        event_type="arrived",
                        simulation_step=step,
                        simulation_time_seconds=simulation_time,
                        vehicle_id=vid,
                        details="vehicle left the simulation",
                    )
                )
        vehicles = list(traci.vehicle.getIDList())
        all_seen_vehicles.update(vehicles)
        traffic_state = build_traffic_state(vehicles)

        if step % llm_decision_interval == 0 or not cached_llm_raw:
            prompt = build_structured_prompt(traffic_state, validate_conflict_matrix(), build_policy_hints(traffic_state))
            response_text, llm_meta = get_llm_response_text(
                llm_mode=llm_mode,
                llm_model=llm_model,
                client=client,
                prompt=prompt,
                traffic_state=traffic_state,
            )
            raw_decisions, validated_decisions, parse_ok = parse_llm_response_details(response_text, vehicles)
            llm_meta["json_parse_success"] = parse_ok if llm_mode == "real" else True
            cached_llm_raw = dict(raw_decisions)
            cached_validated = dict(validated_decisions)
            cached_llm_meta = dict(llm_meta)
        else:
            raw_decisions = dict(cached_llm_raw)
            validated_decisions = dict(cached_validated)
            llm_meta = {
                "llm_called": False,
                "llm_model": cached_llm_meta.get("llm_model", ""),
                "llm_response_time_ms": 0.0,
                "json_parse_success": cached_llm_meta.get("json_parse_success", True),
                "fallback_used": cached_llm_meta.get("fallback_used", False),
                "llm_mode": llm_mode,
                "decision_source": cached_llm_meta.get("decision_source", "FALLBACK"),
            }

        trace = build_decision_trace(traffic_state, raw_decisions, validated_decisions, llm_meta)

        if stage_mode == "raw":
            trace = apply_interface_rule(trace, traffic_state, target_field="final_decision")
            for entry in trace.values():
                entry["postprocessed_decision"] = entry["validated_llm_decision"]
                entry["final_decision"] = entry["final_decision"] if entry["final_decision"] else entry["validated_llm_decision"]
        else:
            trace = apply_interface_rule(trace, traffic_state, target_field="postprocessed_decision")
            trace = apply_cooperative_postprocessing(trace, traffic_state)
            for entry in trace.values():
                entry["final_decision"] = entry["postprocessed_decision"]
            if stage_mode == "hybrid_safety":
                trace = apply_safety_filter(trace, traffic_state)
            else:
                for entry in trace.values():
                    entry["safety_override"] = False
                    entry["safety_reason"] = ""

        for vid in vehicles:
            entry = trace[vid]
            apply_decision(traci, vid, entry["final_decision"])
            records.append(
                create_record(
                    experiment_id=experiment_id,
                    controller=controller_name,
                    scenario=scenario,
                    seed=seed,
                    step=step,
                    traci=traci,
                    veh_id=vid,
                    raw_decision=entry["validated_llm_decision"],
                    final_decision=entry["final_decision"],
                    conflict=entry["conflict_detected"],
                    conflict_type=entry["conflict_type"],
                    priority_reason=entry["priority_reason"],
                    run_id=run_id,
                    safety_enabled=stage_mode == "hybrid_safety",
                    simulation_time_seconds=simulation_time,
                    vehicle_count=vehicle_count,
                    llm_raw_decision=entry["llm_raw_decision"],
                    validated_llm_decision=entry["validated_llm_decision"],
                    postprocessed_decision=entry["postprocessed_decision"],
                    outside_control_zone_rule_applied=entry["outside_control_zone_rule_applied"],
                    postprocess_applied=entry["postprocess_applied"],
                    postprocess_reason=entry["postprocess_reason"],
                    safety_override=entry["safety_override"],
                    safety_reason=entry["safety_reason"],
                    decision_source=entry["decision_source"],
                    llm_mode=entry["llm_mode"],
                    llm_called=entry["llm_called"],
                    llm_model=entry["llm_model"],
                    llm_response_time_ms=entry["llm_response_time_ms"],
                    json_parse_success=entry["json_parse_success"],
                    fallback_used=entry["fallback_used"],
                    departed=vid in departed_seen,
                    arrived=False,
                )
            )
        time.sleep(0.03)

    traci.close(False)
    metadata = build_run_metadata(
        run_id=run_id,
        controller=controller_name,
        safety_enabled=stage_mode == "hybrid_safety",
        scenario_id=scenario,
        density="debug",
        vehicle_count=vehicle_count,
        seed=seed,
        llm_mode=llm_mode,
        llm_model=llm_model if llm_mode == "real" else "",
        prompt_version=prompt_version,
        status="completed",
    )
    metadata["departed_count"] = len(departed_seen)
    metadata["arrived_count"] = len(arrived_seen)
    metadata["collision_count"] = 0
    write_run_artifacts(run_id, records, events, metadata)
    summary = calculate_summary(records, all_seen_vehicles, run_metadata=metadata)
    print_summary(controller_name, summary, output_csv)
