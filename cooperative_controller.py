from __future__ import annotations

import time

import traci

from common import (
    CONFIG,
    MAX_SPEED,
    apply_decision,
    calculate_summary,
    create_record,
    distance_to_center,
    get_vehicle_route,
    is_in_control_zone,
    print_summary,
    write_records,
)
from src.safety.route_conflict import routes_compatible, validate_conflict_matrix


SUMO_BINARY = CONFIG["sumo_gui_binary_path"]
SUMO_CONFIG = CONFIG["sumo_config_path"]
EXPERIMENT_ID = "E02_COOPERATIVE_4V_S1"
CONTROLLER_NAME = "CooperativeRule"
SCENARIO = "debug_four_vehicle"
SEED = CONFIG["default_seed"]
SIMULATION_STEPS = CONFIG["default_simulation_duration"]
OUTPUT_CSV = CONFIG["results_dir_path"] / "E02_COOPERATIVE_4V_S1_records.csv"


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
    all_seen_vehicles = set()

    for step in range(SIMULATION_STEPS):
        traci.simulationStep()
        vehicles = list(traci.vehicle.getIDList())
        all_seen_vehicles.update(vehicles)
        decisions = decide(vehicles)

        for vid in vehicles:
            raw_decision = decisions[vid]
            final_decision = raw_decision
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
                )
            )
        time.sleep(0.03)

    traci.close(False)
    write_records(OUTPUT_CSV, records)
    summary = calculate_summary(records, all_seen_vehicles)
    print_summary("Cooperative Rule Controller Metrics", summary, OUTPUT_CSV)


if __name__ == "__main__":
    run()
