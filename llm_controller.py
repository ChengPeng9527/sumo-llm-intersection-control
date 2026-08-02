from __future__ import annotations

import time

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
from src.llm.prompt_builder import build_structured_prompt
from src.safety.route_conflict import validate_conflict_matrix
from ttc_safety import verify_decisions


SUMO_BINARY = CONFIG["sumo_gui_binary_path"]
SUMO_CONFIG = CONFIG["sumo_config_path"]
EXPERIMENT_ID = "E03_LLM_MOCK_4V_S1"
CONTROLLER_NAME = "LLMMockController"
SCENARIO = "debug_four_vehicle"
SEED = CONFIG["default_seed"]
SIMULATION_STEPS = CONFIG["default_simulation_duration"]
USE_SAFETY_LAYER = True
RUN_ID = f"{EXPERIMENT_ID}_seed{SEED}"
ARTIFACTS = run_artifact_paths(RUN_ID)
OUTPUT_CSV = ARTIFACTS["step_records"]


def build_traffic_state(vehicles):
    state = []
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


def decide(vehicles):
    traffic_state = build_traffic_state(vehicles)
    prompt = build_structured_prompt(traffic_state, validate_conflict_matrix())
    raw_decisions = mock_llm_decision(traffic_state)
    return raw_decisions, prompt


def run():
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

        raw_decisions, _prompt = decide(vehicles)
        if USE_SAFETY_LAYER:
            final_decisions, conflict_flags, conflict_types, priority_reason = verify_decisions(
                traci,
                vehicles,
                raw_decisions,
            )
        else:
            final_decisions = dict(raw_decisions)
            conflict_flags = {vid: False for vid in vehicles}
            conflict_types = {vid: "" for vid in vehicles}
            priority_reason = ""

        for vid in vehicles:
            raw_decision = raw_decisions.get(vid, "WAIT")
            final_decision = final_decisions.get(vid, "WAIT")
            conflict = conflict_flags.get(vid, False)
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
                    conflict=conflict,
                    conflict_type=conflict_types.get(vid, ""),
                    priority_reason=priority_reason,
                    run_id=RUN_ID,
                    safety_enabled=USE_SAFETY_LAYER,
                    simulation_time_seconds=simulation_time,
                    llm_mode="mock",
                    departed=vid in departed_seen,
                    arrived=False,
                )
            )
        time.sleep(0.03)

    traci.close(False)
    metadata = build_run_metadata(
        run_id=RUN_ID,
        controller=CONTROLLER_NAME,
        safety_enabled=USE_SAFETY_LAYER,
        scenario_id=SCENARIO,
        density="debug",
        seed=SEED,
        llm_mode="mock",
        status="completed",
    )
    metadata["departed_count"] = len(departed_seen)
    metadata["arrived_count"] = len(arrived_seen)
    metadata["collision_count"] = 0
    write_run_artifacts(RUN_ID, records, events, metadata)
    summary = calculate_summary(records, all_seen_vehicles, run_metadata=metadata)
    print_summary("LLM Mock Controller With Safety Metrics", summary, OUTPUT_CSV)


if __name__ == "__main__":
    run()
