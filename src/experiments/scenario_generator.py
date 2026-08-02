from __future__ import annotations

import json
import random
from pathlib import Path
from xml.etree import ElementTree as ET

from src.common.config import load_project_config


CONFIG = load_project_config()
PROJECT_ROOT = Path(CONFIG["project_root"])
GENERATED_ROOT = PROJECT_ROOT / "simulation" / "generated_routes"
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


def generate_scenario(scenario_id: str, density_name: str, seed: int) -> dict:
    matrix = load_project_config()
    matrix_path = PROJECT_ROOT / "config" / "experiment_matrix.yaml"
    import yaml

    with matrix_path.open("r", encoding="utf-8") as f:
        exp = yaml.safe_load(f)

    density = exp["densities"][density_name]
    vehicles_per_hour = int(density["vehicles_per_hour"])
    duration = int(density["simulation_duration_seconds"])
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

    generation_config = {
        "scenario_id": scenario_id,
        "density": density_name,
        "seed": seed,
        "vehicles_per_hour": vehicles_per_hour,
        "simulation_duration_seconds": duration,
        "total_vehicles": total_vehicles,
    }
    (out_dir / "generation_config.json").write_text(json.dumps(generation_config, indent=2), encoding="utf-8")
    (out_dir / "generation_manifest.json").write_text(json.dumps({"routes_file": str(routes_path)}, indent=2), encoding="utf-8")
    return generation_config
