import traci
import time
import math

SUMO_GUI = r"D:\Sumo\bin\sumo-gui.exe"
CONFIG = r"D:\Sumo\sumo_train\simulation.sumocfg"

traci.start([
    SUMO_GUI,
    "-c", CONFIG,
    "--start"
])

for step in range(200):

    traci.simulationStep()

    vehicles = traci.vehicle.getIDList()

    # 示例：强制停止 car0
    if "car0" in vehicles:

        x, y = traci.vehicle.getPosition("car0")

        # 接近路口时停车
        if y < 40 and y > 10:
            traci.vehicle.setSpeed("car0", 0)
            print("STOP car0")

        else:
            traci.vehicle.setSpeed("car0", 13.89)

    time.sleep(0.05)

traci.close()