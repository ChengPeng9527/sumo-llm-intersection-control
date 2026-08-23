from __future__ import annotations

import json
import hashlib
import random
from pathlib import Path
from xml.etree import ElementTree as ET

from src.common.config import load_project_config, load_yaml_config
from src.safety.route_semantics import route_edges_for_route_id, supported_route_catalog, supported_route_ids


CONFIG = load_project_config()
PROJECT_ROOT = Path(CONFIG["project_root"])
GENERATED_ROOT = PROJECT_ROOT / "simulation" / "generated_routes"
BASE_SUMOCFG = PROJECT_ROOT / "simulation.sumocfg"
CAR_FOLLOWING_SIGMA = 0.5


def _route_sequence(route_distribution: dict[str, float], count: int, seed: int) -> list[str]:
    rnd = random.Random(seed)
    routes = list(route_distribution.keys())
    weights = [route_distribution[r] for r in routes]
    return rnd.choices(routes, weights=weights, k=count)


def load_experiment_matrix() -> dict:
    return load_yaml_config("experiment_matrix.yaml")


def _departure_times(count: int, seed: int, minimum_gap: int, maximum_gap: int) -> list[int]:
    rnd = random.Random(seed)
    departures: list[int] = []
    depart = 0
    for _ in range(count):
        departures.append(depart)
        depart += rnd.randint(minimum_gap, maximum_gap)
    return departures


def _targeted_demand(
    scenario_definition: dict,
    seed: int,
    vehicle_count: int,
) -> tuple[list[str], list[int]]:
    route_cycle = list(scenario_definition["route_cycle"])
    depart_offsets = [int(value) for value in scenario_definition["depart_offsets"]]
    if not route_cycle or len(route_cycle) != len(depart_offsets):
        raise ValueError("Targeted scenario route_cycle and depart_offsets must be non-empty and equal length")

    supported_counts = {int(value) for value in scenario_definition.get("supported_vehicle_counts", [])}
    if supported_counts and vehicle_count not in supported_counts:
        raise ValueError(f"Unsupported targeted vehicle count: {vehicle_count}")

    wave_spacing = int(scenario_definition["wave_spacing_seconds"])
    jitter = int(scenario_definition.get("departure_jitter_seconds", 0))
    rnd = random.Random(seed)
    demand: list[tuple[int, int, str]] = []
    last_departure_by_approach: dict[str, int] = {}
    for index in range(vehicle_count):
        wave_index, cycle_index = divmod(index, len(route_cycle))
        route_id = route_cycle[cycle_index]
        departure = wave_index * wave_spacing + depart_offsets[cycle_index]
        if jitter:
            departure += rnd.randint(0, jitter)

        incoming_approach = route_id.split("_", 1)[0]
        previous_departure = last_departure_by_approach.get(incoming_approach)
        if previous_departure is not None and departure <= previous_departure:
            departure = previous_departure + 1
        last_departure_by_approach[incoming_approach] = departure
        demand.append((departure, index, route_id))

    demand.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in demand], [item[0] for item in demand]


def _initial_demand_signature(
    *,
    scenario_name: str,
    seed: int,
    route_ids: list[str],
    departure_times: list[int],
) -> str:
    payload = json.dumps(
        {
            "scenario_name": scenario_name,
            "seed": int(seed),
            "route_ids": route_ids,
            "departure_times": departure_times,
            "car_following_sigma": CAR_FOLLOWING_SIGMA,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def _write_scenario(
    *,
    scenario_id: str,
    density_name: str,
    seed: int,
    route_ids: list[str],
    departure_times: list[int],
    duration: int,
    vehicles_per_hour: int,
    extra_config: dict | None = None,
) -> dict:
    if len(route_ids) != len(departure_times):
        raise ValueError("Route and departure sequences must have equal length")

    supported_routes = set(supported_route_ids())
    unsupported_routes = sorted(set(route_ids) - supported_routes)
    if unsupported_routes:
        raise ValueError(f"Unsupported route id for scenario generation: {unsupported_routes[0]}")

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
            "sigma": str(CAR_FOLLOWING_SIGMA),
            "length": "5",
            "maxSpeed": str(CONFIG["max_speed"]),
        },
    )
    unique_route_ids = list(dict.fromkeys(route_ids))
    for route_id in unique_route_ids:
        edge_a, edge_b = route_edges_for_route_id(route_id)
        ET.SubElement(root, "route", attrib={"id": route_id, "edges": f"{edge_a} {edge_b}"})

    for index, (route_id, departure) in enumerate(zip(route_ids, departure_times)):
        ET.SubElement(
            root,
            "vehicle",
            attrib={
                "id": f"{scenario_id}_{seed}_{index}",
                "type": "car",
                "route": route_id,
                "depart": str(departure),
                "departLane": "best",
            },
        )

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
        "vehicle_count": len(route_ids),
        "vehicles_per_hour": vehicles_per_hour,
        "simulation_duration_seconds": duration,
        "total_vehicles": len(route_ids),
        "route_sequence": route_ids,
        "departure_times": departure_times,
        "sumocfg_path": str(scenario_sumocfg),
        **(extra_config or {}),
    }
    (out_dir / "generation_config.json").write_text(json.dumps(generation_config, indent=2), encoding="utf-8")
    (out_dir / "generation_manifest.json").write_text(
        json.dumps(
            {
                "routes_file": str(routes_path),
                "route_count": len(route_ids),
                "route_ids": unique_route_ids,
                "vehicle_count": len(route_ids),
                "seed": seed,
                "scenario_id": scenario_id,
                "sumocfg_path": str(scenario_sumocfg),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return generation_config


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
    min_gap = int(density["minimum_depart_gap"])
    max_gap = int(density["maximum_depart_gap"])
    route_ids = _route_sequence(density["route_distribution"], total_vehicles, seed)
    departures = _departure_times(total_vehicles, seed, min_gap, max_gap)
    return _write_scenario(
        scenario_id=scenario_id,
        density_name=density_name,
        seed=seed,
        route_ids=route_ids,
        departure_times=departures,
        duration=duration,
        vehicles_per_hour=vehicles_per_hour,
    )


def generate_targeted_scenario(
    scenario_id: str,
    scenario_name: str,
    seed: int,
    vehicle_count: int = 8,
) -> dict:
    experiment_matrix = load_experiment_matrix()
    try:
        definition = experiment_matrix["targeted_scenarios"][scenario_name]
    except KeyError as exc:
        raise ValueError(f"Unknown targeted scenario: {scenario_name}") from exc

    route_ids, departures = _targeted_demand(definition, seed, int(vehicle_count))
    duration = max(
        int(definition.get("simulation_duration_seconds", 300)),
        (max(departures) if departures else 0) + 180,
    )
    movement_sequence = [
        next(route.movement for route in supported_route_catalog() if route.route_id == route_id)
        for route_id in route_ids
    ]
    departure_jitter_seconds = int(definition.get("departure_jitter_seconds", 0))
    return _write_scenario(
        scenario_id=scenario_id,
        density_name="targeted",
        seed=seed,
        route_ids=route_ids,
        departure_times=departures,
        duration=duration,
        vehicles_per_hour=0,
        extra_config={
            "scenario_class": scenario_name,
            "purpose": definition.get("purpose", ""),
            "movement_sequence": movement_sequence,
            "fairness_target_route": definition.get("fairness_target_route", ""),
            "intended_waiting_pressure_seconds": int(definition.get("intended_waiting_pressure_seconds", 0)),
            "initial_demand_signature": _initial_demand_signature(
                scenario_name=scenario_name,
                seed=seed,
                route_ids=route_ids,
                departure_times=departures,
            ),
            "seed_semantics": {
                "route_assignment_changes": False,
                "departure_timing_changes": departure_jitter_seconds > 0,
                "departure_jitter_seconds": departure_jitter_seconds,
                "sumo_car_following_changes": True,
                "sumo_car_following_sigma": CAR_FOLLOWING_SIGMA,
            },
        },
    )
