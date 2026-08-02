import random
from xml.etree import ElementTree as Et
import xml.dom.minidom as minidom
import pandas as pd
import numpy as np


traffic_flows_data = pd.read_excel("traffic_volume.xls", index_col=0)

class Direction:
    def __init__(self, vehicles_per_hour, route, name):
        self.vehicles_per_hour = vehicles_per_hour
        self.volume = 0
        self.depart_times = []
        self.route = route
        self.id = name
        self.count = 0

N_N_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "北进口调头"]))
N_N_route = traffic_flows_data.loc["routes", "北进口调头"]
N_N = Direction(N_N_volume, N_N_route, "N_N")

N_S_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "北进口向南"]))
N_S_route = traffic_flows_data.loc["routes", "北进口向南"]
N_S = Direction(N_S_volume, N_S_route, "N_S")

N_W_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "北进口向西"]))
N_W_route = traffic_flows_data.loc["routes", "北进口向西"]
N_W = Direction(N_W_volume, N_W_route, "N_W")

N_E_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "北进口向东"]))
N_E_route = traffic_flows_data.loc["routes", "北进口向东"]
N_E = Direction(N_E_volume, N_E_route, "N_E")

S_S_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "南进口调头"]))
S_S_route = traffic_flows_data.loc["routes", "南进口调头"]
S_S = Direction(S_S_volume, S_S_route, "S_S")

S_N_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "南进口向北"]))
S_N_route = traffic_flows_data.loc["routes", "南进口向北"]
S_N = Direction(S_N_volume, S_N_route, "S_N")

S_W_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "南进口向西"]))
S_W_route = traffic_flows_data.loc["routes", "南进口向西"]
S_W = Direction(S_W_volume, S_W_route, "S_W")

S_E_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "南进口向东"]))
S_E_route = traffic_flows_data.loc["routes", "南进口向东"]
S_E = Direction(S_E_volume, S_E_route, "S_E")

W_W_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "西进口调头"]))
W_W_route = traffic_flows_data.loc["routes", "西进口调头"]
W_W = Direction(W_W_volume, W_W_route, "W_W")

W_N_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "西进口向北"]))
W_N_route = traffic_flows_data.loc["routes", "西进口向北"]
W_N = Direction(W_N_volume, W_N_route, "W_N")

W_S_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "西进口向南"]))
W_S_route = traffic_flows_data.loc["routes", "西进口向南"]
W_S = Direction(W_S_volume, W_S_route, "W_S")

W_E_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "西进口向东"]))
W_E_route = traffic_flows_data.loc["routes", "西进口向东"]
W_E = Direction(W_E_volume, W_E_route, "W_E")

E_E_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "东进口调头"]))
E_E_route = traffic_flows_data.loc["routes", "东进口调头"]
E_E = Direction(E_E_volume, E_E_route, "E_E")

E_N_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "东进口向北"]))
E_N_route = traffic_flows_data.loc["routes", "东进口向北"]
E_N = Direction(E_N_volume, E_N_route, "E_N")

E_S_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "东进口向南"]))
E_S_route = traffic_flows_data.loc["routes", "东进口向南"]
E_S = Direction(E_S_volume, E_S_route, "E_S")

E_W_volume = round(float(traffic_flows_data.loc["vehicles_per_hour", "东进口向西"]))
E_W_route = traffic_flows_data.loc["routes", "东进口向西"]
E_W = Direction(E_W_volume, E_W_route, "E_W")

Direction_list = [N_N, N_S, N_W, N_E, S_S, S_N, S_W, S_E, W_W, W_N, W_S, W_E, E_E, E_N, E_S, E_W]
# 开始编写route.xml文件
root = Et.Element("routes")
vType = Et.SubElement(root, "vType", attrib={"id":"v_type", "accel":"0.8", "color":"white", "decel":"4.5", "sigma":"0.5",
                                             "length":"5", "maxSpeed":"70"})

def write_routes(direction, tree_root):
    Et.SubElement(tree_root, "route", attrib={"id": f"{direction.id}", "edges": f"{direction.route}"})

for i in Direction_list:
    write_routes(i, root)

# 总的仿真时间
total_simulation_time = round(float(traffic_flows_data.loc["total_simulation_time(s)", "北进口调头"]))
total_vehicles_volume = 0
for k in Direction_list:
    k.volume = round(total_simulation_time / 3600) * k.vehicles_per_hour
    total_vehicles_volume += k.volume

depart_times_dic = {}
for j in Direction_list:
    for i in range(j.volume):
        if j.count > j.volume:
            break
        else:
            depart_times_dic[f"{j.id}_{j.count}_vehicle"] = [np.round(random.uniform(0, total_simulation_time), decimals=2), j.id]
            j.count += 1

sorted_depart_time = sorted(depart_times_dic.items(), key=lambda x:x[1])

for vehicle in sorted_depart_time:
    Et.SubElement(root, "vehicle", attrib={"id":vehicle[0], "type":"v_type", "depart":f"{int(vehicle[1][0])}", "route":vehicle[1][1], "departLane":"best"})

tree = Et.ElementTree(root)
rough_str = Et.tostring(root,"utf-8")
reparsed = minidom.parseString(rough_str)
new_str = reparsed.toprettyxml(indent='\t')
with open("routes.xml", "w", encoding="utf-8") as file:
    file.write(new_str)


