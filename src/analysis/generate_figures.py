from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_project_config


def plot_metric(df: pd.DataFrame, x: str, y: str, title: str, output_path: str) -> None:
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    for key, group in df.groupby(x):
        ax.plot(group[y].values, label=str(key))
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_controller_comparison(df: pd.DataFrame, metric: str, filename: str) -> Path | None:
    if df.empty or "controller" not in df.columns or metric not in df.columns:
        return None
    root = Path(load_project_config()["project_root"])
    out_path = root / "results" / "figures" / filename
    fig, ax = plt.subplots(figsize=(8, 4))
    plot_df = df.groupby("controller")[metric].mean().sort_values(ascending=False)
    plot_df.plot(kind="bar", ax=ax, color="#2E86AB")
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_title(f"Controller comparison: {metric}")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
