from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common import resolve_llm_api_key
from src.experiments.phase2_targeted_pilot import (
    run_deterministic_suite,
    run_live_representative_pilot,
    summarize_live_results,
)
from src.llm.request_config import PHASE2_MODEL, PHASE2_PROVIDER_NAME


DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "research" / "phase2_step7_pilot_results.json"


def _json_safe(value):
    if isinstance(value, float) and (value != value or value in {float("inf"), float("-inf")}):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    deterministic_runs = run_deterministic_suite(seed=args.seed)
    live_results: list[dict] = []
    if args.live:
        api_key = resolve_llm_api_key("Gemini")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required for --live")
        live_results = run_live_representative_pilot(deterministic_runs, api_key=api_key)

    result = {
        "step": "PHASE2_STEP7",
        "seed": args.seed,
        "provider": PHASE2_PROVIDER_NAME if args.live else "",
        "model": PHASE2_MODEL if args.live else "",
        "deterministic_runs": deterministic_runs,
        "live_results": live_results,
        "live_summary": summarize_live_results(live_results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(_json_safe(result), indent=2, allow_nan=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "deterministic_run_count": len(deterministic_runs),
                "live_request_count": len(live_results),
                "live_summary": result["live_summary"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
