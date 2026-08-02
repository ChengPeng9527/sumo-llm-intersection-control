from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


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
