from __future__ import annotations

import time

import traci

from common import (
    CONFIG,
    apply_decision,
    calculate_summary,
    create_record,
    distance_to_center,
    estimate_time_to_intersection,
    get_vehicle_route,
    is_in_control_zone,
    print_summary,
    write_records,
)
from src.llm.fallback_policy import mock_llm_decision
from src.llm.prompt_builder import build_basic_prompt
from ttc_safety import verify_decisions


SUMO_BINARY = CONFIG["sumo_gui_binary_path"]
SUMO_CONFIG = CONFIG["sumo_config_path"]
EXPERIMENT_ID = "E03_LLM_MOCK_4V_S1"
CONTROLLER_NAME = "LLMMockController"
SCENARIO = "debug_four_vehicle"
SEED = CONFIG["default_seed"]
SIMULATION_STEPS = CONFIG["default_simulation_duration"]
USE_SAFETY_LAYER = True
OUTPUT_CSV = CONFIG["results_dir_path"] / "E03_LLM_MOCK_4V_S1_records.csv"


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
    prompt = build_basic_prompt(traffic_state)
    raw_decisions = mock_llm_decision(traffic_state)
    return raw_decisions, prompt


def run():
    traci.start([str(SUMO_BINARY), "-c", str(SUMO_CONFIG), "--start"])
    records = []
    all_seen_vehicles = set()

    for step in range(SIMULATION_STEPS):
        traci.simulationStep()
        vehicles = list(traci.vehicle.getIDList())
        all_seen_vehicles.update(vehicles)

        raw_decisions, _prompt = decide(vehicles)
        if USE_SAFETY_LAYER:
            final_decisions, conflict_flags = verify_decisions(traci, vehicles, raw_decisions)
        else:
            final_decisions = dict(raw_decisions)
            conflict_flags = {vid: False for vid in vehicles}

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
                    safety_enabled=USE_SAFETY_LAYER,
                    llm_mode="mock",
                )
            )
        time.sleep(0.03)

    traci.close(False)
    write_records(OUTPUT_CSV, records)
    summary = calculate_summary(records, all_seen_vehicles)
    print_summary("LLM Mock Controller With Safety Metrics", summary, OUTPUT_CSV)


if __name__ == "__main__":
    run()
