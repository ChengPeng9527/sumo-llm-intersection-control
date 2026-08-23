from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common import resolve_llm_api_key
from src.common.metrics import run_artifact_paths
from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.experiments.phase2_closed_loop import (
    prepare_phase2_targeted_demand,
    run_phase2_closed_loop_episode,
)
from src.experiments.phase2_formal_batch import (
    FORMAL_BATCH_ID,
    FORMAL_RESULTS_ROOT,
    FORMAL_RUN_LABEL,
    build_paired_comparison,
    build_phase2_formal_batch_plan,
    copy_formal_run_artifacts,
    extract_disagreements,
    formal_run_target,
    summarize_formal_run,
    validate_formal_pair,
    validate_formal_run_result,
    write_csv,
    write_json,
)


def _git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> int:
    if FORMAL_RESULTS_ROOT.exists():
        raise FileExistsError(f"Formal batch directory already exists: {FORMAL_RESULTS_ROOT}")

    api_key = resolve_llm_api_key("Gemini")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for the formal Gemini runs")

    plan = build_phase2_formal_batch_plan()
    manifest = {
        "batch_id": FORMAL_BATCH_ID,
        "formal": True,
        "freeze_commit": _git_output("rev-parse", "HEAD"),
        "branch": _git_output("branch", "--show-current"),
        "created_at_unix": time.time(),
        "status": "running",
        "runs": [
            {
                "order": spec.order,
                "scenario_class": spec.scenario_class,
                "vehicle_count": spec.vehicle_count,
                "seed": spec.seed,
                "planner_mode": spec.planner_mode,
                "run_id": spec.run_id,
                "formal_target": str(formal_run_target(spec)),
                "status": "planned",
                "reason": "",
            }
            for spec in plan
        ],
    }
    write_json(FORMAL_RESULTS_ROOT / "run_manifest.json", manifest)

    completed_results: list[dict] = []
    run_summaries: list[dict] = []
    for scenario_class in dict.fromkeys(spec.scenario_class for spec in plan):
        pair_specs = [spec for spec in plan if spec.scenario_class == scenario_class]
        generation = prepare_phase2_targeted_demand(
            scenario_class,
            vehicle_count=pair_specs[0].vehicle_count,
            seed=pair_specs[0].seed,
        )
        pair_results: dict[str, dict] = {}

        for spec in pair_specs:
            row = manifest["runs"][spec.order - 1]
            raw_target = run_artifact_paths(spec.run_id)["run_dir"]
            formal_target = formal_run_target(spec)
            if raw_target.exists() or formal_target.exists():
                row["status"] = "blocked_existing_output"
                row["reason"] = "raw_or_formal_target_already_exists"
                manifest["status"] = "invalid"
                write_json(FORMAL_RESULTS_ROOT / "run_manifest.json", manifest)
                raise FileExistsError(f"Refusing to overwrite formal output for {spec.run_id}")

            row["status"] = "running"
            write_json(FORMAL_RESULTS_ROOT / "run_manifest.json", manifest)
            try:
                result = run_phase2_closed_loop_episode(
                    generation,
                    planner_mode=spec.planner_mode,
                    api_key=api_key if spec.planner_mode == GEMINI_CANDIDATE else "",
                    grant_timeout_seconds=45.0,
                    run_label=FORMAL_RUN_LABEL,
                )
                validation_errors = validate_formal_run_result(result, spec)
                if validation_errors:
                    raise RuntimeError("formal_run_validation_failed:" + ";".join(validation_errors))
                copy_formal_run_artifacts(
                    Path(result["artifact_paths"]["run_dir"]),
                    formal_target,
                )
                write_json(
                    formal_target / "formal_validation.json",
                    {
                        "valid": True,
                        "validation_errors": [],
                        "initial_conditions": result["initial_conditions"],
                        "planner_mode": spec.planner_mode,
                        "source_run_dir": result["artifact_paths"]["run_dir"],
                    },
                )
            except Exception as exc:
                row["status"] = "invalid"
                row["reason"] = f"{type(exc).__name__}:{exc}"
                manifest["status"] = "invalid"
                write_json(FORMAL_RESULTS_ROOT / "run_manifest.json", manifest)
                raise

            row["status"] = "completed_valid"
            row["reason"] = ""
            row["initial_demand_signature"] = result["initial_conditions"]["initial_demand_signature"]
            row["raw_results_path"] = result["artifact_paths"]["run_dir"]
            row["formal_results_path"] = str(formal_target)
            write_json(FORMAL_RESULTS_ROOT / "run_manifest.json", manifest)
            pair_results[spec.planner_mode] = result
            completed_results.append(result)
            run_summaries.append(summarize_formal_run(result))

        pair_errors = validate_formal_pair(
            pair_results[DETERMINISTIC_CANDIDATE],
            pair_results[GEMINI_CANDIDATE],
        )
        if pair_errors:
            manifest["status"] = "invalid"
            manifest["pair_validation_error"] = {
                "scenario_class": scenario_class,
                "errors": pair_errors,
            }
            write_json(FORMAL_RESULTS_ROOT / "run_manifest.json", manifest)
            raise RuntimeError("formal_pair_validation_failed:" + ";".join(pair_errors))

    paired_comparison = build_paired_comparison(run_summaries)
    disagreements = extract_disagreements(completed_results)
    manifest["status"] = "completed_valid"
    manifest["completed_at_unix"] = time.time()
    write_json(FORMAL_RESULTS_ROOT / "run_manifest.json", manifest)
    write_json(FORMAL_RESULTS_ROOT / "run_summaries.json", run_summaries)
    write_csv(FORMAL_RESULTS_ROOT / "run_summaries.csv", run_summaries)
    write_json(FORMAL_RESULTS_ROOT / "paired_comparison.json", paired_comparison)
    write_csv(FORMAL_RESULTS_ROOT / "paired_comparison.csv", paired_comparison)
    write_json(FORMAL_RESULTS_ROOT / "disagreements.json", disagreements)
    write_json(
        FORMAL_RESULTS_ROOT / "batch_summary.json",
        {
            "batch_id": FORMAL_BATCH_ID,
            "status": "FORMAL_BATCH_VALID",
            "run_count": len(run_summaries),
            "pair_count": len(paired_comparison),
            "gemini_request_count": sum(row["gemini_request_count"] for row in run_summaries),
            "provider_success_count": sum(row["provider_success_count"] for row in run_summaries),
            "parser_success_count": sum(row["parser_success_count"] for row in run_summaries),
            "fallback_count": sum(row["fallback_count"] for row in run_summaries),
            "agreement_count": sum(row["agreement_count"] for row in run_summaries),
            "disagreement_count": sum(row["disagreement_count"] for row in run_summaries),
            "prompt_tokens": sum(row["prompt_tokens"] for row in run_summaries),
            "completion_tokens": sum(row["completion_tokens"] for row in run_summaries),
            "total_tokens": sum(row["total_tokens"] for row in run_summaries),
            "safety_intervention_count": sum(row["safety_intervention_count"] for row in run_summaries),
            "grant_timeout_count": sum(row["grant_timeout_count"] for row in run_summaries),
        },
    )
    print(
        json.dumps(
            {
                "formal_results_root": str(FORMAL_RESULTS_ROOT),
                "run_count": len(run_summaries),
                "pair_count": len(paired_comparison),
                "gemini_request_count": sum(row["gemini_request_count"] for row in run_summaries),
                "disagreement_count": len(disagreements),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
