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

OUTPUT_CSV = r"D:\Sumo\sumo_train\safe_rule_records.csv"


def distance_to_center(veh_id):
    x, y = traci.vehicle.getPosition(veh_id) 
    cx, cy = INTERSECTION_CENTER 
    return math.sqrt((x - cx) ** 2 + (y - cy) ** 2)


def is_in_control_zone(veh_id):
    return distance_to_center(veh_id) < CONTROL_RADIUS


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
all_seen_vehicles = set()
arrived_vehicles = set()

for step in range(200):
    traci.simulationStep()

    vehicles = list(traci.vehicle.getIDList())
    all_seen_vehicles.update(vehicles)

    priority = choose_priority_vehicle(vehicles)

    for vid in vehicles:
        speed = traci.vehicle.getSpeed(vid)
        dist = distance_to_center(vid)

        if vid not in stop_count:
            stop_count[vid] = 0
        if vid not in waiting_time:
            waiting_time[vid] = 0

        if is_in_control_zone(vid):
            if vid == priority:
                decision = "PROCEED"
                traci.vehicle.setSpeed(vid, MAX_SPEED)
            else:
                decision = "WAIT"
                traci.vehicle.setSpeed(vid, 0)
        else:
            decision = "FREE"
            traci.vehicle.setSpeed(vid, MAX_SPEED)

        if speed < STOP_SPEED:
            stop_count[vid] += 1
            waiting_time[vid] += 1

        records.append({
            "step": step,
            "vehicle": vid,
            "speed": speed,
            "distance_to_intersection": dist,
            "decision": decision
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
            "decision"
        ]
    )
    writer.writeheader()
    writer.writerows(records)

total_vehicles = len(all_seen_vehicles)
total_stop_events = sum(stop_count.values())
avg_waiting_time = sum(waiting_time.values()) / total_vehicles if total_vehicles > 0 else 0
avg_speed = sum(r["speed"] for r in records) / len(records) if records else 0

print("=== Safe Rule Controller Metrics ===")
print(f"Vehicles observed: {total_vehicles}")
print(f"Total stop events: {total_stop_events}")
print(f"Average waiting time per vehicle: {avg_waiting_time:.2f} steps")
print(f"Average speed: {avg_speed:.2f} m/s")
print(f"Saved: {OUTPUT_CSV}")