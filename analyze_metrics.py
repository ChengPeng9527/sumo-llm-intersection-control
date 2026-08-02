from __future__ import annotations

from src.analysis.aggregate_results import aggregate_results
from src.analysis.generate_figures import save_controller_comparison
from src.analysis.statistical_analysis import compare_controllers, export_statistical_summary


def main() -> int:
    df = aggregate_results(include_summaries=True)
    if df.empty:
        print("No result data found.")
        return 0

    summary_df = df[df["artifact_type"] == "summary"] if "artifact_type" in df.columns else df

    if "controller" in summary_df.columns:
        controller_summary = compare_controllers(summary_df, "mean_speed")
        if not controller_summary.empty:
            output_path = export_statistical_summary(controller_summary, "controller_speed_summary.csv")
            print(f"Saved statistical summary: {output_path}")
        figure_path = save_controller_comparison(summary_df, "mean_speed", "controller_speed_comparison.png")
        if figure_path is not None:
            print(f"Saved figure: {figure_path}")

    print(df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
