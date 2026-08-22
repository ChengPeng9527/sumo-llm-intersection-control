from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Sumo\sumo_train")
PYTHON = sys.executable
CTRL = ROOT / "fallback_only_controller.py"
RESULTS_ROOT = ROOT / "results" / "diagnostics" / "fallback_only_ablation_v1"
RUNS_ROOT = RESULTS_ROOT / "runs"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiments.scenario_generator import generate_scenario


def _copytree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    if not rows:
        return {}
    vehicles = sorted({r["vehicle_id"] for r in rows if r.get("vehicle_id")})
    departed = sum(1 for r in rows if r.get("departed", "").lower() == "true")
    arrived = sum(1 for r in rows if r.get("arrived", "").lower() == "true")
    collisions = sum(1 for r in rows if r.get("collision", "").lower() == "true")
    speeds = [float(r.get("speed_after_action") or 0.0) for r in rows]
    waiting = [1 for r in rows if float(r.get("speed_after_action") or 0.0) < 0.1]
    return {
        "vehicles_observed": len(vehicles),
        "departed": departed,
        "arrived": arrived,
        "throughput": arrived,
        "completion_rate": arrived / departed if departed else 0.0,
        "mean_speed": sum(speeds) / len(speeds),
        "mean_waiting_time": sum(waiting) / len(vehicles) if vehicles else 0.0,
        "collision_count": collisions,
    }


def _run_one(seed: int, vehicle_count: int) -> dict[str, object]:
    scenario_id = f"formal_low_v{vehicle_count}_seed{seed}"
    run_id = f"FB_ONLY_v{vehicle_count}_seed{seed}_mock"
    scenario_config = generate_scenario(scenario_id, "low", seed, vehicle_count=vehicle_count)
    env = os.environ.copy()
    env.update(
        {
            "EXPERIMENT_ID": "FB_ONLY",
            "SEED": str(seed),
            "SCENARIO_ID": scenario_id,
            "VEHICLE_COUNT": str(vehicle_count),
            "SIMULATION_STEPS": str(scenario_config["simulation_duration_seconds"]),
        }
    )
    subprocess.run([PYTHON, str(CTRL)], cwd=ROOT, env=env, check=True)
    src_dir = ROOT / "results" / "raw" / run_id
    batch_dir = RUNS_ROOT / f"seed{seed}_v{vehicle_count}"
    dst_dir = batch_dir / run_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    _copytree(src_dir, dst_dir)
    rows = _load_csv_rows(dst_dir / "step_records.csv")
    summary = _summarize(rows)
    summary.update(
        {
            "run_id": run_id,
            "seed": seed,
            "vehicle_count": vehicle_count,
            "scenario_id": scenario_id,
            "source_dir": str(src_dir),
            "diagnostic_dir": str(dst_dir),
        }
    )
    with (dst_dir / "diagnostic_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary


def main() -> int:
    if RESULTS_ROOT.exists():
        shutil.rmtree(RESULTS_ROOT)
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    rows = []
    for vehicle_count in (4, 8):
        for seed in (1, 2, 3):
            rows.append(_run_one(seed=seed, vehicle_count=vehicle_count))

    with (RESULTS_ROOT / "fallback_only_ablation_summary.json").open("w", encoding="utf-8") as f:
        json.dump({"runs": rows}, f, indent=2, ensure_ascii=False)
    with (RESULTS_ROOT / "fallback_only_ablation_summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_id",
                "seed",
                "vehicle_count",
                "throughput",
                "completion_rate",
                "mean_waiting_time",
                "mean_speed",
                "collision_count",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in writer.fieldnames})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
