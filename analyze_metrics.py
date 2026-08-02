from __future__ import annotations

import pandas as pd


def main():
    df = pd.read_csv("results/summary_4v.csv")
    if df.empty:
        print("No summary data found.")
        return
    print("=== Summary Metrics ===")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
