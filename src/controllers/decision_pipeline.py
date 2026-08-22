from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Callable

from src.llm.postprocessor import apply_cooperative_postprocessing, apply_interface_rule
from src.llm.diagnostics import build_provider_diagnostics
from src.llm.provider_gate_diagnostics import build_live_provider_gate_diagnostics
from src.llm.request_config import build_live_request_kwargs, create_live_client
from src.llm.response_parser import parse_llm_response_details


VALID_DECISION_SOURCES = {
    "LLM_RAW",
    "DETERMINISTIC_INTERFACE_RULE",
    "COOPERATIVE_POSTPROCESSOR",
    "SAFETY_VERIFIER",
    "FALLBACK",
}


def run_live_llm_request(client, *, llm_model: str, prompt: str, request_context: dict | None = None):
    return client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        _request_context=request_context or {},
        **build_live_request_kwargs(),
    )


def normalize_action(action: object) -> str:
    if not isinstance(action, str):
        return "WAIT"
    action = action.strip().upper()
    return action if action in {"PROCEED", "WAIT", "FREE"} else "WAIT"


def build_decision_trace(
    vehicle_states: list[dict],
    llm_raw_decisions: dict[str, str],
    validated_llm_decisions: dict[str, str],
    llm_meta: dict | None = None,
) -> dict[str, dict]:
    llm_meta = llm_meta or {}
    trace: dict[str, dict] = {}
    for state in vehicle_states:
        vid = state["vehicle_id"]
        raw_action = llm_raw_decisions.get(vid, "MISSING")
        validated_action = validated_llm_decisions.get(vid, "WAIT")
        decision_source = llm_meta.get("decision_source", "LLM_RAW")
        if raw_action not in {"PROCEED", "WAIT", "FREE"}:
            decision_source = "FALLBACK"
        trace[vid] = {
            "vehicle_id": vid,
            "route_id": state.get("route_id", ""),
            "incoming_edge": state.get("incoming_edge", ""),
            "outgoing_edge": state.get("outgoing_edge", ""),
            "movement": state.get("movement", "UNKNOWN"),
            "inside_control_zone": bool(state.get("inside_control_zone", False)),
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
            "finish_reason": llm_meta.get("finish_reason", ""),
            "prompt_tokens": llm_meta.get("prompt_tokens", None),
            "completion_tokens": llm_meta.get("completion_tokens", None),
            "total_tokens": llm_meta.get("total_tokens", None),
            "reasoning_tokens": llm_meta.get("reasoning_tokens", None),
            "visible_completion_tokens": llm_meta.get("visible_completion_tokens", None),
            "json_parse_success": llm_meta.get("json_parse_success", False),
            "fallback_used": llm_meta.get("fallback_used", False),
            "provider_request_attempted": llm_meta.get("provider_request_attempted", False),
            "provider_request_success": llm_meta.get("provider_request_success", False),
            "provider_name": llm_meta.get("provider_name", ""),
            "model_name": llm_meta.get("model_name", ""),
            "request_id": llm_meta.get("request_id", ""),
            "request_simulation_step": llm_meta.get("request_simulation_step", None),
            "http_attempt_id": llm_meta.get("http_attempt_id", llm_meta.get("request_attempt_count", None)),
            "prompt_hash": llm_meta.get("prompt_hash", ""),
            "request_started_at": llm_meta.get("request_started_at", ""),
            "request_finished_at": llm_meta.get("request_finished_at", ""),
            "request_attempt_count": llm_meta.get("request_attempt_count", None),
            "requested_provider": llm_meta.get("requested_provider", ""),
            "requested_model": llm_meta.get("requested_model", ""),
            "actual_provider": llm_meta.get("actual_provider", ""),
            "actual_model": llm_meta.get("actual_model", ""),
            "provider_switch_count": llm_meta.get("provider_switch_count", 0),
            "provider_chain": llm_meta.get("provider_chain", ()),
            "provider_failure_reason": llm_meta.get("provider_failure_reason", ""),
            "provider_success": llm_meta.get("provider_success", False),
            "http_status": llm_meta.get("http_status", None),
            "response_object_type": llm_meta.get("response_object_type", ""),
            "response_content_present": llm_meta.get("response_content_present", False),
            "response_content_length": llm_meta.get("response_content_length", 0),
            "response_content_redacted": llm_meta.get("response_content_redacted", ""),
            "parser_input_present": llm_meta.get("parser_input_present", False),
            "parser_input_length": llm_meta.get("parser_input_length", 0),
            "parser_input_redacted": llm_meta.get("parser_input_redacted", ""),
            "parser_success": llm_meta.get("parser_success", False),
            "parser_action": llm_meta.get("parser_action", ""),
            "parser_failure_reason": llm_meta.get("parser_failure_reason", ""),
            "fallback_triggered": llm_meta.get("fallback_triggered", False),
            "fallback_reason": llm_meta.get("fallback_reason", ""),
            "llm_branch_entered": llm_meta.get("llm_branch_entered", False),
            "live_provider_gate_entered": llm_meta.get("live_provider_gate_entered", False),
            "live_provider_enabled": llm_meta.get("live_provider_enabled", False),
            "credential_available": llm_meta.get("credential_available", False),
            "live_client_constructed": llm_meta.get("live_client_constructed", False),
            "provider_call_function_entered": llm_meta.get("provider_call_function_entered", False),
            "provider_request_kwargs_built": llm_meta.get("provider_request_kwargs_built", False),
            "provider_request_skipped": llm_meta.get("provider_request_skipped", False),
            "provider_skip_reason": llm_meta.get("provider_skip_reason", ""),
            "fallback_trigger_reason": llm_meta.get("fallback_trigger_reason", ""),
            "exception_type": llm_meta.get("exception_type", ""),
            "exception_message_redacted": llm_meta.get("exception_message_redacted", ""),
            "latency_ms": llm_meta.get("latency_ms", llm_meta.get("llm_response_time_ms", 0.0)),
        }
    return trace


def apply_safety_filter(trace: dict[str, dict], vehicle_states: list[dict]) -> dict[str, dict]:
    from src.safety.safety_verifier import verify_decisions

    return _build_runtime_trace_from_guard(trace, vehicle_states, verify_decisions)


def execute_decision_pipeline(
    vehicle_states: list[dict],
    llm_raw_decisions: dict[str, str],
    *,
    stage_mode: str,
    llm_meta: dict | None = None,
    routes_compatible_fn: Callable[[str, str], bool] | None = None,
    postprocessor_fn: Callable[[dict[str, dict], list[dict]], dict[str, dict]] | None = None,
    safety_guard_fn: Callable[[dict[str, dict], list[dict]], dict[str, dict]] | None = None,
) -> dict[str, dict]:
    vehicle_ids = [state["vehicle_id"] for state in vehicle_states]
    validated_llm_decisions = {
        vid: normalize_action(llm_raw_decisions.get(vid, "MISSING"))
        for vid in vehicle_ids
    }
    trace = build_decision_trace(
        vehicle_states,
        llm_raw_decisions,
        validated_llm_decisions,
        llm_meta=llm_meta,
    )
    trace = apply_interface_rule(trace, vehicle_states, target_field="final_decision")

    if stage_mode not in {"raw", "hybrid", "hybrid_safety"}:
        raise ValueError(f"Unsupported stage mode: {stage_mode}")

    if stage_mode in {"hybrid", "hybrid_safety"} and postprocessor_fn is not None:
        trace = postprocessor_fn(trace, vehicle_states)
        for entry in trace.values():
            if not entry["outside_control_zone_rule_applied"]:
                entry["final_decision"] = entry["postprocessed_decision"]
                if entry["postprocess_applied"]:
                    entry["decision_source"] = "COOPERATIVE_POSTPROCESSOR"

    if stage_mode == "raw":
        for entry in trace.values():
            if not entry["outside_control_zone_rule_applied"]:
                entry["postprocessed_decision"] = entry["validated_llm_decision"]
                entry["final_decision"] = entry["validated_llm_decision"]
                entry["decision_source"] = "LLM_RAW" if entry["decision_source"] != "FALLBACK" else "FALLBACK"

    if stage_mode == "hybrid_safety" and safety_guard_fn is not None:
        trace = safety_guard_fn(trace, vehicle_states)

    return trace


def _build_runtime_trace_from_guard(
    trace: dict[str, dict],
    vehicle_states: list[dict],
    guard_fn: Callable[[list[dict], dict[str, str]], tuple[dict[str, str], dict[str, bool], dict[str, str], str]],
) -> dict[str, dict]:
    postprocessed = {vid: entry["postprocessed_decision"] for vid, entry in trace.items()}
    final_decisions, conflict_flags, conflict_types, priority_reason = guard_fn(vehicle_states, postprocessed)
    updated = {vid: dict(entry) for vid, entry in trace.items()}
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
    llm_client=None,
    prompt_version: str = "v2",
) -> None:
    from common import (
        CONFIG,
        resolve_llm_api_key,
        resolve_sumo_termination_reason,
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
    from src.llm.prompt_builder import build_structured_prompt

    llm_api_key = llm_api_key or resolve_llm_api_key()
    from src.safety.route_conflict import routes_compatible, validate_conflict_matrix
    from src.safety.route_semantics import describe_route_id
    from ttc_safety import verify_decisions

    try:
        import traci
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("traci is required to run SUMO controllers") from exc

    def build_traffic_state(vehicles: list[str]) -> list[dict]:
        state: list[dict] = []
        for vid in vehicles:
            route_id = get_vehicle_route(traci, vid)
            try:
                semantics = describe_route_id(route_id)
                incoming_edge = semantics.incoming_edge
                outgoing_edge = semantics.outgoing_edge
                movement = semantics.movement
            except ValueError:
                incoming_edge = ""
                outgoing_edge = ""
                movement = "UNKNOWN"
            state.append(
                {
                    "vehicle_id": vid,
                    "route_id": route_id,
                    "incoming_edge": incoming_edge,
                    "outgoing_edge": outgoing_edge,
                    "movement": movement,
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

    def build_real_llm_client():
        if llm_mode != "real":
            return None
        if llm_client is not None:
            return llm_client
        if not llm_api_key:
            return None
        return create_live_client(base_url=llm_base_url, api_key=llm_api_key)

    def run_live_llm_request(client, *, llm_model: str, prompt: str, request_context: dict | None = None):
        return client.chat.completions.create(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            _request_context=request_context or {},
            **build_live_request_kwargs(),
        )

    def llm_provider(traffic_state: list[dict], *, simulation_step: int) -> tuple[dict[str, str], dict]:
        prompt = build_structured_prompt(traffic_state, validate_conflict_matrix(), build_policy_hints(traffic_state))
        vehicle_ids = [v["vehicle_id"] for v in traffic_state]
        request_context = {
            "request_id": f"{run_id}_step{simulation_step:05d}",
            "request_simulation_step": simulation_step,
            "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest().upper(),
        }
        credential_available = bool(llm_api_key)
        openai_available = True
        client = build_real_llm_client()
        live_client_constructed = client is not None
        llm_branch_entered = True
        base_gate_meta = build_live_provider_gate_diagnostics(
            llm_mode=llm_mode,
            credential_available=credential_available,
            openai_available=openai_available,
            live_client_constructed=live_client_constructed,
            llm_branch_entered=llm_branch_entered,
            provider_call_function_entered=False,
            provider_request_kwargs_built=False,
            provider_request_attempted=False,
            provider_request_skipped=True,
            eligible_vehicle_count=len(vehicle_ids),
            decision_source="FALLBACK",
        )
        if llm_mode == "real" and client is not None:
            start_time = time.perf_counter()
            try:
                gate_meta = build_live_provider_gate_diagnostics(
                    llm_mode=llm_mode,
                    credential_available=True,
                    openai_available=openai_available,
                    live_client_constructed=True,
                    llm_branch_entered=True,
                    provider_call_function_entered=True,
                    provider_request_kwargs_built=True,
                    provider_request_attempted=True,
                    provider_request_skipped=False,
                    eligible_vehicle_count=len(vehicle_ids),
                    decision_source="LLM_RAW",
                )
                response = run_live_llm_request(client, llm_model=llm_model, prompt=prompt, request_context=request_context)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                response_text = ""
                if response is not None and getattr(response, "choices", None):
                    choice = response.choices[0]
                    message = getattr(choice, "message", None)
                    response_text = getattr(message, "content", "") or ""
                raw_decisions, validated_decisions, parse_ok = parse_llm_response_details(response_text, vehicle_ids)
                parse_actions = [validated_decisions.get(vid, "WAIT") for vid in vehicle_ids]
                first_action = parse_actions[0] if parse_actions else ""
                response_meta = build_provider_diagnostics(
                    provider_name="Groq",
                    model_name=llm_model,
                    response=response,
                    parser_input=response_text,
                    parser_success=parse_ok,
                    parser_action=first_action,
                    parser_failure_reason="" if parse_ok else "PARSER_FAILURE",
                    fallback_triggered=False,
                    fallback_reason="",
                    latency_ms=elapsed_ms,
                    provider_request_attempted=True,
                    provider_request_success=True,
                )
                meta = {
                    "llm_called": True,
                    "llm_branch_entered": True,
                    "llm_model": llm_model,
                    "llm_response_time_ms": round(elapsed_ms, 2),
                    "json_parse_success": parse_ok,
                    "fallback_used": False,
                    "llm_mode": llm_mode,
                    "decision_source": "LLM_RAW",
                    **gate_meta,
                    **response_meta,
                }
                if parse_ok:
                    meta["parser_failure_reason"] = ""
                else:
                    meta["parser_failure_reason"] = "PARSER_FAILURE"
                return raw_decisions, meta
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                raw = mock_llm_decision(traffic_state)
                exception_meta = build_provider_diagnostics(
                    provider_name="Groq",
                    model_name=llm_model,
                    parser_input="",
                    parser_success=False,
                    parser_action="",
                    parser_failure_reason="PROVIDER_REQUEST_EXCEPTION",
                    fallback_triggered=True,
                    fallback_reason="PROVIDER_REQUEST_EXCEPTION",
                    exception=exc,
                    latency_ms=elapsed_ms,
                    provider_request_attempted=True,
                    provider_request_success=False,
                )
                gate_meta = build_live_provider_gate_diagnostics(
                    llm_mode=llm_mode,
                    credential_available=True,
                    openai_available=openai_available,
                    live_client_constructed=True,
                    llm_branch_entered=True,
                    provider_call_function_entered=True,
                    provider_request_kwargs_built=True,
                    provider_request_attempted=True,
                    provider_request_skipped=False,
                    eligible_vehicle_count=len(vehicle_ids),
                    fallback_trigger_reason="PROVIDER_REQUEST_EXCEPTION",
                    decision_source="FALLBACK",
                )
                return raw, {
                    "llm_called": True,
                    "llm_branch_entered": True,
                    "llm_model": llm_model,
                    "llm_response_time_ms": round(elapsed_ms, 2),
                    "json_parse_success": False,
                    "fallback_used": True,
                    "llm_mode": llm_mode,
                    "decision_source": "FALLBACK",
                    **gate_meta,
                    **exception_meta,
                }

        raw = mock_llm_decision(traffic_state)
        fallback_meta = build_provider_diagnostics(
            provider_name="Groq" if llm_mode == "real" else "mock",
            model_name=llm_model if llm_mode == "real" else "",
            parser_input="",
            parser_success=True,
            parser_action="",
            parser_failure_reason="",
            fallback_triggered=False,
            fallback_reason=base_gate_meta["fallback_trigger_reason"],
            latency_ms=0.0,
            provider_request_attempted=False,
            provider_request_success=False,
        )
        return raw, {
            "llm_called": True,
            "llm_branch_entered": True,
            "llm_model": llm_model if llm_mode == "real" else "",
            "llm_response_time_ms": 0.0,
            "json_parse_success": True,
            "fallback_used": True,
            "llm_mode": llm_mode,
            "decision_source": "FALLBACK",
            **base_gate_meta,
            **fallback_meta,
        }

    def safety_guard(trace: dict[str, dict], vehicle_states: list[dict]) -> dict[str, dict]:
        vehicles = [state["vehicle_id"] for state in vehicle_states]

        def guard_fn(states: list[dict], raw_decisions: dict[str, str]):
            return verify_decisions(traci, vehicles, raw_decisions)

        return _build_runtime_trace_from_guard(trace, vehicle_states, guard_fn)

    client = build_real_llm_client()
    run_suffix = os.getenv("RUN_SUFFIX", "")
    run_id = f"{experiment_id}_v{vehicle_count}_seed{seed}{run_suffix}_{llm_mode}"
    artifacts = run_artifact_paths(run_id)
    output_csv = artifacts["step_records"]
    records = []
    events = []
    all_seen_vehicles = set()
    departed_seen = set()
    arrived_seen = set()
    cached_trace: dict[str, dict] = {}
    cached_llm_meta = {
        "llm_called": False,
        "llm_branch_entered": False,
        "live_provider_gate_entered": False,
        "live_provider_enabled": False,
        "credential_available": False,
        "live_client_constructed": False,
        "provider_call_function_entered": False,
        "provider_request_kwargs_built": False,
        "provider_request_attempted": False,
        "provider_request_skipped": False,
        "provider_skip_reason": "",
        "fallback_trigger_reason": "",
        "llm_model": "",
        "llm_response_time_ms": 0.0,
        "json_parse_success": True,
        "fallback_used": False,
        "llm_mode": llm_mode,
        "decision_source": "FALLBACK",
        "provider_request_attempted": False,
        "provider_request_success": False,
        "provider_name": "",
        "model_name": "",
        "http_status": None,
        "response_object_type": "",
        "response_content_present": False,
        "response_content_length": 0,
        "response_content_redacted": "",
        "parser_input_present": False,
        "parser_input_length": 0,
        "parser_input_redacted": "",
        "parser_success": False,
        "parser_action": "",
        "parser_failure_reason": "",
        "fallback_triggered": False,
        "fallback_reason": "",
        "exception_type": "",
        "exception_message_redacted": "",
        "latency_ms": 0.0,
    }

    traci_started = False
    try:
        traci.start([str(sumo_binary), "-c", str(sumo_config), "--start"])
        traci_started = True

        step = 0
        termination_reason = "UNEXPECTED_SUMO_TERMINATION"
        while step < simulation_steps:
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

            if step % llm_decision_interval == 0 or not cached_trace:
                raw_decisions, llm_meta = llm_provider(traffic_state, simulation_step=step)
                cached_trace = execute_decision_pipeline(
                    traffic_state,
                    raw_decisions,
                    stage_mode=stage_mode,
                    llm_meta=llm_meta,
                    routes_compatible_fn=routes_compatible,
                    postprocessor_fn=lambda trace, states: apply_cooperative_postprocessing(
                        trace,
                        states,
                        routes_compatible_fn=routes_compatible,
                    ),
                    safety_guard_fn=safety_guard if stage_mode == "hybrid_safety" else None,
                )
                cached_llm_meta = dict(llm_meta)
            else:
                llm_meta = dict(cached_llm_meta)

            trace = dict(cached_trace)

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
                        request_id=entry.get("request_id", ""),
                        request_simulation_step=entry.get("request_simulation_step", None),
                        http_attempt_id=entry.get("http_attempt_id", None),
                        prompt_hash=entry.get("prompt_hash", ""),
                        request_started_at=entry.get("request_started_at", ""),
                        request_finished_at=entry.get("request_finished_at", ""),
                        request_attempt_count=entry.get("request_attempt_count", None),
                        llm_branch_entered=entry.get("llm_branch_entered", False),
                        live_provider_gate_entered=entry.get("live_provider_gate_entered", False),
                        live_provider_enabled=entry.get("live_provider_enabled", False),
                        credential_available=entry.get("credential_available", False),
                        live_client_constructed=entry.get("live_client_constructed", False),
                        provider_call_function_entered=entry.get("provider_call_function_entered", False),
                        provider_request_kwargs_built=entry.get("provider_request_kwargs_built", False),
                        provider_request_skipped=entry.get("provider_request_skipped", False),
                        provider_skip_reason=entry.get("provider_skip_reason", ""),
                        fallback_trigger_reason=entry.get("fallback_trigger_reason", ""),
                        llm_model=entry["llm_model"],
                        llm_response_time_ms=entry["llm_response_time_ms"],
                        finish_reason=entry.get("finish_reason", ""),
                        prompt_tokens=entry.get("prompt_tokens", None),
                        completion_tokens=entry.get("completion_tokens", None),
                        total_tokens=entry.get("total_tokens", None),
                        reasoning_tokens=entry.get("reasoning_tokens", None),
                        visible_completion_tokens=entry.get("visible_completion_tokens", None),
                        json_parse_success=entry["json_parse_success"],
                        fallback_used=entry["fallback_used"],
                        provider_request_attempted=entry["provider_request_attempted"],
                        provider_request_success=entry["provider_request_success"],
                        requested_provider=entry.get("requested_provider", ""),
                        requested_model=entry.get("requested_model", ""),
                        actual_provider=entry.get("actual_provider", ""),
                        actual_model=entry.get("actual_model", ""),
                        provider_switch_count=entry.get("provider_switch_count", 0),
                        provider_chain=entry.get("provider_chain", ()),
                        provider_failure_reason=entry.get("provider_failure_reason", ""),
                        provider_success=entry.get("provider_success", False),
                        provider_name=entry["provider_name"],
                        model_name=entry["model_name"],
                        http_status=entry["http_status"],
                        response_object_type=entry["response_object_type"],
                        response_content_present=entry["response_content_present"],
                        response_content_length=entry["response_content_length"],
                        response_content_redacted=entry["response_content_redacted"],
                        parser_input_present=entry["parser_input_present"],
                        parser_input_length=entry["parser_input_length"],
                        parser_input_redacted=entry["parser_input_redacted"],
                        parser_success=entry["parser_success"],
                        parser_action=entry["parser_action"],
                        parser_failure_reason=entry["parser_failure_reason"],
                        fallback_triggered=entry["fallback_triggered"],
                        fallback_reason=entry["fallback_reason"],
                        exception_type=entry["exception_type"],
                        exception_message_redacted=entry["exception_message_redacted"],
                        latency_ms=entry["latency_ms"],
                        departed=vid in departed_seen,
                        arrived=False,
                    )
                )
            termination_reason = resolve_sumo_termination_reason(
                simulation_step=step,
                simulation_steps=simulation_steps,
                expected_remaining=int(traci.simulation.getMinExpectedNumber()),
                arrived_count=len(arrived_seen),
                target_vehicle_count=vehicle_count,
            )
            if termination_reason:
                break
            step += 1
            time.sleep(0.03)
    finally:
        if traci_started:
            try:
                traci.close(False)
            except Exception:  # pragma: no cover
                pass

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
        termination_reason=termination_reason,
    )
    metadata["departed_count"] = len(departed_seen)
    metadata["arrived_count"] = len(arrived_seen)
    metadata["collision_count"] = 0
    write_run_artifacts(run_id, records, events, metadata)
    summary = calculate_summary(records, all_seen_vehicles, run_metadata=metadata)
    print_summary(controller_name, summary, output_csv)
