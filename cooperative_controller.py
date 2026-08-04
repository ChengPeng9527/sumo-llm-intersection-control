from __future__ import annotations

import os
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
    get_vehicle_route,
    is_in_control_zone,
    print_summary,
    run_artifact_paths,
    write_run_artifacts,
)
from src.safety.route_conflict import routes_compatible, validate_conflict_matrix


SUMO_BINARY = CONFIG["sumo_gui_binary_path"]
SUMO_CONFIG = Path(os.getenv("SUMO_CONFIG_PATH", str(CONFIG["sumo_config_path"])))
EXPERIMENT_ID = "E02_COOPERATIVE_4V_S1"
CONTROLLER_NAME = "CooperativeRule"
SCENARIO = os.getenv("SCENARIO_ID", "debug_four_vehicle")
VEHICLE_COUNT = int(os.getenv("VEHICLE_COUNT", "4"))
SEED = CONFIG["default_seed"]
SIMULATION_STEPS = int(os.getenv("SIMULATION_STEPS", str(CONFIG["default_simulation_duration"])))
RUN_ID = f"{EXPERIMENT_ID}_v{VEHICLE_COUNT}_seed{SEED}"
ARTIFACTS = run_artifact_paths(RUN_ID)
OUTPUT_CSV = ARTIFACTS["step_records"]


def choose_priority_vehicle(vehicles):
    candidates = [v for v in vehicles if is_in_control_zone(traci, v)]
    if not candidates:
        return None
    return min(candidates, key=lambda v: distance_to_center(traci, v))


def are_routes_compatible(route_a, route_b):
    return routes_compatible(route_a, route_b)


def decide(vehicles):
    decisions = {}
    priority = choose_priority_vehicle(vehicles)
    if priority is None:
        for vid in vehicles:
            decisions[vid] = "FREE"
        return decisions

    priority_route = get_vehicle_route(traci, priority)
    for vid in vehicles:
        if not is_in_control_zone(traci, vid):
            decisions[vid] = "FREE"
        elif vid == priority:
            decisions[vid] = "PROCEED"
        else:
            route_id = get_vehicle_route(traci, vid)
            decisions[vid] = "PROCEED" if are_routes_compatible(priority_route, route_id) else "WAIT"
    return decisions


def run():
    matrix_status = validate_conflict_matrix()
    print(f"Route matrix valid: {matrix_status['valid']}")
    traci.start([str(SUMO_BINARY), "-c", str(SUMO_CONFIG), "--start"])
    records = []
    events = []
    all_seen_vehicles = set()
    departed_seen = set()
    arrived_seen = set()

    for step in range(SIMULATION_STEPS):
        traci.simulationStep()
        departed_ids = list(traci.simulation.getDepartedIDList())
        arrived_ids = list(traci.simulation.getArrivedIDList())
        simulation_time = step * CONFIG["simulation_step_length"]
        for vid in departed_ids:
            if vid not in departed_seen:
                departed_seen.add(vid)
                events.append(
                    build_event(
                        run_id=RUN_ID,
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
                        run_id=RUN_ID,
                        event_type="arrived",
                        simulation_step=step,
                        simulation_time_seconds=simulation_time,
                        vehicle_id=vid,
                        details="vehicle left the simulation",
                    )
                )
        vehicles = list(traci.vehicle.getIDList())
        all_seen_vehicles.update(vehicles)
        decisions = decide(vehicles)

        for vid in vehicles:
            raw_decision = decisions[vid]
            final_decision = raw_decision
            outside_rule = not is_in_control_zone(traci, vid)
            postprocess_applied = is_in_control_zone(traci, vid)
            postprocess_reason = ""
            if postprocess_applied:
                postprocess_reason = "compatible_route" if final_decision == "PROCEED" else "route_conflict"
            apply_decision(traci, vid, final_decision)
            records.append(
                create_record(
                    experiment_id=EXPERIMENT_ID,
                    controller=CONTROLLER_NAME,
                    scenario=SCENARIO,
                    seed=SEED,
                    step=step,
                    traci=traci,
                    veh_id=vid,
                    raw_decision=raw_decision,
                    final_decision=final_decision,
                    conflict=False,
                    llm_raw_decision=raw_decision,
                    validated_llm_decision=raw_decision,
                    postprocessed_decision=final_decision,
                    run_id=RUN_ID,
                    safety_enabled=False,
                    simulation_time_seconds=simulation_time,
                    vehicle_count=VEHICLE_COUNT,
                    outside_control_zone_rule_applied=outside_rule,
                    postprocess_applied=postprocess_applied,
                    postprocess_reason=postprocess_reason,
                    safety_override=False,
                    safety_reason="",
                    decision_source="COOPERATIVE_POSTPROCESSOR" if postprocess_applied else "DETERMINISTIC_INTERFACE_RULE",
                    departed=vid in departed_seen,
                    arrived=False,
                )
            )
        time.sleep(0.03)

    traci.close(False)
    metadata = build_run_metadata(
        run_id=RUN_ID,
        controller=CONTROLLER_NAME,
        safety_enabled=False,
        scenario_id=SCENARIO,
        density="debug",
        vehicle_count=VEHICLE_COUNT,
        seed=SEED,
        status="completed",
    )
    metadata["departed_count"] = len(departed_seen)
    metadata["arrived_count"] = len(arrived_seen)
    metadata["collision_count"] = 0
    write_run_artifacts(RUN_ID, records, events, metadata)
    summary = calculate_summary(records, all_seen_vehicles, run_metadata=metadata)
    print_summary("Cooperative Rule Controller Metrics", summary, OUTPUT_CSV)


if __name__ == "__main__":
    run()
