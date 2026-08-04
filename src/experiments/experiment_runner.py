from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
from pathlib import Path

from src.common.config import load_project_config, load_yaml_config
from src.experiments.scenario_generator import generate_scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--controller",
        choices=["baseline", "cooperative", "cooperative_rule", "llm", "raw_llm", "hybrid_llm", "hybrid_llm_safety"],
        default=None,
    )
    parser.add_argument("--density", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--vehicle-count", type=int, default=None)
    parser.add_argument("--vehicle-counts", nargs="*", type=int, default=None)
    parser.add_argument("--llm-mode", choices=["mock", "real"], default="mock")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-runs", type=int, default=0)
    args = parser.parse_args(argv)

    project = load_project_config()
    root = Path(project["project_root"])
    matrix = load_yaml_config("experiment_matrix.yaml")

    controllers = matrix["controllers"]
    densities = list(matrix["densities"].keys())
    seeds = matrix["seeds"]
    configured_vehicle_counts = matrix.get("vehicle_counts", [4])

    if args.controller is not None:
        controllers = [args.controller]
    if args.density is not None:
        densities = [args.density]
    if args.seed is not None:
        seeds = [args.seed]
    if args.vehicle_counts:
        vehicle_counts = list(args.vehicle_counts)
    elif args.vehicle_count is not None:
        vehicle_counts = [args.vehicle_count]
    else:
        vehicle_counts = [configured_vehicle_counts[0] if configured_vehicle_counts else 4]

    runs = list(itertools.product(controllers, densities, seeds, vehicle_counts))
    if args.max_runs:
        runs = runs[: args.max_runs]

    manifest_rows = []
    if args.dry_run:
        for controller, density, seed, vehicle_count in runs:
            scenario_id = f"{density}_v{vehicle_count}_seed{seed}"
            entry = {
                "controller": controller,
                "density": density,
                "seed": seed,
                "vehicle_count": vehicle_count,
                "scenario_id": scenario_id,
                "llm_mode": args.llm_mode if controller == "llm" else "",
            }
            manifest_rows.append(entry)
            print(entry)
        manifest_path = root / "results" / "run_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest_rows, indent=2), encoding="utf-8")
        return 0

    controller_script_map = {
        "baseline": root / "baseline_controller.py",
        "cooperative": root / "cooperative_controller.py",
        "cooperative_rule": root / "cooperative_controller.py",
        "llm": root / "llm_controller.py",
        "raw_llm": root / "raw_llm_controller.py",
        "hybrid_llm": root / "hybrid_llm_controller.py",
        "hybrid_llm_safety": root / "hybrid_llm_safety_controller.py",
    }

    for controller, density, seed, vehicle_count in runs:
        scenario_id = f"{density}_v{vehicle_count}_seed{seed}"
        scenario_config = generate_scenario(scenario_id, density, seed, vehicle_count=vehicle_count)
        controller_script = controller_script_map.get(controller, root / f"{controller}_controller.py")
        launch_env = os.environ.copy()
        launch_env["SCENARIO_ID"] = scenario_id
        launch_env["VEHICLE_COUNT"] = str(vehicle_count)
        launch_env["SUMO_CONFIG_PATH"] = scenario_config["sumocfg_path"]
        launch_env["SIMULATION_STEPS"] = str(scenario_config["simulation_duration_seconds"])
        if controller == "llm":
            launch_env["LLM_MODE"] = args.llm_mode
        manifest_rows.append(
            {
                "controller": controller,
                "density": density,
                "seed": seed,
                "vehicle_count": vehicle_count,
                "scenario_id": scenario_id,
                "controller_script": str(controller_script),
                "scenario_config": scenario_config,
                "sumocfg_path": scenario_config["sumocfg_path"],
                "llm_mode": args.llm_mode if controller == "llm" else "",
            }
        )
        subprocess.run([sys.executable, str(controller_script)], check=True, env=launch_env)

    manifest_path = root / "results" / "run_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest_rows, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
