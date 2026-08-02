from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path

import yaml

from src.common.config import load_project_config
from src.experiments.scenario_generator import generate_scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controller", choices=["baseline", "cooperative"], default=None)
    parser.add_argument("--density", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-runs", type=int, default=0)
    args = parser.parse_args(argv)

    project = load_project_config()
    root = Path(project["project_root"])
    matrix_path = root / "config" / "experiment_matrix.yaml"
    with matrix_path.open("r", encoding="utf-8") as f:
        matrix = yaml.safe_load(f)

    controllers = matrix["controllers"]
    densities = list(matrix["densities"].keys())
    seeds = matrix["seeds"]

    if args.controller is not None:
        controllers = [args.controller]
    if args.density is not None:
        densities = [args.density]
    if args.seed is not None:
        seeds = [args.seed]

    runs = list(itertools.product(controllers, densities, seeds))
    if args.max_runs:
        runs = runs[: args.max_runs]

    manifest_rows = []
    if args.dry_run:
        for controller, density, seed in runs:
            scenario_id = f"{density}_{seed}"
            entry = {"controller": controller, "density": density, "seed": seed, "scenario_id": scenario_id}
            manifest_rows.append(entry)
            print(entry)
        manifest_path = root / "results" / "run_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest_rows, indent=2), encoding="utf-8")
        return 0

    for controller, density, seed in runs:
        scenario_id = f"{density}_{seed}"
        scenario_config = generate_scenario(scenario_id, density, seed)
        controller_script = root / f"{controller}_controller.py"
        manifest_rows.append(
            {
                "controller": controller,
                "density": density,
                "seed": seed,
                "scenario_id": scenario_id,
                "controller_script": str(controller_script),
                "scenario_config": scenario_config,
            }
        )
        subprocess.run([sys.executable, str(controller_script)], check=True)

    manifest_path = root / "results" / "run_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest_rows, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
