from __future__ import annotations

import argparse
import itertools
import subprocess
import sys
from pathlib import Path

import yaml

from src.common.config import load_project_config
from src.experiments.scenario_generator import generate_scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
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

    runs = list(itertools.product(controllers, densities, seeds))
    if args.max_runs:
        runs = runs[: args.max_runs]

    if args.dry_run:
        for controller, density, seed in runs:
            scenario_id = f"{density}_{seed}"
            print({"controller": controller, "density": density, "seed": seed, "scenario_id": scenario_id})
        return 0

    for controller, density, seed in runs:
        scenario_id = f"{density}_{seed}"
        generate_scenario(scenario_id, density, seed)
        controller_script = root / f"{controller}_controller.py"
        subprocess.run([sys.executable, str(controller_script)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
