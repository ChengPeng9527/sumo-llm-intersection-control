from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import load_project_config
from src.experiments.counterfactual_replay import DEFAULT_OUTPUT_ROOT, RealSumoReplayRunner


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic real-SUMO replay-equivalence validation")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--simulation-steps", type=int, default=480)
    args = parser.parse_args()
    config = load_project_config()
    print("[REPLAY EQUIVALENCE START]", flush=True)
    print("[PATH A REFERENCE]", flush=True)
    runner = RealSumoReplayRunner(sumo_binary=Path(config["sumo_binary_path"]), output_root=args.output_root)
    result = runner.run(simulation_steps=args.simulation_steps)
    print(f"[{result['gate']}]", flush=True)
    return 0 if result["gate"] == "REPLAY_EQUIVALENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
