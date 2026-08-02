from __future__ import annotations

import pandas as pd


def describe_by_group(df: pd.DataFrame, group_cols: list[str], metric_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return df
    return df.groupby(group_cols)[metric_cols].agg(["mean", "std", "count"]).reset_index()
