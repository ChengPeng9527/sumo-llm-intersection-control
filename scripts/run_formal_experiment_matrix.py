from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common import CONFIG
from src.experiments.formal_experiment_matrix import (
    FORMAL_RESULTS_ROOT,
    FORMAL_REQUEST_CONFIG,
    FORMAL_SCENARIO_DENSITY,
    build_formal_manifest_row,
    build_formal_run_plan,
    formal_run_complete,
    formal_run_target_complete,
    formal_results_dir,
)
from src.experiments.scenario_generator import generate_scenario


PROJECT_ROOT = Path(CONFIG["project_root"])
COOLDOWN_SECONDS = 25


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _copy_run_artifacts(source_run_dir: Path, target_dir: Path) -> None:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in source_run_dir.iterdir():
        destination = target_dir / item.name
        if item.is_dir():
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)


def _move_partial_run_dir(run_dir: Path) -> Path:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    partial_dir = run_dir.with_name(f"{run_dir.name}__partial_{timestamp}")
    shutil.move(str(run_dir), str(partial_dir))
    return partial_dir




def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _merge_runtime_credentials(env: dict[str, str]) -> dict[str, str]:
    merged = dict(env)
    candidate_paths = []
    for credential_env in ("GROQ_CREDENTIAL_FILE", "LLM_CREDENTIAL_FILE"):
        credential_file = os.getenv(credential_env, "")
        if credential_file:
            candidate_paths.append(Path(credential_file))
    for user_env in (os.getenv("USERPROFILE", ""), os.getenv("HOME", "")):
        if user_env:
            candidate_paths.append(Path(user_env) / ".codex" / ".env")
    candidate_paths.extend([
        Path.home() / ".codex" / ".env",
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / ".codex" / ".env",
    ])
    for candidate in candidate_paths:
        for key, value in _load_env_file(candidate).items():
            if key in {"GROQ_API_KEY", "OPENROUTER_API_KEY", "SUMO_HOME", "PYTHONPATH"} and not merged.get(key):
                merged[key] = value
    return merged


def _build_env(spec, scenario_config: dict[str, object]) -> dict[str, str]:
    env = _merge_runtime_credentials(os.environ.copy())
    env["EXPERIMENT_ID"] = spec.experiment_id
    env["SEED"] = str(spec.seed)
    env["SCENARIO_ID"] = spec.scenario_id
    env["VEHICLE_COUNT"] = str(spec.vehicle_count)
    env["SIMULATION_STEPS"] = str(scenario_config["simulation_duration_seconds"])
    env["LLM_MODEL"] = FORMAL_REQUEST_CONFIG["model"]
    env["LLM_BASE_URL"] = FORMAL_REQUEST_CONFIG["base_url"]
    env["LLM_DECISION_INTERVAL"] = "1"
    if spec.llm_mode:
        env["LLM_MODE"] = spec.llm_mode
    return env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-runs", type=int, default=0)
    parser.add_argument("--cooldown-seconds", type=int, default=COOLDOWN_SECONDS)
    args = parser.parse_args(argv)

    plan = build_formal_run_plan()
    if args.max_runs:
        plan = plan[: args.max_runs]

    manifest_root = FORMAL_RESULTS_ROOT
    manifest_root.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_root / "run_manifest.json"
    dry_run_path = manifest_root / "dry_run_plan.json"

    manifest_rows: list[dict[str, object]] = []
    for spec in plan:
        row = build_formal_manifest_row(spec)
        row["status"] = "planned"
        row["reason"] = ""
        manifest_rows.append(row)

    _write_json(manifest_path, manifest_rows)
    _write_json(dry_run_path, manifest_rows)

    if args.dry_run:
        summary = {
            "planned_runs": len(manifest_rows),
            "completed_runs": 0,
            "skipped_completed_runs": 0,
            "dry_run": True,
            "manifest": str(manifest_path),
            "dry_run_plan": str(dry_run_path),
        }
        _write_json(manifest_root / "formal_experiment_summary.json", summary)
        print(json.dumps(summary, indent=2))
        return 0

    for index, spec in enumerate(plan, start=1):
        row = manifest_rows[index - 1]
        raw_artifacts = Path(row["raw_results_path"])
        formal_dir = Path(row["formal_results_path"])

        if formal_run_target_complete(spec.batch_id, spec.run_id):
            row["status"] = "skipped_completed"
            row["reason"] = "formal_results_already_complete"
            _write_json(manifest_path, manifest_rows)
            continue

        if formal_dir.exists() and not formal_run_target_complete(spec.batch_id, spec.run_id):
            partial_target = _move_partial_run_dir(formal_dir)
            row["formal_partial_backup_path"] = str(partial_target)

        scenario_config = generate_scenario(spec.scenario_id, FORMAL_SCENARIO_DENSITY, spec.seed, vehicle_count=spec.vehicle_count)
        env = _build_env(spec, scenario_config)
        row["simulation_steps"] = scenario_config["simulation_duration_seconds"]
        row["sumocfg_path"] = scenario_config["sumocfg_path"]
        row["status"] = "running"
        row["reason"] = ""
        _write_json(manifest_path, manifest_rows)

        if formal_run_complete(spec.run_id):
            row["status"] = "skipped_completed"
            row["reason"] = "raw_results_already_complete"
        else:
            subprocess.run([sys.executable, str(spec.controller_script)], cwd=PROJECT_ROOT, env=env, check=True)
            if not formal_run_complete(spec.run_id):
                row["status"] = "failed_incomplete_artifacts"
                row["reason"] = "missing_expected_raw_artifacts"
                _write_json(manifest_path, manifest_rows)
                raise RuntimeError(f"Formal run incomplete: {spec.run_id}")
            row["status"] = "completed"
            row["reason"] = ""

        if not formal_run_target_complete(spec.batch_id, spec.run_id):
            _copy_run_artifacts(raw_artifacts, formal_dir)

        row["formal_results_path"] = str(formal_dir)
        _write_json(manifest_path, manifest_rows)

        if index < len(plan):
            time.sleep(max(0, args.cooldown_seconds))

    summary = {
        "planned_runs": len(manifest_rows),
        "completed_runs": sum(1 for row in manifest_rows if row.get("status") == "completed"),
        "skipped_completed_runs": sum(1 for row in manifest_rows if row.get("status") == "skipped_completed"),
        "manifest": str(manifest_path),
        "dry_run_plan": str(dry_run_path),
    }
    _write_json(manifest_root / "formal_experiment_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
