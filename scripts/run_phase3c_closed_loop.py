"""Manually invoked, staged Phase 3C closed-loop runner.

It is intentionally not run by tests or by import.  Stage 2 is a separate
human-authorised command and cannot follow Stage 1 automatically.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common import resolve_llm_api_key
from src.controllers.candidate_runtime import GEMINI_CANDIDATE
from src.experiments.phase2_closed_loop import initial_condition_record, run_phase2_closed_loop_episode
from src.experiments.phase3c_closed_loop import (
    PHASE3C_ID,
    STAGE_DETERMINISTIC,
    STAGE_GEMINI,
    build_phase3c_plan,
    build_final_comparison,
    copy_result_artifacts,
    direct_connectivity_gate,
    phase3c_results_root,
    prepare_phase3c_demand,
    require_stage2_authorization,
    stage1_feasibility,
    write_observer_output,
)


def _git_output(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True).stdout.strip()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


_EXPERIMENT_ARTEFACT_NAMES = {
    "decision_records.jsonl", "summary.json", "step_records.csv", "run_metadata.json",
    "events.jsonl", "stage1_feasibility_report.json", "stage2_validity_report.json",
    "stage2_connectivity_gate.json", "final_comparison_table.json",
}


def inspect_stage1_output_root(root: Path) -> tuple[bool, str, dict | None]:
    """Allow only an empty root or the known pre-SUMO bootstrap failure.

    Any run directory, result artefact, or unfamiliar file is ambiguous
    provenance and must fail closed rather than being overwritten.
    """
    if not root.exists():
        return True, "root_absent", None
    files = [path for path in root.rglob("*") if path.is_file()]
    if any(path.name in _EXPERIMENT_ARTEFACT_NAMES for path in files) or (root / "runs").exists():
        return False, "formal_or_partial_experiment_evidence_present", None
    manifest_path = root / f"{STAGE_DETERMINISTIC}_manifest.json"
    if not files:
        return True, "empty_root", None
    if files != [manifest_path] or not manifest_path.is_file():
        return False, "unknown_root_contents", None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, "unreadable_bootstrap_manifest", None
    failed = manifest.get("failed_run", {})
    harmless = (
        manifest.get("extension_id") == PHASE3C_ID
        and manifest.get("stage") == STAGE_DETERMINISTIC
        and manifest.get("status") == "invalid"
        and manifest.get("runs") == []
        and failed.get("error_type") == "KeyError"
        and failed.get("error") == "'initial_demand_signature'"
    )
    return (True, "known_pre_sumo_bootstrap_failure", manifest) if harmless else (False, "ambiguous_stage1_manifest", None)


def initialize_stage1_output_root(root: Path) -> None:
    allowed, reason, manifest = inspect_stage1_output_root(root)
    if not allowed:
        raise FileExistsError(f"Refusing Phase 3C Stage 1 output root ({reason}): {root}")
    if manifest is not None:
        recovery_path = root / "initialization_recovery.json"
        if recovery_path.exists():
            raise FileExistsError(f"Existing initialization recovery record is ambiguous: {recovery_path}")
        _write_json(recovery_path, {
            "classification": reason,
            "preserved_bootstrap_manifest": manifest,
            "recovery_action": "permit a fresh Stage 1 manifest; no SUMO or Gemini artefact existed",
        })


def _manifest(root: Path, stage: str) -> dict:
    return {
        "extension_id": PHASE3C_ID,
        "stage": stage,
        "created_at_unix": time.time(),
        "branch": _git_output("branch", "--show-current"),
        "execution_commit": _git_output("rev-parse", "HEAD"),
        "status": "running",
        "runs": [],
    }


def _run_specs(root: Path, stage: str, api_key: str = "") -> list[dict]:
    observations: list[dict] = []
    manifest_path = root / f"{stage}_manifest.json"
    manifest = _manifest(root, stage)
    _write_json(manifest_path, manifest)
    for spec in build_phase3c_plan(stage):
        generation = prepare_phase3c_demand(spec.condition, spec.seed)
        output = root / "runs" / spec.pair_id / spec.run_id
        if output.exists():
            raise FileExistsError(f"Refusing to overwrite Phase 3C run: {output}")
        try:
            result = run_phase2_closed_loop_episode(
                generation,
                planner_mode=spec.planner_mode,
                api_key=api_key if spec.planner_mode == GEMINI_CANDIDATE else "",
                grant_timeout_seconds=45.0,
                strict_llm_mode=spec.planner_mode == GEMINI_CANDIDATE,
                run_label=PHASE3C_ID,
            )
        except Exception as error:
            manifest["status"] = "invalid"
            manifest["failed_run"] = {"run_id": spec.run_id, "error_type": type(error).__name__, "error": str(error)}
            _write_json(manifest_path, manifest)
            raise
        copy_result_artifacts(result, output)
        observation = write_observer_output(output / "phase3c_observer.json", result)
        observation.update({"condition": spec.condition.name, "seed": spec.seed, "planner": spec.planner_mode})
        _write_json(output / "phase3c_observer.json", observation)
        manifest["runs"].append({
            "condition": spec.condition.name,
            "seed": spec.seed,
            "planner_mode": spec.planner_mode,
            "run_id": spec.run_id,
            "initial_conditions": initial_condition_record(generation),
            "output": str(output),
        })
        _write_json(manifest_path, manifest)
        observations.append(observation)
    manifest["status"] = "completed"
    _write_json(manifest_path, manifest)
    return observations


def run_stage(stage: str, *, approve_stage1: bool) -> int:
    root = phase3c_results_root()
    if stage == STAGE_DETERMINISTIC:
        initialize_stage1_output_root(root)
        observations = _run_specs(root, stage)
        report = stage1_feasibility(observations)
        report["stage"] = stage
        report["run_count"] = len(observations)
        _write_json(root / "stage1_feasibility_report.json", report)
        print(f"[PHASE3C STAGE1 COMPLETE] gate={report['stage1_gate_passed']}")
        return 0

    report_path = root / "stage1_feasibility_report.json"
    if not report_path.is_file():
        raise FileNotFoundError("Stage 1 feasibility report is required before Stage 2")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    require_stage2_authorization(stage1_report=report, explicitly_approved=approve_stage1)
    api_key = resolve_llm_api_key("Gemini")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for Stage 2")
    gate = direct_connectivity_gate(api_key)
    _write_json(root / "stage2_connectivity_gate.json", gate)
    if not gate["passed"]:
        raise RuntimeError("STOP_PHASE3C: Stage 2 connectivity gate failed; no Gemini episode started")
    observations = _run_specs(root, stage, api_key)
    stage1_manifest = json.loads((root / f"{STAGE_DETERMINISTIC}_manifest.json").read_text(encoding="utf-8"))
    stage1_signatures = {
        (row["condition"], row["seed"]): row["initial_conditions"]["initial_demand_signature"]
        for row in stage1_manifest["runs"]
    }
    stage2_manifest = json.loads((root / f"{STAGE_GEMINI}_manifest.json").read_text(encoding="utf-8"))
    for row in stage2_manifest["runs"]:
        key = (row["condition"], row["seed"])
        if row["initial_conditions"]["initial_demand_signature"] != stage1_signatures.get(key):
            raise RuntimeError(f"paired_initial_demand_signature_mismatch:{key[0]}:seed{key[1]}")
    validity = {
        "stage": stage,
        "total_llm_episodes": len(observations),
        "valid_llm_episodes": sum(item.get("llm_episode_valid") is True for item in observations),
        "invalid_llm_episodes": sum(item.get("llm_episode_valid") is not True for item in observations),
    }
    validity["excluded_llm_episodes"] = validity["invalid_llm_episodes"]
    _write_json(root / "stage2_validity_report.json", validity)
    stage1_observations = []
    for row in stage1_manifest["runs"]:
        observer_path = Path(row["output"]) / "phase3c_observer.json"
        stage1_observations.append(json.loads(observer_path.read_text(encoding="utf-8")))
    _write_json(root / "final_comparison_table.json", {"rows": build_final_comparison(stage1_observations + observations)})
    print("[PHASE3C STAGE2 COMPLETE]")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=(STAGE_DETERMINISTIC, STAGE_GEMINI))
    parser.add_argument("--approve-stage1", action="store_true", help="Human confirmation after reviewing Stage 1 evidence.")
    args = parser.parse_args(argv)
    return run_stage(args.stage, approve_stage1=args.approve_stage1)


if __name__ == "__main__":
    raise SystemExit(main())
