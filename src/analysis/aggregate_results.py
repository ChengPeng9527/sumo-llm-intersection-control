from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import load_project_config


def aggregate_results() -> pd.DataFrame:
    root = Path(load_project_config()["project_root"])
    results_dir = root / "results"
    frames = []
    for csv_path in results_dir.rglob("*.csv"):
        if csv_path.name.startswith("summary"):
            continue
        try:
            frames.append(pd.read_csv(csv_path))
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
