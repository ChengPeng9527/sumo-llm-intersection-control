from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import load_project_config
from src.experiments.counterfactual_branches import DEFAULT_OUTPUT_ROOT, SameStateCounterfactualRunner


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run six preregistered same-state S3 R4/S2 counterfactual continuations"
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--simulation-steps", type=int, default=480)
    args = parser.parse_args()
    config = load_project_config()
    print("[COUNTERFACTUAL START]", flush=True)
    print("[SEEDS 1-3: R4/S2]", flush=True)
    runner = SameStateCounterfactualRunner(
        sumo_binary=Path(config["sumo_binary_path"]), output_root=args.output_root
    )
    result = runner.run(simulation_steps=args.simulation_steps)
    print(f"[COUNTERFACTUAL {result['interpretation']}]", flush=True)
    print("[COUNTERFACTUAL DONE]", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
