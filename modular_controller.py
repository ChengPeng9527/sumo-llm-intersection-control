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

OUTPUT_CSV = r"D:\Sumo\sumo_train\modular_records.csv"


def distance_to_center_by_pos(x, y):
    cx, cy = INTERSECTION_CENTER
    return math.sqrt((x - cx) ** 2 + (y - cy) ** 2)


def get_vehicle_direction(route_id):
    """
    根据 route id 判断车辆方向。
    例如 N_S, S_N, E_W, W_E。
    """
    if "_" not in route_id:
        return "UNKNOWN" 

    return route_id


def extract_state():
    """
    从 SUMO 提取结构化车辆状态。
    这一步以后就是 LLM prompt 的输入来源。
    """
    vehicles = list(traci.vehicle.getIDList())
    state = {}

    for vid in vehicles:
        x, y = traci.vehicle.getPosition(vid)
        speed = traci.vehicle.getSpeed(vid)
        route_id = traci.vehicle.getRouteID(vid)
        distance = distance_to_center_by_pos(x, y)

        state[vid] = {
            "id": vid,
            "x": x,
            "y": y,
            "speed": speed,
            "route": route_id,
            "distance_to_intersection": distance,
            "in_control_zone": distance < CONTROL_RADIUS
        }

    return state


def estimate_time_to_intersection(vehicle_state):
    speed = vehicle_state["speed"]
    dist = vehicle_state["distance_to_intersection"]

    if speed < 0.1:
        return float("inf")

    return dist / speed


def route_group(route_id):
    """
    把路线分组：
    N_S 和 S_N 属于 north_south
    E_W 和 W_E 属于 east_west

    后续 cooperative rule 允许同组直行车辆一起过。
    """
    if route_id in ["N_S", "S_N"]:
        return "north_south"
    if route_id in ["E_W", "W_E"]:
        return "east_west"
    return "other"


def decision_module(state):
    """
    当前是假LLM / cooperative rule。
    后面接 LLM 时，只需要替换这个函数。

    策略：
    1. 找到控制区内车辆。
    2. 选择最近车辆所在方向组作为当前通行组。
    3. 同一方向组车辆一起 PROCEED。
    4. 其他方向 WAIT。
    """
    decisions = {}

    controlled = {
        vid: s for vid, s in state.items()
        if s["in_control_zone"]
    }

    if not controlled:
        for vid in state:
            decisions[vid] = "FREE"
        return decisions

    nearest_vid = min(
        controlled,
        key=lambda vid: controlled[vid]["distance_to_intersection"]
    )

    active_group = route_group(controlled[nearest_vid]["route"])

    for vid, s in state.items():
        if not s["in_control_zone"]:
            decisions[vid] = "FREE"
        elif route_group(s["route"]) == active_group:
            decisions[vid] = "PROCEED"
        else:
            decisions[vid] = "WAIT"

    return decisions


def has_ttc_conflict(vid, state):
    """
    简化TTC风险判断：
    如果两辆不同方向组的车预计到达路口时间差小于阈值，则存在冲突。
    """
    my_state = state[vid]
    my_tti = estimate_time_to_intersection(my_state)
    my_group = route_group(my_state["route"])

    for other_id, other_state in state.items():
        if other_id == vid:
            continue

        if not other_state["in_control_zone"]:
            continue

        other_group = route_group(other_state["route"])

        # 同方向组直行暂时认为可并行
        if other_group == my_group:
            continue

        other_tti = estimate_time_to_intersection(other_state)

        if abs(my_tti - other_tti) < TTC_THRESHOLD:
            return True

    return False


def safety_filter(raw_decisions, state):
    """
    安全层：
    如果存在TTC冲突，非优先车辆 WAIT。
    """
    final_decisions = dict(raw_decisions)

    controlled = {
        vid: s for vid, s in state.items()
        if s["in_control_zone"]
    }

    if not controlled:
        return final_decisions, 0

    priority_vid = min(
        controlled,
        key=lambda vid: controlled[vid]["distance_to_intersection"]
    )

    ttc_conflict_events = 0

    for vid in controlled:
        conflict = has_ttc_conflict(vid, state)

        if conflict:
            ttc_conflict_events += 1

            if vid != priority_vid:
                final_decisions[vid] = "WAIT"

    return final_decisions, ttc_conflict_events


def apply_control(decisions):
    for vid, decision in decisions.items():
        if vid not in traci.vehicle.getIDList():
            continue

        if decision == "WAIT":
            traci.vehicle.setSpeed(vid, 0)
        else:
            traci.vehicle.setSpeed(vid, MAX_SPEED)


traci.start([
    SUMO_GUI,
    "-c", CONFIG,
    "--start"
])

records = []
stop_count = {}
waiting_time = {}
all_seen_vehicles = set()
total_ttc_conflict_events = 0

for step in range(200):
    traci.simulationStep()

    state = extract_state()
    all_seen_vehicles.update(state.keys())

    raw_decisions = decision_module(state)
    final_decisions, ttc_events = safety_filter(raw_decisions, state)
    total_ttc_conflict_events += ttc_events

    apply_control(final_decisions)

    for vid, s in state.items():
        speed = s["speed"]

        if vid not in stop_count:
            stop_count[vid] = 0
        if vid not in waiting_time:
            waiting_time[vid] = 0

        if speed < STOP_SPEED:
            stop_count[vid] += 1
            waiting_time[vid] += 1

        records.append({
            "step": step,
            "vehicle": vid,
            "speed": s["speed"],
            "route": s["route"],
            "distance_to_intersection": s["distance_to_intersection"],
            "in_control_zone": s["in_control_zone"],
            "raw_decision": raw_decisions.get(vid, "NONE"),
            "final_decision": final_decisions.get(vid, "NONE")
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
            "route",
            "distance_to_intersection",
            "in_control_zone",
            "raw_decision",
            "final_decision"
        ]
    )
    writer.writeheader()
    writer.writerows(records)

total_vehicles = len(all_seen_vehicles)
total_stop_events = sum(stop_count.values())
avg_waiting_time = sum(waiting_time.values()) / total_vehicles if total_vehicles > 0 else 0
avg_speed = sum(r["speed"] for r in records) / len(records) if records else 0

print("=== Modular Cooperative Rule Controller Metrics ===")
print(f"Vehicles observed: {total_vehicles}")
print(f"Total stop events: {total_stop_events}")
print(f"Average waiting time per vehicle: {avg_waiting_time:.2f} steps")
print(f"Average speed: {avg_speed:.2f} m/s")
print(f"TTC conflict events: {total_ttc_conflict_events}")
print(f"Saved: {OUTPUT_CSV}")