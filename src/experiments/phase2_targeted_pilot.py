from __future__ import annotations

import math
from statistics import fmean

from common import distance_to_center, estimate_time_to_intersection, get_vehicle_route, is_in_control_zone
from src.common.config import load_project_config
from src.controllers.decision_pipeline import (
    execute_cooperative_comparator_pipeline,
    execute_llm_candidate_selector_pipeline,
)
from src.experiments.scenario_generator import generate_targeted_scenario
from src.llm.candidate_selector import build_candidate_selection_context, run_live_candidate_request
from src.llm.request_config import PHASE2_MODEL, PHASE2_PROVIDER_NAME, create_phase2_live_client
from src.safety.candidate_groups import build_safe_candidate_groups
from src.safety.route_semantics import describe_route_id


PRIMARY_SCENARIOS = (
    "S1_BALANCED_MIXED_TURN",
    "S2_SIMULTANEOUS_CONFLICT",
    "S3_COOPERATIVE_OPPORTUNITY",
    "S4_FAIRNESS_PRESSURE",
)
TARGETED_SCALE_VALIDATIONS = (
    ("S3_COOPERATIVE_OPPORTUNITY", 12),
    ("S4_FAIRNESS_PRESSURE", 16),
)


def _finite(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _vehicle_states(traci) -> list[dict]:
    states: list[dict] = []
    for vehicle_id in sorted(traci.vehicle.getIDList()):
        route_id = get_vehicle_route(traci, vehicle_id)
        semantics = describe_route_id(route_id)
        speed = round(float(traci.vehicle.getSpeed(vehicle_id)), 2)
        distance = round(float(distance_to_center(traci, vehicle_id)), 2)
        states.append(
            {
                "vehicle_id": vehicle_id,
                "route_id": route_id,
                "incoming_edge": semantics.incoming_edge,
                "outgoing_edge": semantics.outgoing_edge,
                "movement": semantics.movement,
                "speed": speed,
                "distance_to_intersection": distance,
                "time_to_intersection": round(float(estimate_time_to_intersection(traci, vehicle_id)), 2),
                "waiting_time": round(float(traci.vehicle.getWaitingTime(vehicle_id)), 2),
                "inside_control_zone": is_in_control_zone(traci, vehicle_id),
            }
        )
    return states


def build_candidate_observation(
    *,
    scenario_class: str,
    simulation_step: int,
    vehicle_states: list[dict],
    candidate_groups: list[list[str]],
    trace: dict[str, dict],
    fairness_target_route: str = "",
    intended_waiting_pressure_seconds: float = 0.0,
) -> dict:
    controlled_states = [state for state in vehicle_states if state.get("inside_control_zone")]
    entry = next((trace[state["vehicle_id"]] for state in controlled_states), {})
    selected_ids = set(entry.get("selected_vehicle_ids", ()))
    group_sizes = [len(group) for group in candidate_groups]
    selected_waits = [float(state.get("waiting_time", 0.0)) for state in controlled_states if state["vehicle_id"] in selected_ids]
    unselected_waits = [float(state.get("waiting_time", 0.0)) for state in controlled_states if state["vehicle_id"] not in selected_ids]
    target_waits = [
        float(state.get("waiting_time", 0.0))
        for state in controlled_states
        if state.get("route_id") == fairness_target_route and state["vehicle_id"] not in selected_ids
    ]
    finite_ttis = [value for state in controlled_states if (value := _finite(state.get("time_to_intersection"))) is not None]
    eta_simultaneity_available = len(finite_ttis) >= 2
    target_wait = max(target_waits, default=0.0)
    fairness_pressure = bool(
        target_waits
        and target_wait >= float(intended_waiting_pressure_seconds)
        and len(selected_ids) > 1
    )
    return {
        "scenario_class": scenario_class,
        "simulation_step": simulation_step,
        "controlled_vehicle_count": len(controlled_states),
        "candidate_count": len(candidate_groups),
        "candidate_group_sizes": group_sizes,
        "mean_candidate_group_size": fmean(group_sizes) if group_sizes else 0.0,
        "maximum_compatible_group_size": max(group_sizes, default=0),
        "has_multiple_candidates": len(candidate_groups) > 1,
        "has_multi_vehicle_candidate": any(size > 1 for size in group_sizes),
        "movement_diversity": len({state.get("movement") for state in controlled_states}),
        "arrival_tti_spread": max(finite_ttis) - min(finite_ttis) if eta_simultaneity_available else None,
        "eta_simultaneity_available": eta_simultaneity_available,
        "finite_tti_count": len(finite_ttis),
        "maximum_waiting_time": max((float(state.get("waiting_time", 0.0)) for state in controlled_states), default=0.0),
        "maximum_selected_waiting_time": max(selected_waits, default=0.0),
        "maximum_unselected_waiting_time": max(unselected_waits, default=0.0),
        "fairness_target_waiting_time": target_wait,
        "fairness_pressure_present": fairness_pressure,
        "deterministic_candidate_id": entry.get("deterministic_candidate_id", ""),
        "selected_vehicle_ids": list(entry.get("selected_vehicle_ids", ())),
        "safety_intervention_count": sum(bool(item.get("safety_intervened") or item.get("safety_override")) for item in trace.values()),
        "candidate_groups": [list(group) for group in candidate_groups],
        "vehicle_states": [dict(state) for state in vehicle_states],
    }


def _representative_score(observation: dict) -> tuple[float, ...]:
    scenario_class = observation["scenario_class"]
    if scenario_class == "S2_SIMULTANEOUS_CONFLICT":
        eta_available = bool(observation.get("eta_simultaneity_available"))
        tti_spread = observation.get("arrival_tti_spread")
        return (
            float(observation["has_multiple_candidates"]),
            float(eta_available),
            -float(tti_spread) if eta_available and tti_spread is not None else 0.0,
            float(observation["candidate_count"]),
        )
    if scenario_class == "S3_COOPERATIVE_OPPORTUNITY":
        return (
            float(observation["maximum_compatible_group_size"]),
            float(observation["candidate_count"]),
            float(observation["movement_diversity"]),
        )
    if scenario_class == "S4_FAIRNESS_PRESSURE":
        return (
            float(observation["fairness_pressure_present"]),
            float(observation["fairness_target_waiting_time"]),
            float(observation["maximum_compatible_group_size"]),
        )
    return (
        float(observation["movement_diversity"]),
        float(observation["candidate_count"]),
        float(observation["maximum_compatible_group_size"]),
    )


def summarize_candidate_observations(observations: list[dict]) -> dict:
    candidate_decisions = len(observations)
    multiple = sum(bool(item.get("has_multiple_candidates")) for item in observations)
    cooperative = sum(bool(item.get("has_multi_vehicle_candidate")) for item in observations)
    candidate_counts = [int(item.get("candidate_count", 0)) for item in observations]
    all_group_sizes = [
        int(size)
        for item in observations
        for size in item.get("candidate_group_sizes", [])
    ]
    richness_ratio = multiple / candidate_decisions if candidate_decisions else 0.0
    cooperative_ratio = cooperative / candidate_decisions if candidate_decisions else 0.0
    max_group_size = max(all_group_sizes, default=0)
    if richness_ratio >= 0.8 and cooperative_ratio >= 0.5 and max_group_size >= 3:
        richness_label = "HIGH"
    elif richness_ratio >= 0.5 and cooperative_ratio > 0.0 and max(candidate_counts, default=0) > 1:
        richness_label = "MEDIUM"
    else:
        richness_label = "LOW"
    return {
        "controlled_decisions": candidate_decisions,
        "candidate_sets": candidate_decisions,
        "candidate_sets_with_multiple_legal_candidates": multiple,
        "candidate_sets_with_multi_vehicle_candidates": cooperative,
        "maximum_candidate_count": max(candidate_counts, default=0),
        "mean_candidate_count": fmean(candidate_counts) if candidate_counts else 0.0,
        "mean_candidate_group_size": fmean(all_group_sizes) if all_group_sizes else 0.0,
        "maximum_compatible_group_size": max_group_size,
        "candidate_richness_ratio": richness_ratio,
        "cooperative_opportunity_ratio": cooperative_ratio,
        "fairness_pressure_decisions": sum(bool(item.get("fairness_pressure_present")) for item in observations),
        "safety_intervention_count": sum(int(item.get("safety_intervention_count", 0)) for item in observations),
        "richness_label": richness_label,
    }


def run_deterministic_sumo_pilot(
    scenario_class: str,
    *,
    vehicle_count: int,
    seed: int,
) -> dict:
    try:
        import traci
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("traci is required for the Step 7 SUMO pilot") from exc

    scenario_id = f"step7_{scenario_class.lower()}_v{vehicle_count}_seed{seed}"
    generation = generate_targeted_scenario(scenario_id, scenario_class, seed, vehicle_count)
    project = load_project_config()
    command = [
        str(project["sumo_binary_path"]),
        "-c",
        generation["sumocfg_path"],
        "--seed",
        str(seed),
        "--no-step-log",
        "true",
        "--no-warnings",
        "true",
    ]
    observations: list[dict] = []
    representative: dict | None = None
    departed_count = 0
    arrived_count = 0
    collision_count = 0
    traci_started = False
    try:
        traci.start(command)
        traci_started = True
        for simulation_step in range(int(generation["simulation_duration_seconds"])):
            traci.simulationStep()
            departed_count += len(traci.simulation.getDepartedIDList())
            arrived_count += len(traci.simulation.getArrivedIDList())
            try:
                collision_count += int(traci.simulation.getCollidingVehiclesNumber())
            except Exception:
                pass

            states = _vehicle_states(traci)
            candidate_groups = build_safe_candidate_groups(states)
            if candidate_groups:
                trace = execute_cooperative_comparator_pipeline(states, candidate_groups)
                observation = build_candidate_observation(
                    scenario_class=scenario_class,
                    simulation_step=simulation_step,
                    vehicle_states=states,
                    candidate_groups=candidate_groups,
                    trace=trace,
                    fairness_target_route=generation.get("fairness_target_route", ""),
                    intended_waiting_pressure_seconds=generation.get("intended_waiting_pressure_seconds", 0),
                )
                observations.append(observation)
                if representative is None or _representative_score(observation) > _representative_score(representative):
                    representative = observation

            if traci.simulation.getMinExpectedNumber() <= 0:
                break
    finally:
        if traci_started:
            traci.close(False)

    summary = summarize_candidate_observations(observations)
    summary.update(
        {
            "scenario_class": scenario_class,
            "scenario_id": scenario_id,
            "vehicle_count": vehicle_count,
            "seed": seed,
            "departed_count": departed_count,
            "arrived_count": arrived_count,
            "collision_count": collision_count,
            "pilot_execution_mode": "SUMO_OBSERVER_NATIVE_SIGNAL",
            "route_sequence": generation["route_sequence"],
            "departure_times": generation["departure_times"],
            "movement_sequence": generation["movement_sequence"],
            "departure_cluster_span_seconds": (
                max(generation["departure_times"]) - min(generation["departure_times"])
                if generation["departure_times"]
                else 0
            ),
            "seed_semantics": generation.get("seed_semantics", {}),
            "initial_demand_signature": generation.get("initial_demand_signature", ""),
        }
    )
    return {
        "summary": summary,
        "representative_observation": representative or {},
    }


def run_deterministic_suite(*, seed: int = 7) -> list[dict]:
    runs = [run_deterministic_sumo_pilot(name, vehicle_count=8, seed=seed) for name in PRIMARY_SCENARIOS]
    runs.extend(
        run_deterministic_sumo_pilot(name, vehicle_count=vehicle_count, seed=seed)
        for name, vehicle_count in TARGETED_SCALE_VALIDATIONS
    )
    return runs


def run_live_representative_pilot(deterministic_runs: list[dict], *, api_key: str) -> list[dict]:
    client = create_phase2_live_client(api_key=api_key)
    live_results: list[dict] = []
    repeated_failure_reason = ""
    repeated_failure_count = 0
    for run in deterministic_runs:
        summary = run["summary"]
        if summary["vehicle_count"] != 8:
            continue
        representative = run["representative_observation"]
        vehicle_states = representative.get("vehicle_states", [])
        candidate_groups = representative.get("candidate_groups", [])
        if not vehicle_states or not candidate_groups:
            raise RuntimeError(f"No representative candidate state for {summary['scenario_class']}")
        _, candidate_features, _ = build_candidate_selection_context(vehicle_states, candidate_groups)
        candidate_ids = [feature["candidate_id"] for feature in candidate_features]
        request_id = f"step7-{summary['scenario_class'].lower()}-v8-seed{summary['seed']}"
        trace = execute_llm_candidate_selector_pipeline(
            vehicle_states,
            candidate_groups,
            lambda prompt: run_live_candidate_request(
                client,
                model_name=PHASE2_MODEL,
                prompt=prompt,
                candidate_ids=candidate_ids,
                request_context={
                    "request_id": request_id,
                    "request_simulation_step": representative["simulation_step"],
                },
            ),
            provider_name=PHASE2_PROVIDER_NAME,
            model_name=PHASE2_MODEL,
            llm_mode="real",
        )
        entry = trace[vehicle_states[0]["vehicle_id"]]
        live_result = {
                "scenario_class": summary["scenario_class"],
                "scenario_id": summary["scenario_id"],
                "vehicle_count": summary["vehicle_count"],
                "seed": summary["seed"],
                "simulation_step": representative["simulation_step"],
                "request_id": request_id,
                "provider": entry.get("actual_provider", entry.get("provider_name", "")),
                "model": entry.get("actual_model", entry.get("model_name", "")),
                "request_success": bool(entry.get("provider_request_success")),
                "http_status": entry.get("http_status"),
                "parser_success": bool(entry.get("parser_success")),
                "fallback_used": bool(entry.get("fallback_used")),
                "fallback_reason": entry.get("fallback_reason", ""),
                "provider_failure_reason": entry.get("provider_failure_reason", ""),
                "parser_failure_reason": entry.get("parser_failure_reason", ""),
                "latency_ms": entry.get("latency_ms"),
                "prompt_tokens": entry.get("prompt_tokens"),
                "completion_tokens": entry.get("completion_tokens"),
                "total_tokens": entry.get("total_tokens"),
                "llm_raw_output": entry.get("llm_raw_output", ""),
                "candidate_count": len(candidate_groups),
                "llm_candidate_id": entry.get("llm_candidate_id", ""),
                "deterministic_candidate_id": entry.get("deterministic_candidate_id", ""),
                "candidate_agreement": entry.get("candidate_agreement"),
                "candidate_disagreement": bool(entry.get("candidate_disagreement")),
                "final_selected_candidate": entry.get("final_selected_candidate", ""),
                "safety_intervention_count": sum(bool(item.get("safety_intervened")) for item in trace.values()),
                "final_actions": {vehicle_id: item.get("final_decision") for vehicle_id, item in trace.items()},
            }
        live_results.append(live_result)
        if live_result["request_success"]:
            repeated_failure_reason = ""
            repeated_failure_count = 0
            continue
        failure_reason = live_result["provider_failure_reason"] or live_result["fallback_reason"] or "UNKNOWN"
        if failure_reason == repeated_failure_reason:
            repeated_failure_count += 1
        else:
            repeated_failure_reason = failure_reason
            repeated_failure_count = 1
        if repeated_failure_count >= 2:
            break
    return live_results


def summarize_live_results(live_results: list[dict]) -> dict:
    count = len(live_results)
    comparable = [item for item in live_results if item.get("candidate_agreement") is not None]
    token_fields = ("prompt_tokens", "completion_tokens", "total_tokens")
    summary = {
        "request_count": count,
        "request_success_count": sum(bool(item.get("request_success")) for item in live_results),
        "parser_success_count": sum(bool(item.get("parser_success")) for item in live_results),
        "fallback_count": sum(bool(item.get("fallback_used")) for item in live_results),
        "comparable_decisions": len(comparable),
        "agreement_count": sum(item.get("candidate_agreement") is True for item in comparable),
        "disagreement_count": sum(bool(item.get("candidate_disagreement")) for item in comparable),
        "safety_intervention_count": sum(int(item.get("safety_intervention_count", 0)) for item in live_results),
    }
    for field in token_fields:
        values = [float(item[field]) for item in live_results if item.get(field) is not None]
        summary[f"mean_{field}"] = fmean(values) if values else None
        summary[f"total_{field}"] = sum(values) if values else None
    latencies = [float(item["latency_ms"]) for item in live_results if item.get("latency_ms") is not None]
    summary["mean_latency_ms"] = fmean(latencies) if latencies else None
    summary["minimum_latency_ms"] = min(latencies) if latencies else None
    summary["maximum_latency_ms"] = max(latencies) if latencies else None
    return summary
