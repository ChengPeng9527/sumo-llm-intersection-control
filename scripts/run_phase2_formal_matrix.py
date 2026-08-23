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
from src.experiments.phase2_formal_batch import copy_formal_run_artifacts, write_json
from src.experiments.phase2_formal_matrix import (
    BATCH1_RESULTS_ROOT,
    FORMAL_MATRIX_BATCH_ID,
    FORMAL_MATRIX_RESULTS_ROOT,
    FORMAL_MATRIX_RUN_LABEL,
    build_remaining_matrix_plan,
    load_completed_batch,
    matrix_run_target,
    validate_formal_pair,
    validate_persisted_formal_run,
    write_complete_matrix_summaries,
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


def _record_manifest(path: Path, manifest: dict) -> None:
    write_json(path / "run_manifest.json", manifest)


def main() -> int:
    if FORMAL_MATRIX_RESULTS_ROOT.exists():
        raise FileExistsError(f"Formal matrix output already exists: {FORMAL_MATRIX_RESULTS_ROOT}")
    batch1_manifest, _ = load_completed_batch(BATCH1_RESULTS_ROOT)
    if len(batch1_manifest["runs"]) != 6:
        raise RuntimeError("Batch 1 does not contain exactly six frozen runs")

    api_key = resolve_llm_api_key("Gemini")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for the formal Gemini runs")
    plan = build_remaining_matrix_plan()
    if len(plan) != 30 or len({spec.run_id for spec in plan}) != 30:
        raise RuntimeError("Remaining formal matrix plan is not exactly 30 unique runs")
    batch1_ids = {row["run_id"] for row in batch1_manifest["runs"]}
    if batch1_ids & {spec.run_id for spec in plan}:
        raise RuntimeError("Remaining formal matrix reuses a Batch 1 run ID")

    manifest = {
        "batch_id": FORMAL_MATRIX_BATCH_ID,
        "formal": True,
        "freeze_commit": _git_output("rev-parse", "HEAD"),
        "branch": _git_output("branch", "--show-current"),
        "created_at_unix": time.time(),
        "status": "running",
        "request_volume_guard": "stop_before_next_gemini_episode_if_requests_exceed_two_per_vehicle",
        "runs": [
            {
                "order": spec.order,
                "scenario_class": spec.scenario_class,
                "vehicle_count": spec.vehicle_count,
                "seed": spec.seed,
                "planner_mode": spec.planner_mode,
                "run_id": spec.run_id,
                "formal_target": str(matrix_run_target(spec)),
                "status": "planned",
                "reason": "",
            }
            for spec in plan
        ],
    }
    _record_manifest(FORMAL_MATRIX_RESULTS_ROOT, manifest)

    completed_results: list[dict] = []
    for pair_id in dict.fromkeys(spec.pair_id for spec in plan):
        pair_specs = [spec for spec in plan if spec.pair_id == pair_id]
        generation = prepare_phase2_targeted_demand(
            pair_specs[0].scenario_class,
            vehicle_count=pair_specs[0].vehicle_count,
            seed=pair_specs[0].seed,
        )
        pair_results: dict[str, dict] = {}
        for spec in pair_specs:
            row = manifest["runs"][spec.order - 1]
            raw_target = run_artifact_paths(spec.run_id)["run_dir"]
            formal_target = matrix_run_target(spec)
            if raw_target.exists() or formal_target.exists():
                row["status"] = "blocked_existing_output"
                row["reason"] = "raw_or_formal_target_already_exists"
                manifest["status"] = "invalid"
                _record_manifest(FORMAL_MATRIX_RESULTS_ROOT, manifest)
                raise FileExistsError(f"Refusing to overwrite formal output for {spec.run_id}")
            row["status"] = "running"
            _record_manifest(FORMAL_MATRIX_RESULTS_ROOT, manifest)
            try:
                result = run_phase2_closed_loop_episode(
                    generation,
                    planner_mode=spec.planner_mode,
                    api_key=api_key if spec.planner_mode == GEMINI_CANDIDATE else "",
                    grant_timeout_seconds=45.0,
                    run_label=FORMAL_MATRIX_RUN_LABEL,
                )
                validation_errors = validate_persisted_formal_run(result, spec)
                if validation_errors:
                    raise RuntimeError("formal_run_validation_failed:" + ";".join(validation_errors))
                copy_formal_run_artifacts(Path(result["artifact_paths"]["run_dir"]), formal_target)
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
                _record_manifest(FORMAL_MATRIX_RESULTS_ROOT, manifest)
                raise

            row["status"] = "completed_valid"
            row["initial_demand_signature"] = result["initial_conditions"]["initial_demand_signature"]
            row["raw_results_path"] = result["artifact_paths"]["run_dir"]
            row["formal_results_path"] = str(formal_target)
            _record_manifest(FORMAL_MATRIX_RESULTS_ROOT, manifest)
            pair_results[spec.planner_mode] = result
            completed_results.append(result)

            if (
                spec.planner_mode == GEMINI_CANDIDATE
                and int(result["summary"].get("provider_request_count", 0)) > spec.vehicle_count * 2
            ):
                manifest["status"] = "stopped_request_volume_anomaly"
                manifest["request_volume_anomaly"] = {
                    "run_id": spec.run_id,
                    "request_count": result["summary"].get("provider_request_count", 0),
                    "threshold": spec.vehicle_count * 2,
                }
                _record_manifest(FORMAL_MATRIX_RESULTS_ROOT, manifest)
                raise RuntimeError("GEMINI_REQUEST_VOLUME_ANOMALY_STOPPED_BEFORE_NEXT_EPISODE")

        pair_errors = validate_formal_pair(
            pair_results[DETERMINISTIC_CANDIDATE],
            pair_results[GEMINI_CANDIDATE],
        )
        if pair_errors:
            manifest["status"] = "invalid"
            manifest["pair_validation_error"] = {"pair_id": pair_id, "errors": pair_errors}
            _record_manifest(FORMAL_MATRIX_RESULTS_ROOT, manifest)
            raise RuntimeError("formal_pair_validation_failed:" + ";".join(pair_errors))

    manifest["status"] = "completed_valid"
    manifest["completed_at_unix"] = time.time()
    _record_manifest(FORMAL_MATRIX_RESULTS_ROOT, manifest)
    _, batch1_results = load_completed_batch(BATCH1_RESULTS_ROOT)
    summary_root = FORMAL_MATRIX_RESULTS_ROOT / "complete_matrix_summary"
    summaries = write_complete_matrix_summaries(batch1_results + completed_results, summary_root)
    print(
        json.dumps(
            {
                "formal_results_root": str(FORMAL_MATRIX_RESULTS_ROOT),
                "remaining_run_count": len(completed_results),
                "complete_run_count": len(summaries["run_summaries"]),
                "complete_pair_count": len(summaries["paired_comparisons"]),
                "disagreement_count": len(summaries["disagreements"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
