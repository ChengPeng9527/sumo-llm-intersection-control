import traci
import time
import math
import csv

SUMO_GUI = r"D:\Sumo\bin\sumo-gui.exe"
CONFIG = r"D:\Sumo\sumo_train\simulation.sumocfg"

INTERSECTION_CENTER = (-43.65, 11.26)
CONTROL_RADIUS = 45
MAX_SPEED = 13.89

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
stop_counts = {}
arrived = set()

for step in range(200):
    traci.simulationStep()

    vehicles = list(traci.vehicle.getIDList())
    priority = choose_priority_vehicle(vehicles)

    for vid in vehicles:
        speed = traci.vehicle.getSpeed(vid)
        dist = distance_to_center(vid)

        if vid not in stop_counts:
            stop_counts[vid] = 0

        if is_in_control_zone(vid):
            if vid == priority:
                traci.vehicle.setSpeed(vid, MAX_SPEED)
                decision = "PROCEED"
            else:
                traci.vehicle.setSpeed(vid, 0)
                decision = "WAIT"
                if speed < 0.1:
                    stop_counts[vid] += 1
        else:
            traci.vehicle.setSpeed(vid, MAX_SPEED)
            decision = "FREE"

        records.append({
            "step": step,
            "vehicle": vid,
            "speed": speed,
            "distance_to_intersection": dist,
            "decision": decision
        })
    
    time.sleep(0.05)
    print("Simulation finished")
traci.close(False)

with open(r"D:\Sumo\sumo_train\baseline_records.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["step", "vehicle", "speed", "distance_to_intersection", "decision"]
    )
    writer.writeheader()
    writer.writerows(records)

print("Saved baseline_records.csv")
print("Stop counts:", stop_counts)