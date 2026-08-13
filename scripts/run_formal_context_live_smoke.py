from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import scripts.run_formal_experiment_matrix as formal_runner
from src.common.metrics import calculate_summary, run_artifact_paths
from src.experiments.formal_experiment_matrix import FORMAL_CONTROLLER_SPECS, FORMAL_SCENARIO_DENSITY
from src.experiments.scenario_generator import generate_scenario

OUTPUT_ROOT = PROJECT_ROOT / "results" / "diagnostics" / "formal_context_live_smoke_v1"
SMOKE_EXPERIMENT_ID = "FORMAL_CONTEXT_SMOKE_RAW_V2"
SMOKE_CONTROLLER = "raw_llm"
SMOKE_CONTROLLER_SCRIPT = FORMAL_CONTROLLER_SPECS[SMOKE_CONTROLLER]["script"]
SMOKE_SCENARIO_ID = "formal_low_v4_seed1"
SMOKE_SEED = 1
SMOKE_VEHICLE_COUNT = 4
SMOKE_LLM_MODE = "real"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _git_output(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip()


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() == "true"


def _int_value(value: object) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _str_value(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _process_snapshot() -> dict[str, set[str]]:
    snapshot: dict[str, set[str]] = {"sumo.exe": set(), "sumo-gui.exe": set()}
    for image in snapshot:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV", "/NH"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if "No tasks are running" in result.stdout:
            continue
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith('"Image Name"'):
                continue
            try:
                row = next(csv.reader([line]))
            except Exception:
                continue
            if len(row) >= 2 and row[0].strip().lower() == image:
                snapshot[image].add(row[1].strip())
    return snapshot


def _residual_sumo_processes(baseline: dict[str, set[str]] | None = None) -> list[str]:
    baseline = baseline or {}
    residual: list[str] = []
    current = _process_snapshot()
    for image, pids in current.items():
        baseline_pids = baseline.get(image, set())
        for pid in sorted(pids - baseline_pids):
            residual.append(f"{image}:{pid}")
    return residual


def _cleanup_owned_sumo_processes(baseline: dict[str, set[str]]) -> list[str]:
    residual_before_cleanup = _residual_sumo_processes(baseline)
    pids = [entry.split(":", 1)[1] for entry in residual_before_cleanup if ":" in entry]
    if pids:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {', '.join(pids)} -Force"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        time.sleep(1.0)
    return _residual_sumo_processes(baseline)


def main() -> int:
    smoke_spec = SimpleNamespace(
        experiment_id=SMOKE_EXPERIMENT_ID,
        seed=SMOKE_SEED,
        scenario_id=SMOKE_SCENARIO_ID,
        vehicle_count=SMOKE_VEHICLE_COUNT,
        llm_mode=SMOKE_LLM_MODE,
    )
    scenario_config = generate_scenario(
        SMOKE_SCENARIO_ID,
        FORMAL_SCENARIO_DENSITY,
        SMOKE_SEED,
        vehicle_count=SMOKE_VEHICLE_COUNT,
    )
    env = formal_runner._build_env(smoke_spec, scenario_config)
    env["EXPERIMENT_ID"] = SMOKE_EXPERIMENT_ID
    env["SCENARIO_ID"] = SMOKE_SCENARIO_ID
    env["VEHICLE_COUNT"] = str(SMOKE_VEHICLE_COUNT)
    env["SEED"] = str(SMOKE_SEED)
    env["LLM_MODE"] = SMOKE_LLM_MODE

    run_id = f"{SMOKE_EXPERIMENT_ID}_v{SMOKE_VEHICLE_COUNT}_seed{SMOKE_SEED}_{SMOKE_LLM_MODE}"
    artifacts = run_artifact_paths(run_id)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    initial_sumo_processes = _process_snapshot()

    subprocess.run(
        [sys.executable, str(SMOKE_CONTROLLER_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )
    residual_after_cleanup = _cleanup_owned_sumo_processes(initial_sumo_processes)

    step_path = artifacts["step_records"]
    meta_path = artifacts["run_metadata"]
    event_path = artifacts["events"]

    with step_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    summary_stats = calculate_summary(rows, metadata)

    provider_rows = [row for row in rows if _bool_value(row.get("provider_request_attempted"))]
    provider_success_rows = [row for row in provider_rows if _bool_value(row.get("provider_request_success"))]
    parser_success_rows = [row for row in provider_success_rows if _bool_value(row.get("parser_success"))]
    fallback_rows = [row for row in rows if _bool_value(row.get("fallback_used"))]
    safety_rows = [row for row in rows if _bool_value(row.get("safety_override"))]
    finish_reason_counter = Counter(_str_value(row.get("finish_reason")) for row in provider_success_rows if _str_value(row.get("finish_reason")))
    response_lengths = [_int_value(row.get("response_content_length")) for row in provider_success_rows if _int_value(row.get("response_content_length"))]
    completion_tokens = [_int_value(row.get("completion_tokens")) for row in provider_success_rows if _int_value(row.get("completion_tokens"))]
    reasoning_tokens = [_int_value(row.get("reasoning_tokens")) for row in provider_success_rows if _int_value(row.get("reasoning_tokens"))]
    provider_names = sorted({ _str_value(row.get("provider_name")) for row in provider_success_rows if _str_value(row.get("provider_name")) })
    model_names = sorted({ _str_value(row.get("model_name")) for row in provider_success_rows if _str_value(row.get("model_name")) })
    trace_rows: list[dict[str, object]] = []
    for row in provider_rows:
        trace_rows.append(
            {
                "simulation_step": _int_value(row.get("simulation_step")),
                "vehicle_id": _str_value(row.get("vehicle_id")),
                "provider_request_attempted": _bool_value(row.get("provider_request_attempted")),
                "provider_request_success": _bool_value(row.get("provider_request_success")),
                "parser_success": _bool_value(row.get("parser_success")),
                "fallback_used": _bool_value(row.get("fallback_used")),
                "decision_source": _str_value(row.get("decision_source")),
                "finish_reason": _str_value(row.get("finish_reason")),
                "completion_tokens": _int_value(row.get("completion_tokens")) if _str_value(row.get("completion_tokens")) else None,
                "reasoning_tokens": _int_value(row.get("reasoning_tokens")) if _str_value(row.get("reasoning_tokens")) else None,
                "response_content_length": _int_value(row.get("response_content_length")) if _str_value(row.get("response_content_length")) else None,
                "latency_ms": float(row.get("latency_ms") or 0.0),
                "provider_name": _str_value(row.get("provider_name")),
                "model_name": _str_value(row.get("model_name")),
                "http_status": _str_value(row.get("http_status")),
            }
        )
    _write_jsonl(OUTPUT_ROOT / "formal_context_live_smoke_trace.jsonl", trace_rows)

    residual_processes = residual_after_cleanup

    summary = {
        "repository": str(PROJECT_ROOT),
        "branch": _git_output("branch", "--show-current"),
        "head": _git_output("rev-parse", "HEAD"),
        "controller": "raw_llm",
        "experiment_id": SMOKE_EXPERIMENT_ID,
        "run_id": run_id,
        "scenario_id": SMOKE_SCENARIO_ID,
        "vehicle_count": SMOKE_VEHICLE_COUNT,
        "seed": SMOKE_SEED,
        "provider": provider_names[0] if provider_names else "Groq",
        "model": model_names[0] if model_names else "openai/gpt-oss-20b",
        "base_url": env.get("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        "max_completion_tokens": env.get("LLM_MAX_COMPLETION_TOKENS", formal_runner.FORMAL_REQUEST_CONFIG["max_completion_tokens"]),
        "reasoning_effort": env.get("LLM_REASONING_EFFORT", formal_runner.FORMAL_REQUEST_CONFIG["reasoning_effort"]),
        "timeout": float(env.get("LLM_TIMEOUT_SECONDS", formal_runner.FORMAL_REQUEST_CONFIG["timeout"])),
        "max_retries": int(env.get("LLM_MAX_RETRIES", formal_runner.FORMAL_REQUEST_CONFIG["max_retries"])),
        "request_count": len(provider_rows),
        "provider_request_attempted": any(_bool_value(row.get("provider_request_attempted")) for row in rows),
        "provider_request_success": any(_bool_value(row.get("provider_request_success")) for row in rows),
        "provider_success_count": len(provider_success_rows),
        "provider_failure_count": len(provider_rows) - len(provider_success_rows),
        "parser_success_count": len(parser_success_rows),
        "fallback_count": len(fallback_rows),
        "safety_override_count": len(safety_rows),
        "finish_reason_distribution": dict(finish_reason_counter),
        "truncated_response_count": sum(1 for value in finish_reason_counter if value == "length"),
        "response_length_distribution": dict(Counter(response_lengths)),
        "completion_tokens_distribution": dict(Counter(completion_tokens)),
        "reasoning_tokens_values": sorted(set(reasoning_tokens)),
        "provider_request_rows": len(provider_rows),
        "parser_success_rows": len(parser_success_rows),
        "response_received": any(_int_value(row.get("response_content_length")) > 0 for row in provider_success_rows),
        "credential_available": bool(env.get("GROQ_API_KEY") or env.get("GROQ_CREDENTIAL_FILE") or env.get("LLM_CREDENTIAL_FILE")),
        "live_provider_gate_entered": bool(provider_rows),
        "live_provider_enabled": env.get("LLM_MODE", "").strip().lower() == "real",
        "live_client_constructed": bool(provider_success_rows),
        "provider_call_function_entered": bool(provider_rows),
        "parser_success": bool(parser_success_rows),
        "final_decision_values": sorted({ _str_value(row.get("final_decision")) for row in rows if _str_value(row.get("final_decision")) }),
        "decision_source_values": sorted({ _str_value(row.get("decision_source")) for row in rows if _str_value(row.get("decision_source")) }),
        "fallback_used": any(_bool_value(row.get("fallback_used")) for row in rows),
        "summary_metrics": {
            "departed": summary_stats.get("departed", 0),
            "arrived": summary_stats.get("arrived", 0),
            "completion_rate": summary_stats.get("completion_rate", 0.0),
            "mean_waiting_time": summary_stats.get("mean_waiting_time", 0.0),
            "mean_speed": summary_stats.get("mean_speed", 0.0),
            "collision_count": summary_stats.get("collision_count", 0),
        },
        "sumo_completed": bool(summary_stats.get("arrived", 0) == summary_stats.get("departed", 0) and summary_stats.get("departed", 0) > 0),
        "baseline_sumo_processes": {image: sorted(pids) for image, pids in initial_sumo_processes.items()},
        "residual_sumo_processes": residual_processes,
        "traci_cleanup": "passed" if not residual_processes else "failed",
        "evidence_path": str(OUTPUT_ROOT),
        "raw_artifacts": {
            "step_records": str(step_path),
            "run_metadata": str(meta_path),
            "events": str(event_path),
        },
        "trace_path": str(OUTPUT_ROOT / "formal_context_live_smoke_trace.jsonl"),
        "summary_path": str(OUTPUT_ROOT / "formal_context_live_smoke_summary.json"),
        "final_verdict": (
            "FORMAL_CONTEXT_SMOKE_PASSED"
            if any(_bool_value(row.get("provider_request_attempted")) for row in rows)
            and any(_bool_value(row.get("provider_request_success")) for row in rows)
            and any(_bool_value(row.get("parser_success")) for row in rows)
            and not residual_processes
            else "FORMAL_CONTEXT_SMOKE_FAILED"
        ),
    }

    _write_json(OUTPUT_ROOT / "formal_context_live_smoke_summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
