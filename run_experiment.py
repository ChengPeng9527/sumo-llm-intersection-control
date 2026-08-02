from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from common import CONFIG


RESULT_DIR = CONFIG["results_dir_path"]
EXPERIMENT_FILES = [
    {
        "experiment_id": "E01_BASELINE_4V_S1",
        "controller": "BaselineRule",
        "records_csv": RESULT_DIR / "E01_BASELINE_4V_S1_records.csv",
    },
    {
        "experiment_id": "E02_COOPERATIVE_4V_S1",
        "controller": "CooperativeRule",
        "records_csv": RESULT_DIR / "E02_COOPERATIVE_4V_S1_records.csv",
    },
    {
        "experiment_id": "E03_LLM_MOCK_4V_S1",
        "controller": "LLMMockController",
        "records_csv": RESULT_DIR / "E03_LLM_MOCK_4V_S1_records.csv",
    },
]

SUMMARY_CSV = RESULT_DIR / "summary_4v.csv"


def calculate_summary_from_csv(exp):
    path = Path(exp["records_csv"])
    if not path.exists():
        print(f"Missing file: {path}")
        return None

    df = pd.read_csv(path)
    if df.empty:
        print(f"Empty file: {path}")
        return None

    vehicles = df["vehicle_id"].unique() if "vehicle_id" in df.columns else df["vehicle"].unique()
    total_vehicles = len(vehicles)
    speed_col = "speed_after_action" if "speed_after_action" in df.columns else "speed"
    decision_col = "final_decision" if "final_decision" in df.columns else "decision"

    total_stop_events = (df[speed_col] < 0.1).sum()
    waiting_by_vehicle = (
        df[df[speed_col] < 0.1]
        .groupby("vehicle_id" if "vehicle_id" in df.columns else "vehicle")
        .size()
        .reindex(vehicles, fill_value=0)
    )
    avg_waiting_time = waiting_by_vehicle.mean()
    avg_speed = df[speed_col].mean()

    ttc_conflicts = df["conflict_detected"].astype(str).str.lower().eq("true").sum() if "conflict_detected" in df.columns else (df["conflict"].astype(str).str.lower().eq("true").sum() if "conflict" in df.columns else 0)
    safety_overrides = df["safety_override"].astype(str).str.lower().eq("true").sum() if "safety_override" in df.columns else 0

    proceed_count = (df[decision_col] == "PROCEED").sum()
    wait_count = (df[decision_col] == "WAIT").sum()
    free_count = (df[decision_col] == "FREE").sum()

    return {
        "experiment_id": exp["experiment_id"],
        "controller": exp["controller"],
        "vehicles_observed": total_vehicles,
        "total_stop_events": int(total_stop_events),
        "average_waiting_time": round(avg_waiting_time, 2),
        "average_speed": round(avg_speed, 2),
        "ttc_conflicts": int(ttc_conflicts),
        "safety_overrides": int(safety_overrides),
        "proceed_count": int(proceed_count),
        "wait_count": int(wait_count),
        "free_count": int(free_count),
    }


def main():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []

    for exp in EXPERIMENT_FILES:
        summary = calculate_summary_from_csv(exp)
        if summary is not None:
            summaries.append(summary)

    if not summaries:
        print("No summaries generated.")
        return

    fieldnames = list(summaries[0].keys())
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    print(f"Saved summary: {SUMMARY_CSV}")
    for s in summaries:
        print(
            s["controller"],
            "| vehicles:", s["vehicles_observed"],
            "| stop:", s["total_stop_events"],
            "| wait:", s["average_waiting_time"],
            "| speed:", s["average_speed"],
            "| conflicts:", s["ttc_conflicts"],
            "| overrides:", s["safety_overrides"],
        )


if __name__ == "__main__":
    main()
