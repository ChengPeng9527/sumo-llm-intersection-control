from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common import resolve_llm_api_key
from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.experiments.phase2_closed_loop import (
    prepare_phase2_targeted_demand,
    run_phase2_closed_loop_episode,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--planner",
        choices=("deterministic", "gemini"),
        default="deterministic",
    )
    parser.add_argument("--scenario", default="S3_COOPERATIVE_OPPORTUNITY")
    parser.add_argument("--vehicle-count", type=int, default=8)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--grant-timeout", type=float, default=45.0)
    parser.add_argument("--max-gemini-requests", type=int, default=0)
    args = parser.parse_args(argv)

    planner_mode = GEMINI_CANDIDATE if args.planner == "gemini" else DETERMINISTIC_CANDIDATE
    api_key = resolve_llm_api_key("Gemini") if planner_mode == GEMINI_CANDIDATE else ""
    if planner_mode == GEMINI_CANDIDATE and not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for Gemini candidate mode")

    generation = prepare_phase2_targeted_demand(
        args.scenario,
        vehicle_count=args.vehicle_count,
        seed=args.seed,
    )
    result = run_phase2_closed_loop_episode(
        generation,
        planner_mode=planner_mode,
        api_key=api_key,
        grant_timeout_seconds=args.grant_timeout,
        max_gemini_requests=args.max_gemini_requests,
    )
    print(
        json.dumps(
            {
                "run_id": result["run_id"],
                "initial_conditions": result["initial_conditions"],
                "summary": result["summary"],
                "artifact_paths": result["artifact_paths"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
