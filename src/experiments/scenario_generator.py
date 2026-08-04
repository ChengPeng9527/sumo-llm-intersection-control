from __future__ import annotations

import json
import random
from pathlib import Path
from xml.etree import ElementTree as ET

from src.common.config import load_project_config, load_yaml_config


CONFIG = load_project_config()
PROJECT_ROOT = Path(CONFIG["project_root"])
GENERATED_ROOT = PROJECT_ROOT / "simulation" / "generated_routes"
BASE_SUMOCFG = PROJECT_ROOT / "simulation.sumocfg"
EDGE_MAP = {
    "N_S": ("N", "-S"),
    "S_N": ("S", "-N"),
    "E_W": ("E", "-W"),
    "W_E": ("W", "-E"),
}


def _route_sequence(route_distribution: dict[str, float], count: int, seed: int) -> list[str]:
    rnd = random.Random(seed)
    routes = list(route_distribution.keys())
    weights = [route_distribution[r] for r in routes]
    return rnd.choices(routes, weights=weights, k=count)


def load_experiment_matrix() -> dict:
    return load_yaml_config("experiment_matrix.yaml")


def generate_scenario(
    scenario_id: str,
    density_name: str,
    seed: int,
    vehicle_count: int | None = None,
) -> dict:
    experiment_matrix = load_experiment_matrix()

    density = experiment_matrix["densities"][density_name]
    vehicles_per_hour = int(density["vehicles_per_hour"])
    base_duration = int(density["simulation_duration_seconds"])
    if vehicle_count is not None:
        total_vehicles = int(vehicle_count)
        duration = max(base_duration, 240 + max(0, total_vehicles - 4) * 40)
    else:
        duration = base_duration
        total_vehicles = max(1, int(round(vehicles_per_hour * duration / 3600)))
    route_ids = _route_sequence(density["route_distribution"], total_vehicles, seed)
    rnd = random.Random(seed)

    out_dir = GENERATED_ROOT / scenario_id
    out_dir.mkdir(parents=True, exist_ok=True)

    root = ET.Element("routes")
    ET.SubElement(
        root,
        "vType",
        attrib={
            "id": "car",
            "accel": "2.6",
            "decel": "4.5",
            "sigma": "0.5",
            "length": "5",
            "maxSpeed": str(CONFIG["max_speed"]),
        },
    )
    for route_id in density["route_distribution"].keys():
        edge_a, edge_b = EDGE_MAP.get(route_id, (route_id, route_id))
        ET.SubElement(root, "route", attrib={"id": route_id, "edges": f"{edge_a} {edge_b}"})

    depart = 0
    min_gap = int(density["minimum_depart_gap"])
    max_gap = int(density["maximum_depart_gap"])
    for idx, route_id in enumerate(route_ids):
        ET.SubElement(
            root,
            "vehicle",
            attrib={
                "id": f"{scenario_id}_{seed}_{idx}",
                "type": "car",
                "route": route_id,
                "depart": str(depart),
                "departLane": "best",
            },
        )
        depart += rnd.randint(min_gap, max_gap)

    routes_path = out_dir / "routes.xml"
    ET.ElementTree(root).write(routes_path, encoding="utf-8", xml_declaration=True)

    scenario_sumocfg = out_dir / "simulation.sumocfg"
    try:
        config_tree = ET.parse(BASE_SUMOCFG)
        config_root = config_tree.getroot()
        for route_node in config_root.iter("route-files"):
            route_node.set("value", str(routes_path.resolve()))
        for net_node in config_root.iter("net-file"):
            net_node.set("value", str((PROJECT_ROOT / "net.net.xml").resolve()))
        config_tree.write(scenario_sumocfg, encoding="utf-8", xml_declaration=True)
    except Exception:
        scenario_sumocfg.write_text(
            (
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                "<configuration>\n"
                "  <input>\n"
                f"    <net-file value=\"{(PROJECT_ROOT / 'net.net.xml').resolve()}\"/>\n"
                f"    <route-files value=\"{routes_path.resolve()}\"/>\n"
                "  </input>\n"
                "</configuration>\n"
            ),
            encoding="utf-8",
        )

    generation_config = {
        "scenario_id": scenario_id,
        "density": density_name,
        "seed": seed,
        "vehicle_count": total_vehicles,
        "vehicles_per_hour": vehicles_per_hour,
        "simulation_duration_seconds": duration,
        "total_vehicles": total_vehicles,
        "route_sequence": route_ids,
        "sumocfg_path": str(scenario_sumocfg),
    }
    (out_dir / "generation_config.json").write_text(json.dumps(generation_config, indent=2), encoding="utf-8")
    (out_dir / "generation_manifest.json").write_text(
        json.dumps(
            {
                "routes_file": str(routes_path),
                "route_count": len(route_ids),
                "route_ids": list(density["route_distribution"].keys()),
                "vehicle_count": total_vehicles,
                "seed": seed,
                "scenario_id": scenario_id,
                "sumocfg_path": str(scenario_sumocfg),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return generation_config
