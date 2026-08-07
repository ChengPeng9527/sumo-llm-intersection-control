from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from src.common.config import load_project_config
from src.common.logging_schema import FIELDNAMES
from src.experiments.scenario_generator import generate_scenario


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PILOT_ROOT = PROJECT_ROOT / "results" / "pilot" / "dissertation_pilot_v1"
PILOT_SCENARIO_DENSITY = "low"
PILOT_SCENARIO_SEED = 1
PILOT_VEHICLE_COUNT = 4
PILOT_SCENARIO_ID = "dissertation_pilot_low_v4_seed1"
PILOT_LLM_MODE = "real"
PILOT_LLM_BASE_URL = "https://api.groq.com/openai/v1"
PILOT_LLM_MODEL = "openai/gpt-oss-20b"
PILOT_LLM_DECISION_INTERVAL = "1"


CONTROLLERS = [
    {
        "key": "rule_based",
        "label": "Rule-based",
        "script": PROJECT_ROOT / "baseline_controller.py",
        "run_id": "E01_BASELINE_4V_S1_v4_seed1",
        "llm_mode": None,
    },
    {
        "key": "raw_llm",
        "label": "Raw LLM",
        "script": PROJECT_ROOT / "raw_llm_controller.py",
        "run_id": "E04_RAW_LLM_4V_S1_v4_seed1_real",
        "llm_mode": PILOT_LLM_MODE,
    },
    {
        "key": "hybrid",
        "label": "Hybrid",
        "script": PROJECT_ROOT / "hybrid_llm_controller.py",
        "run_id": "E05_HYBRID_LLM_4V_S1_v4_seed1_real",
        "llm_mode": PILOT_LLM_MODE,
    },
    {
        "key": "hybrid_safety",
        "label": "Hybrid + Safety",
        "script": PROJECT_ROOT / "hybrid_llm_safety_controller.py",
        "run_id": "E06_HYBRID_LLM_SAFETY_4V_S1_v4_seed1_real",
        "llm_mode": PILOT_LLM_MODE,
    },
]


def _bool_state(value: str | None) -> str:
    return "present" if value else "missing"


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _group_rows_by_request(rows: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if _to_bool(row.get("llm_called")):
            grouped[_to_int(row.get("simulation_step"))].append(row)
    return [grouped[step] for step in sorted(grouped)]


def _decision_counter(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(Counter(row.get(field, "") for row in rows if row.get(field)))


def _ensure_no_residual_sumo_processes() -> list[str]:
    residual: list[str] = []
    for image_name in ("sumo.exe", "sumo-gui.exe"):
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image_name}"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            lowered = line.lower().strip()
            if lowered.startswith(image_name):
                residual.append(line.strip())
    return residual


def _run_controller(script: Path, env: dict[str, str]) -> float:
    start = time.perf_counter()
    subprocess.run([sys.executable, str(script)], cwd=PROJECT_ROOT, env=env, check=True)
    return time.perf_counter() - start


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


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _summarise_rows(
    *,
    controller_key: str,
    controller_label: str,
    run_id: str,
    source_run_dir: Path,
    controller_dir: Path,
    scenario_id: str,
    vehicle_count: int,
    seed: int,
    runtime_seconds: float,
) -> dict:
    step_records = source_run_dir / "step_records.csv"
    run_metadata_path = source_run_dir / "run_metadata.json"
    events_path = source_run_dir / "events.jsonl"

    if not step_records.exists() or not run_metadata_path.exists() or not events_path.exists():
        raise FileNotFoundError(f"Missing expected artifacts for {controller_key}: {source_run_dir}")

    rows = _read_csv_rows(step_records)
    if not rows:
        raise RuntimeError(f"No step records found for {controller_key}")

    with run_metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)

    missing_fields = [field for field in FIELDNAMES if field not in rows[0]]
    output_file_count = sum(1 for item in controller_dir.iterdir() if item.is_file())
    total_rows = len(rows)
    vehicles = sorted({row.get("vehicle_id", "") for row in rows if row.get("vehicle_id")})
    departed_total = _to_float(metadata.get("departed_count", sum(1 for row in rows if _to_bool(row.get("departed")))))
    arrived_total = _to_float(metadata.get("arrived_count", sum(1 for row in rows if _to_bool(row.get("arrived")))))
    collision_count = _to_int(metadata.get("collision_count", sum(1 for row in rows if _to_bool(row.get("collision")))))
    completion_rate = arrived_total / departed_total if departed_total else 0.0
    mean_speed = sum(_to_float(row.get("speed_after_action")) for row in rows) / total_rows
    mean_waiting_time = (sum(1 for row in rows if _to_float(row.get("speed_after_action")) < 0.1) / len(vehicles)) if vehicles else 0.0
    episode_duration = max(_to_float(row.get("simulation_time_seconds")) for row in rows)
    max_step = max(_to_int(row.get("simulation_step")) for row in rows)
    actual_simulation_steps = len({_to_int(row.get("simulation_step")) for row in rows})

    request_groups = _group_rows_by_request(rows)
    request_count = len(request_groups)
    successful_request_count = sum(1 for group in request_groups if _to_bool(group[0].get("json_parse_success")) and not _to_bool(group[0].get("fallback_used")))
    failed_request_count = request_count - successful_request_count
    retry_count = sum(_to_int(group[0].get("retry_count")) for group in request_groups)
    parser_success_count = sum(1 for group in request_groups if _to_bool(group[0].get("json_parse_success")))
    fallback_count = sum(1 for group in request_groups if _to_bool(group[0].get("fallback_used")))
    latencies = [_to_float(group[0].get("llm_response_time_ms")) for group in request_groups]
    average_latency = sum(latencies) / len(latencies) if latencies else 0.0
    total_latency = sum(latencies)
    provider = "Groq" if request_count else "N/A"
    model = next((group[0].get("llm_model", "") for group in request_groups if group and group[0].get("llm_model")), "")

    raw_distribution = _decision_counter(rows, "llm_raw_decision")
    validated_distribution = _decision_counter(rows, "validated_llm_decision")
    postprocessed_distribution = _decision_counter(rows, "postprocessed_decision")
    final_distribution = _decision_counter(rows, "final_decision")
    decision_source_distribution = _decision_counter(rows, "decision_source")
    postprocessor_intervention_count = sum(1 for row in rows if _to_bool(row.get("postprocess_applied")))
    safety_override_count = sum(1 for row in rows if _to_bool(row.get("safety_override")))
    raw_to_final_agreement_count = sum(1 for row in rows if row.get("final_decision") == row.get("validated_llm_decision"))
    validated_to_postprocessed_change_count = sum(1 for row in rows if row.get("postprocessed_decision") != row.get("validated_llm_decision"))
    postprocessed_to_final_change_count = sum(1 for row in rows if row.get("final_decision") != row.get("postprocessed_decision"))

    return {
        "controller_key": controller_key,
        "controller_label": controller_label,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "vehicle_count": vehicle_count,
        "seed": seed,
        "controller_runtime_seconds": round(runtime_seconds, 3),
        "wall_clock_runtime_seconds": round(runtime_seconds, 3),
        "sumo_runtime_seconds": round(episode_duration, 3),
        "scheduled_vehicles": _to_int(metadata.get("vehicle_count", vehicle_count)),
        "departed_vehicles": _to_int(departed_total),
        "arrived_vehicles": _to_int(arrived_total),
        "completion_rate": round(completion_rate, 6),
        "throughput": _to_int(arrived_total),
        "mean_waiting_time": round(mean_waiting_time, 6),
        "mean_speed": round(mean_speed, 6),
        "episode_duration": round(episode_duration, 3),
        "collision_count": collision_count,
        "max_simulation_step": max_step,
        "actual_simulation_steps": actual_simulation_steps,
        "live_request_count": request_count,
        "successful_request_count": successful_request_count,
        "failed_request_count": failed_request_count,
        "retry_count": retry_count,
        "parser_success_count": parser_success_count,
        "fallback_count": fallback_count,
        "average_latency_ms": round(average_latency, 3),
        "total_latency_ms": round(total_latency, 3),
        "provider": provider,
        "model": model,
        "raw_action_count": raw_distribution,
        "validated_action_count": validated_distribution,
        "postprocessed_action_count": postprocessed_distribution,
        "final_action_count": final_distribution,
        "postprocessor_intervention_count": postprocessor_intervention_count,
        "safety_override_count": safety_override_count,
        "raw_to_final_agreement_count": raw_to_final_agreement_count,
        "validated_to_postprocessed_change_count": validated_to_postprocessed_change_count,
        "postprocessed_to_final_change_count": postprocessed_to_final_change_count,
        "decision_source_distribution": decision_source_distribution,
        "output_file_count": output_file_count,
        "missing_field_count": len(missing_fields),
        "missing_fields": missing_fields,
        "source_artifacts": {
            "step_records": str(step_records),
            "run_metadata": str(run_metadata_path),
            "events": str(events_path),
        },
    }


def main() -> int:
    project = load_project_config()
    sumo_binary = project["sumo_binary_path"]
    sumo_gui_binary = project["sumo_gui_binary_path"]
    sumo_config = project["sumo_config_path"]

    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("PILOT_BLOCKED_NO_SAFE_CREDENTIAL: GROQ_API_KEY is missing from the current PowerShell session.")

    for required in [sumo_binary, sumo_gui_binary, sumo_config]:
        if not Path(required).exists():
            raise SystemExit("PILOT_BLOCKED_CONFIGURATION: required SUMO files are missing.")

    for controller in CONTROLLERS:
        if not controller["script"].exists():
            raise SystemExit(f"PILOT_BLOCKED_CONFIGURATION: missing controller script {controller['script']}.")

    PILOT_ROOT.mkdir(parents=True, exist_ok=True)

    scenario_config = generate_scenario(
        PILOT_SCENARIO_ID,
        PILOT_SCENARIO_DENSITY,
        PILOT_SCENARIO_SEED,
        vehicle_count=PILOT_VEHICLE_COUNT,
    )
    scenario_summary = {
        "scenario_id": PILOT_SCENARIO_ID,
        "density": PILOT_SCENARIO_DENSITY,
        "seed": PILOT_SCENARIO_SEED,
        "vehicle_count": PILOT_VEHICLE_COUNT,
        "sumocfg_path": scenario_config["sumocfg_path"],
        "simulation_duration_seconds": scenario_config["simulation_duration_seconds"],
        "route_sequence": scenario_config["route_sequence"],
    }

    controller_env_base = os.environ.copy()
    controller_env_base["SCENARIO_ID"] = PILOT_SCENARIO_ID
    controller_env_base["VEHICLE_COUNT"] = str(PILOT_VEHICLE_COUNT)
    controller_env_base["SUMO_CONFIG_PATH"] = scenario_config["sumocfg_path"]
    controller_env_base["SIMULATION_STEPS"] = str(scenario_config["simulation_duration_seconds"])
    controller_env_base["LLM_DECISION_INTERVAL"] = PILOT_LLM_DECISION_INTERVAL
    controller_env_base["LLM_BASE_URL"] = PILOT_LLM_BASE_URL
    controller_env_base["LLM_MODEL"] = PILOT_LLM_MODEL

    pilot_config = {
        "pilot_id": "dissertation_pilot_v1",
        "current_branch": "phase-18-decision-pipeline-separation",
        "python_executable": sys.executable,
        "sumo_binary": str(sumo_binary),
        "sumo_gui_binary": str(sumo_gui_binary),
        "sumo_config": str(sumo_config),
        "groq_api_key_state": _bool_state(os.getenv("GROQ_API_KEY")),
        "provider": "Groq",
        "base_url": PILOT_LLM_BASE_URL,
        "model": PILOT_LLM_MODEL,
        "decision_interval": int(PILOT_LLM_DECISION_INTERVAL),
        "seed": PILOT_SCENARIO_SEED,
        "vehicle_count": PILOT_VEHICLE_COUNT,
        "scenario": scenario_summary,
        "controllers": [
            {
                "key": controller["key"],
                "label": controller["label"],
                "script": str(controller["script"]),
                "run_id": controller["run_id"],
                "llm_mode": controller["llm_mode"],
            }
            for controller in CONTROLLERS
        ],
    }
    _write_json(PILOT_ROOT / "pilot_config.json", pilot_config)

    summary_rows: list[dict[str, object]] = []
    decision_flow_rows: list[dict[str, object]] = []
    request_cost_summary: dict[str, dict[str, object]] = {}
    runtime_summary: dict[str, dict[str, object]] = {}
    overall_status = "completed"
    failures: list[dict[str, object]] = []

    for controller in CONTROLLERS:
        controller_key = controller["key"]
        controller_label = controller["label"]
        controller_dir = PILOT_ROOT / controller_key / controller["run_id"]
        source_run_dir = Path(project["results_dir_path"]) / "raw" / controller["run_id"]
        env = controller_env_base.copy()
        if controller["llm_mode"] is not None:
            env["LLM_MODE"] = controller["llm_mode"]

        print(f"[pilot] running {controller_label} -> {controller['run_id']}")
        try:
            runtime_seconds = _run_controller(controller["script"], env)
            _copy_run_artifacts(source_run_dir, controller_dir)
            summary = _summarise_rows(
                controller_key=controller_key,
                controller_label=controller_label,
                run_id=controller["run_id"],
                source_run_dir=source_run_dir,
                controller_dir=controller_dir,
                scenario_id=PILOT_SCENARIO_ID,
                vehicle_count=PILOT_VEHICLE_COUNT,
                seed=PILOT_SCENARIO_SEED,
                runtime_seconds=runtime_seconds,
            )
            summary["status"] = "completed"
            summary_rows.append(summary)
            request_cost_summary[controller_key] = {
                "controller_label": controller_label,
                "provider": summary["provider"],
                "model": summary["model"],
                "live_request_count": summary["live_request_count"],
                "successful_request_count": summary["successful_request_count"],
                "failed_request_count": summary["failed_request_count"],
                "retry_count": summary["retry_count"],
                "parser_success_count": summary["parser_success_count"],
                "fallback_count": summary["fallback_count"],
                "average_latency_ms": summary["average_latency_ms"],
                "total_latency_ms": summary["total_latency_ms"],
            }
            runtime_summary[controller_key] = {
                "controller_label": controller_label,
                "controller_runtime_seconds": summary["controller_runtime_seconds"],
                "wall_clock_runtime_seconds": summary["wall_clock_runtime_seconds"],
                "sumo_runtime_seconds": summary["sumo_runtime_seconds"],
                "output_file_count": summary["output_file_count"],
                "missing_field_count": summary["missing_field_count"],
            }
            decision_flow_rows.append(
                {
                    "controller_key": controller_key,
                    "controller_label": controller_label,
                    "raw_action_count": json.dumps(summary["raw_action_count"], ensure_ascii=False),
                    "validated_action_count": json.dumps(summary["validated_action_count"], ensure_ascii=False),
                    "postprocessed_action_count": json.dumps(summary["postprocessed_action_count"], ensure_ascii=False),
                    "final_action_count": json.dumps(summary["final_action_count"], ensure_ascii=False),
                    "postprocessor_intervention_count": summary["postprocessor_intervention_count"],
                    "safety_override_count": summary["safety_override_count"],
                    "raw_to_final_agreement_count": summary["raw_to_final_agreement_count"],
                    "validated_to_postprocessed_change_count": summary["validated_to_postprocessed_change_count"],
                    "postprocessed_to_final_change_count": summary["postprocessed_to_final_change_count"],
                    "decision_source_distribution": json.dumps(summary["decision_source_distribution"], ensure_ascii=False),
                }
            )
        except Exception as exc:
            overall_status = "failed"
            failures.append(
                {
                    "controller_key": controller_key,
                    "controller_label": controller_label,
                    "run_id": controller["run_id"],
                    "error": str(exc),
                }
            )
            break

    if failures:
        _write_json(PILOT_ROOT / "pilot_failures.json", failures)

    _write_csv(
        PILOT_ROOT / "pilot_summary.csv",
        summary_rows,
        [
            "controller_key",
            "controller_label",
            "run_id",
            "scenario_id",
            "vehicle_count",
            "seed",
            "controller_runtime_seconds",
            "wall_clock_runtime_seconds",
            "sumo_runtime_seconds",
            "scheduled_vehicles",
            "departed_vehicles",
            "arrived_vehicles",
            "completion_rate",
            "throughput",
            "mean_waiting_time",
            "mean_speed",
            "episode_duration",
            "collision_count",
            "max_simulation_step",
            "actual_simulation_steps",
            "live_request_count",
            "successful_request_count",
            "failed_request_count",
            "retry_count",
            "parser_success_count",
            "fallback_count",
            "average_latency_ms",
            "total_latency_ms",
            "provider",
            "model",
            "postprocessor_intervention_count",
            "safety_override_count",
            "raw_to_final_agreement_count",
            "validated_to_postprocessed_change_count",
            "postprocessed_to_final_change_count",
            "output_file_count",
            "missing_field_count",
            "status",
        ],
    )

    _write_json(
        PILOT_ROOT / "pilot_summary.json",
        {
            "pilot_id": pilot_config["pilot_id"],
            "status": overall_status,
            "scenario": scenario_summary,
            "controllers": summary_rows,
            "failures": failures,
        },
    )
    _write_csv(
        PILOT_ROOT / "decision_flow_summary.csv",
        decision_flow_rows,
        [
            "controller_key",
            "controller_label",
            "raw_action_count",
            "validated_action_count",
            "postprocessed_action_count",
            "final_action_count",
            "postprocessor_intervention_count",
            "safety_override_count",
            "raw_to_final_agreement_count",
            "validated_to_postprocessed_change_count",
            "postprocessed_to_final_change_count",
            "decision_source_distribution",
        ],
    )
    _write_json(PILOT_ROOT / "request_cost_summary.json", request_cost_summary)
    _write_json(PILOT_ROOT / "runtime_summary.json", runtime_summary)

    residual_sumo = _ensure_no_residual_sumo_processes()
    _write_json(
        PILOT_ROOT / "pilot_verification.json",
        {
            "residual_sumo_processes": residual_sumo,
            "output_root": str(PILOT_ROOT),
            "artifact_files": {
                "pilot_config": str(PILOT_ROOT / "pilot_config.json"),
                "pilot_summary_csv": str(PILOT_ROOT / "pilot_summary.csv"),
                "pilot_summary_json": str(PILOT_ROOT / "pilot_summary.json"),
                "decision_flow_summary_csv": str(PILOT_ROOT / "decision_flow_summary.csv"),
                "request_cost_summary_json": str(PILOT_ROOT / "request_cost_summary.json"),
                "runtime_summary_json": str(PILOT_ROOT / "runtime_summary.json"),
            },
        },
    )

    if residual_sumo:
        raise SystemExit("PILOT_BLOCKED_CONFIGURATION: residual SUMO processes were detected after the pilot run.")
    if overall_status != "completed":
        raise SystemExit("PILOT_FAILED_CONTROLLER_INCONSISTENCY")

    print(json.dumps({"status": overall_status, "output_root": str(PILOT_ROOT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
