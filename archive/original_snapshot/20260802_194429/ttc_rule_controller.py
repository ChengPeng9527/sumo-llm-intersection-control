import traci
import time
import math
import csv

SUMO_GUI = r"D:\Sumo\bin\sumo-gui.exe"
CONFIG = r"D:\Sumo\sumo_train\simulation.sumocfg"

INTERSECTION_CENTER = (-43.65, 11.26)
CONTROL_RADIUS = 45
MAX_SPEED = 13.89
STOP_SPEED = 0.1
TTC_THRESHOLD = 3.0

OUTPUT_CSV = r"D:\Sumo\sumo_train\ttc_rule_records.csv"


def distance_to_center(veh_id):
    x, y = traci.vehicle.getPosition(veh_id)
    cx, cy = INTERSECTION_CENTER
    return math.sqrt((x - cx) ** 2 + (y - cy) ** 2)


def is_in_control_zone(veh_id):
    return distance_to_center(veh_id) < CONTROL_RADIUS

 
def estimate_time_to_intersection(veh_id):
    speed = traci.vehicle.getSpeed(veh_id)
    dist = distance_to_center(veh_id)

    if speed < 0.1:
        return float("inf")

    return dist / speed


def has_ttc_conflict(veh_id, vehicles):
    my_tti = estimate_time_to_intersection(veh_id)

    for other in vehicles:
        if other == veh_id:
            continue

        if not is_in_control_zone(other):
            continue

        other_tti = estimate_time_to_intersection(other)

        # 如果两辆车预计几乎同时到达路口，则认为存在冲突风险
        if abs(my_tti - other_tti) < TTC_THRESHOLD:
            return True

    return False


def choose_priority_vehicle(vehicles):
    candidates = [v for v in vehicles if is_in_control_zone(v)]
    if not candidates:
        return None

    return min(candidates, key=distance_to_center)


traci.start([
    SUMO_GUI,
    "-c", CONFIG,
    "--start"
])

records = []
stop_count = {}
waiting_time = {}
ttc_violations = 0
all_seen_vehicles = set()

for step in range(200):
    traci.simulationStep()

    vehicles = list(traci.vehicle.getIDList())
    all_seen_vehicles.update(vehicles)

    priority = choose_priority_vehicle(vehicles)

    for vid in vehicles:
        speed = traci.vehicle.getSpeed(vid)
        dist = distance_to_center(vid)
        tti = estimate_time_to_intersection(vid)

        if vid not in stop_count:
            stop_count[vid] = 0
        if vid not in waiting_time:
            waiting_time[vid] = 0

        in_zone = is_in_control_zone(vid)
        conflict = has_ttc_conflict(vid, vehicles)

        raw_decision = "FREE"
        final_decision = "FREE"

        if in_zone:
            if vid == priority:
                raw_decision = "PROCEED"
            else:
                raw_decision = "WAIT"
        else:
            raw_decision = "FREE"

        # Safety filter
        if in_zone and conflict and vid != priority:
            final_decision = "WAIT"
            ttc_violations += 1
        else:
            final_decision = raw_decision

        if final_decision == "WAIT":
            traci.vehicle.setSpeed(vid, 0)
        else:
            traci.vehicle.setSpeed(vid, MAX_SPEED)

        if speed < STOP_SPEED:
            stop_count[vid] += 1
            waiting_time[vid] += 1

        records.append({
            "step": step,
            "vehicle": vid,
            "speed": speed,
            "distance_to_intersection": dist,
            "time_to_intersection": tti,
            "raw_decision": raw_decision,
            "final_decision": final_decision,
            "conflict": conflict
        })

    time.sleep(0.03)

traci.close(False)

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "step",
            "vehicle",
            "speed",
            "distance_to_intersection",
            "time_to_intersection",
            "raw_decision",
            "final_decision",
            "conflict"
        ]
    )
    writer.writeheader()
    writer.writerows(records)

total_vehicles = len(all_seen_vehicles)
total_stop_events = sum(stop_count.values())
avg_waiting_time = sum(waiting_time.values()) / total_vehicles if total_vehicles > 0 else 0
avg_speed = sum(r["speed"] for r in records) / len(records) if records else 0

print("=== TTC Rule Controller Metrics ===")
print(f"Vehicles observed: {total_vehicles}")
print(f"Total stop events: {total_stop_events}")
print(f"Average waiting time per vehicle: {avg_waiting_time:.2f} steps")
print(f"Average speed: {avg_speed:.2f} m/s")
print(f"TTC conflict events: {ttc_violations}")
print(f"Saved: {OUTPUT_CSV}")