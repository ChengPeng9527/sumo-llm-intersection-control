from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.common.config import load_project_config


def _raw_run_frames(results_dir: Path) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    raw_dir = results_dir / "raw"
    for step_records in raw_dir.glob("*/step_records.csv"):
        try:
            frame = pd.read_csv(step_records)
        except Exception:
            continue
        frame["source_file"] = str(step_records)
        frame["run_id_from_path"] = step_records.parent.name
        frame["artifact_type"] = "raw"
        frames.append(frame)
    return frames


def _summary_frames(results_dir: Path) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    summaries_dir = results_dir / "summaries"
    for summary_file in summaries_dir.glob("*.csv"):
        try:
            frame = pd.read_csv(summary_file)
        except Exception:
            continue
        frame["source_file"] = str(summary_file)
        frame["artifact_type"] = "summary"
        frames.append(frame)
    return frames


def aggregate_results(include_summaries: bool = True) -> pd.DataFrame:
    root = Path(load_project_config()["project_root"])
    results_dir = root / "results"
    frames = _raw_run_frames(results_dir)
    if include_summaries:
        frames.extend(_summary_frames(results_dir))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def load_run_manifest() -> list[dict]:
    root = Path(load_project_config()["project_root"])
    manifest_path = root / "results" / "run_manifest.json"
    if not manifest_path.exists():
        return []
    return json.loads(manifest_path.read_text(encoding="utf-8"))
