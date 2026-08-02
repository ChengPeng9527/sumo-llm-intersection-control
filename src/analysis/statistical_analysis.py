from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import load_project_config


def describe_by_group(df: pd.DataFrame, group_cols: list[str], metric_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return df
    return df.groupby(group_cols)[metric_cols].agg(["mean", "std", "count"]).reset_index()


def compare_controllers(summary_df: pd.DataFrame, metric: str) -> pd.DataFrame:
    if summary_df.empty or "controller" not in summary_df.columns or metric not in summary_df.columns:
        return pd.DataFrame()
    grouped = summary_df.groupby("controller")[metric].agg(["mean", "std", "count"]).reset_index()
    grouped = grouped.sort_values("mean", ascending=False)
    return grouped


def export_statistical_summary(summary_df: pd.DataFrame, output_name: str = "statistical_summary.csv") -> Path:
    root = Path(load_project_config()["project_root"])
    out_dir = root / "results" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / output_name
    summary_df.to_csv(output_path, index=False)
    return output_path
