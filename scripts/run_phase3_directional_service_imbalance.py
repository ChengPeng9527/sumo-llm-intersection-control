"""Manual staged runner for the final Q3 service-imbalance extension."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common import resolve_llm_api_key
from src.controllers.candidate_runtime import GEMINI_CANDIDATE
from src.experiments.phase2_closed_loop import initial_condition_record, run_phase2_closed_loop_episode
from src.llm.diagnostics import redact_sensitive_text
from src.experiments.phase3_directional_service_imbalance import (
    CONDITION,
    EXTENSION_ID,
    STAGE1,
    STAGE2,
    build_plan,
    classify_benefit,
    copy_result_artifacts,
    prepare_demand,
    require_stage2_authorization,
    results_root,
    stage1_feasibility,
    valid_gemini_observation,
    verify_matched_initial_conditions,
    write_observer_output,
)


def _git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


_SENSITIVE_FIELD_NAMES = {
    "api_key", "authorization", "credential", "secret", "access_token", "refresh_token",
}


def _sanitize_evidence(value, *, secrets: tuple[str, ...] = ()):
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if str(key).lower() in _SENSITIVE_FIELD_NAMES else _sanitize_evidence(item, secrets=secrets)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize_evidence(item, secrets=secrets) for item in value]
    if isinstance(value, str):
        sanitized = redact_sensitive_text(value)
        for secret in secrets:
            if secret:
                sanitized = sanitized.replace(secret, "[REDACTED]")
        return sanitized
    return value


def _candidate_ids_from_decision(decision: dict) -> list[str]:
    ranking_ids = [
        str(item.get("candidate_id", ""))
        for item in decision.get("candidate_ranking", ())
        if isinstance(item, dict) and item.get("candidate_id")
    ]
    if ranking_ids:
        return ranking_ids
    candidate_ids = []
    for group in decision.get("candidate_groups", ()):
        if isinstance(group, dict) and group.get("candidate_id"):
            candidate_ids.append(str(group["candidate_id"]))
        elif isinstance(group, (list, tuple)):
            candidate_ids.append("|".join(str(vehicle_id) for vehicle_id in group))
    return candidate_ids


def _persist_failure(
    output: Path,
    *,
    spec,
    generation: dict,
    error: Exception,
    api_key: str,
) -> None:
    output.mkdir(parents=True, exist_ok=False)
    initial = initial_condition_record(generation)
    decision = dict(getattr(error, "decision_record", {}) or {})
    candidate_ids = _candidate_ids_from_decision(decision)
    selected_candidate_id = str(
        decision.get("final_selected_candidate", decision.get("selected_candidate_id", ""))
    )
    required_defaults = {
        "provider_request_success": False,
        "provider_failure_reason": "",
        "exception_type": "",
        "exception_message_redacted": "",
        "http_status": None,
        "parser_success": False,
        "parser_failure_reason": "",
        "fallback_used": False,
        "latency_ms": None,
        "llm_raw_output": "",
        "response_content_redacted": "",
    }
    for field, default in required_defaults.items():
        decision.setdefault(field, default)
    decision.update({
        "scenario": generation["scenario_id"],
        "condition": spec.condition,
        "seed": spec.seed,
        "planner": spec.planner_mode,
        "run_id": spec.run_id,
        "candidate_ids": candidate_ids,
        "selected_candidate_id": selected_candidate_id,
        "selected_candidate_is_legal": (
            selected_candidate_id in candidate_ids if selected_candidate_id and candidate_ids else None
        ),
        "strict_valid": False,
        "failure_reason": decision.get("failure_reason") or str(error),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "llm_episode_valid": False,
    })
    failure = {
        "scenario": generation["scenario_id"],
        "condition": spec.condition,
        "seed": spec.seed,
        "planner": spec.planner_mode,
        "run_id": spec.run_id,
        "status": "INVALID",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "llm_episode_valid": False,
        "initial_conditions": initial,
        "failure_decision_path": str(output / "failure_decision.json"),
    }
    secrets = (api_key,)
    _write_json(output / "failure_decision.json", _sanitize_evidence(decision, secrets=secrets))
    _write_json(output / "failure.json", _sanitize_evidence(failure, secrets=secrets))


def _verify_stage2_generation(spec, generation: dict, expected_initial_conditions: dict[int, dict]) -> None:
    if spec.planner_mode != GEMINI_CANDIDATE:
        raise RuntimeError("Stage 2 may contain only GEMINI_CANDIDATE runs")
    actual = initial_condition_record(generation)
    expected = expected_initial_conditions.get(spec.seed)
    if expected is None:
        raise RuntimeError(f"missing_stage1_initial_conditions:seed{spec.seed}")
    if actual["scenario_class"] != CONDITION or actual["vehicle_count"] != 16 or actual["seed"] != spec.seed:
        raise RuntimeError(f"stage2_generation_contract_mismatch:seed{spec.seed}")
    if actual["initial_demand_signature"] != expected.get("initial_demand_signature"):
        raise RuntimeError(f"matched_initial_demand_signature_mismatch:seed{spec.seed}")


def stage2_exit_code(stage2_manifest: dict) -> int:
    return 0 if stage2_manifest.get("status") == "completed" else 1


def _new_manifest(stage: str) -> dict:
    return {
        "extension_id": EXTENSION_ID,
        "condition": CONDITION,
        "stage": stage,
        "created_at_unix": time.time(),
        "branch": _git_output("branch", "--show-current"),
        "execution_commit": _git_output("rev-parse", "HEAD"),
        "status": "running",
        "runs": [],
    }


def _ensure_stage1_namespace_is_new(root: Path) -> None:
    if root.exists():
        raise FileExistsError(f"Refusing to overwrite existing Q3 evidence root: {root}")


def run_specs(
    root: Path,
    stage: str,
    *,
    api_key: str = "",
    demand_factory: Callable[[int], dict] = prepare_demand,
    episode_runner: Callable[..., dict] = run_phase2_closed_loop_episode,
    artifact_copier: Callable[[dict, Path], None] = copy_result_artifacts,
    observer_writer: Callable[[Path, dict, list[str]], dict] = write_observer_output,
    expected_initial_conditions: dict[int, dict] | None = None,
) -> list[dict]:
    manifest_path = root / f"{stage}_manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"Stage already has a manifest: {manifest_path}")
    manifest = _new_manifest(stage)
    _write_json(manifest_path, manifest)
    observations: list[dict] = []
    failures = 0
    for spec in build_plan(stage):
        generation = demand_factory(spec.seed)
        output = root / "runs" / spec.run_id
        if output.exists():
            raise FileExistsError(f"Run evidence already exists: {output}")
        if stage == STAGE2:
            _verify_stage2_generation(spec, generation, expected_initial_conditions or {})
        try:
            result = episode_runner(
                generation,
                planner_mode=spec.planner_mode,
                api_key=api_key if spec.planner_mode == GEMINI_CANDIDATE else "",
                grant_timeout_seconds=45.0,
                strict_llm_mode=spec.planner_mode == GEMINI_CANDIDATE,
                run_label=EXTENSION_ID,
            )
            artifact_copier(result, output)
            observation = observer_writer(
                output / "directional_service_observer.json",
                result,
                list(generation["target_smaller_vehicle_ids"]),
            )
            observation.update({
                "condition": spec.condition,
                "seed": spec.seed,
                "planner": spec.planner_mode,
            })
            _write_json(output / "directional_service_observer.json", observation)
            status = "valid" if spec.planner_mode != GEMINI_CANDIDATE or valid_gemini_observation(observation) else "invalid_llm"
            manifest["runs"].append({
                "run_id": spec.run_id,
                "condition": spec.condition,
                "seed": spec.seed,
                "planner": spec.planner_mode,
                "status": status,
                "initial_conditions": initial_condition_record(generation),
                "target_smaller_vehicle_ids": generation["target_smaller_vehicle_ids"],
                "output": str(output),
            })
            observations.append(observation)
        except Exception as error:
            failures += 1
            _persist_failure(
                output,
                spec=spec,
                generation=generation,
                error=error,
                api_key=api_key,
            )
            manifest["runs"].append({
                "run_id": spec.run_id,
                "condition": spec.condition,
                "seed": spec.seed,
                "planner": spec.planner_mode,
                "status": "invalid",
                "error_type": type(error).__name__,
                "error": _sanitize_evidence(str(error), secrets=(api_key,)),
                "llm_episode_valid": False,
                "initial_conditions": initial_condition_record(generation),
                "target_smaller_vehicle_ids": generation["target_smaller_vehicle_ids"],
                "output": str(output),
            })
            _write_json(manifest_path, manifest)
            if stage == STAGE1:
                manifest["status"] = "invalid"
                _write_json(manifest_path, manifest)
                raise
            # Stage 2 has no replacement runs. Continue to preserve the fixed matrix.
        _write_json(manifest_path, manifest)
    manifest["status"] = "invalid" if failures else "completed"
    manifest["invalid_episode_count"] = failures
    _write_json(manifest_path, manifest)
    return observations


def run_stage(stage: str, *, authorize_stage2: bool) -> int:
    root = results_root()
    if stage == STAGE1:
        _ensure_stage1_namespace_is_new(root)
        observations = run_specs(root, STAGE1)
        report = stage1_feasibility(observations)
        report["stage"] = STAGE1
        report["run_count"] = len(observations)
        _write_json(root / "stage1_feasibility_report.json", report)
        print(f"[DIRECTIONAL STRESS STAGE1 COMPLETE] gate={report['stage1_gate_passed']}", flush=True)
        return 0

    stage1_report_path = root / "stage1_feasibility_report.json"
    if not stage1_report_path.is_file():
        raise FileNotFoundError("Stage 1 feasibility report is required")
    stage1_report = json.loads(stage1_report_path.read_text(encoding="utf-8"))
    require_stage2_authorization(stage1_report, authorize_stage2)
    stage1_manifest = json.loads((root / f"{STAGE1}_manifest.json").read_text(encoding="utf-8"))
    expected_initial_conditions = {
        int(row["seed"]): dict(row["initial_conditions"])
        for row in stage1_manifest["runs"]
        if row.get("status") == "valid"
    }
    api_key = resolve_llm_api_key("Gemini")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for the separately authorized Stage 2")
    stage2_observations = run_specs(
        root,
        STAGE2,
        api_key=api_key,
        expected_initial_conditions=expected_initial_conditions,
    )
    stage2_manifest = json.loads((root / f"{STAGE2}_manifest.json").read_text(encoding="utf-8"))
    verify_matched_initial_conditions(stage1_manifest, stage2_manifest)
    stage1_observations = [
        json.loads((Path(row["output"]) / "directional_service_observer.json").read_text(encoding="utf-8"))
        for row in stage1_manifest["runs"]
        if row.get("status") == "valid"
    ]
    report = classify_benefit(stage1_observations + stage2_observations)
    report.update({
        "total_gemini_episodes": 3,
        "valid_gemini_episodes": sum(valid_gemini_observation(item) for item in stage2_observations),
        "invalid_gemini_episodes": 3 - sum(valid_gemini_observation(item) for item in stage2_observations),
        "excluded_gemini_episodes": 3 - sum(valid_gemini_observation(item) for item in stage2_observations),
        "stopping_rule": "STOP_SUPPLEMENTARY_EXPERIMENTS_AFTER_STAGE2",
        "stage2_status": stage2_manifest["status"],
    })
    _write_json(root / "stage2_descriptive_comparison.json", report)
    exit_code = stage2_exit_code(stage2_manifest)
    if exit_code:
        print("[DIRECTIONAL STRESS STAGE2 INVALID]", flush=True)
        return exit_code
    print("[DIRECTIONAL STRESS STAGE2 COMPLETE]", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=(STAGE1, STAGE2))
    parser.add_argument(
        "--authorize-stage2",
        action="store_true",
        help="New human authorization after a reviewed passing Stage 1 gate.",
    )
    args = parser.parse_args(argv)
    return run_stage(args.stage, authorize_stage2=args.authorize_stage2)


if __name__ == "__main__":
    raise SystemExit(main())
