import traci
import time
import os

BASE_DIR = r"D:\Sumo\sumo_train"
SUMO_GUI = r"D:\Sumo\bin\sumo-gui.exe"
CONFIG = os.path.join(BASE_DIR, "simulation.sumocfg")

traci.start([
    SUMO_GUI,
    "-c", CONFIG,
    "--start"
])

for step in range(200):
    traci.simulationStep()

    vehicles = traci.vehicle.getIDList()
    print(f"Step {step}: {vehicles}")

    for vid in vehicles:
        speed = traci.vehicle.getSpeed(vid)
        pos = traci.vehicle.getPosition(vid)
        print(f"  {vid}: speed={speed:.2f}, pos={pos}")

    time.sleep(0.05)

traci.close()