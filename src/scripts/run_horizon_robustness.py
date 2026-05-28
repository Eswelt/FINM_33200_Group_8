"""Run 1/4/13-week horizon robustness experiments."""

from pathlib import Path

import pandas as pd

from cli import build_model_panel, load_prices_for_config
from config import ProjectConfig
from expected_return_strategy import evaluate_expected_return_strategy
from price_target_tests import run_price_only_target_tests
from reports import save_metrics, save_predictions
from volatility import add_horizon_targets, evaluate_volatility_forecast


HORIZONS = (1, 4, 13)
FEATURE_SETS = (
    "price_only",
    "price_ai",
    "price_gdelt",
    "price_ai_gdelt",
    "price_calendar",
    "price_calendar_ai",
    "price_calendar_gdelt",
    "price_calendar_ai_gdelt",
)
OUTPUT_DIR = Path("docs_src/reports")
EXPERIMENT_DIR = Path("docs_src/experiments")


def flatten_metrics(task: str, horizon_weeks: int, metrics: dict) -> list[dict]:
    rows = []
    for run_id, values in metrics.items():
        row = {"task": task, "horizon_weeks": horizon_weeks, "run_id": run_id}
        row.update(values)
        rows.append(row)
    return rows


def markdown_table(frame: pd.DataFrame, floatfmt: str = ".4f") -> str:
    """Render a small DataFrame as a GitHub-style markdown table without extra deps."""
    if frame.empty:
        return ""
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(format(value, floatfmt))
            else:
                values.append("" if pd.isna(value) else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_markdown(summary: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Horizon Robustness Results",
        "",
        "Run date: 2026-05-27.",
        "",
        "This experiment keeps the weekly prediction cadence but changes the forward target horizon:",
        "",
        "- 1 week",
        "- 4 weeks",
        "- 13 weeks",
        "",
        "For return and direction tasks, the target is cumulative log return over the next horizon. For volatility, the target is realized volatility over the next horizon, measured as the square root of the sum of squared weekly returns. Multi-week targets overlap across adjacent prediction dates, so the results should be read as horizon-sensitivity diagnostics rather than independent quarterly observations.",
        "",
        "Feature sets:",
        "",
        "- `price_only`",
        "- `price_ai`",
        "- `price_gdelt`",
        "- `price_ai_gdelt`",
        "- `price_calendar`",
        "- `price_calendar_ai`",
        "- `price_calendar_gdelt`",
        "- `price_calendar_ai_gdelt`",
        "",
        "## Direction Pipeline",
        "",
    ]

    direction = summary[summary["task"] == "direction_classification"].copy()
    direction = direction[direction["run_id"].str.endswith("three_class_fixed")]
    if not direction.empty:
        table = direction[
            [
                "horizon_weeks",
                "feature_set",
                "accuracy",
                "balanced_accuracy_present_classes",
                "macro_f1",
                "n_test",
            ]
        ].rename(columns={"balanced_accuracy_present_classes": "balanced_accuracy"})
        lines.append(markdown_table(table))
        lines.append("")

    lines.extend(["## Expected-Return Pipeline", ""])
    returns = summary[summary["task"] == "expected_return"].copy()
    if not returns.empty:
        table = returns[
            [
                "horizon_weeks",
                "feature_set",
                "estimator",
                "mae",
                "rmse",
                "r2",
                "direction_accuracy",
                "strategy_total_return",
                "strategy_sharpe",
            ]
        ]
        lines.append(markdown_table(table))
        lines.append("")

    lines.extend(["## Volatility Pipeline", ""])
    vol = summary[summary["task"] == "volatility"].copy()
    if not vol.empty:
        table = vol[
            [
                "horizon_weeks",
                "feature_set",
                "estimator",
                "mae",
                "rmse",
                "r2",
                "spearman_corr",
                "high_vol_balanced_accuracy",
            ]
        ]
        lines.append(markdown_table(table))
        lines.append("")

    lines.extend(
        [
            "## Takeaway",
            "",
            "The horizon comparison is intended to show whether USDA/GLM and seasonality features work better as medium-horizon signals than as one-week signals. Direction and return results should be interpreted cautiously because multi-week cumulative returns are still noisy and overlapping. The volatility pipeline is the most economically natural horizon test because crop and weather information often changes the width of the return distribution before it gives a clean directional edge.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    config = ProjectConfig(end="2026-05-15", feature_sets=",".join(FEATURE_SETS))
    prices = load_prices_for_config(config, demo=False)
    base_panel = build_model_panel(config, prices)

    summary_rows = []
    prediction_frames = []

    for horizon in HORIZONS:
        panel = add_horizon_targets(base_panel, horizon)

        direction_metrics, direction_predictions = run_price_only_target_tests(
            panel=panel,
            feature_sets=FEATURE_SETS,
            split_date=config.split_date,
            test_window_weeks=config.test_window_weeks,
            retrain_step_weeks=config.retrain_step_weeks,
            three_class_threshold=config.fixed_return_threshold,
        )
        summary_rows.extend(flatten_metrics("direction_classification", horizon, direction_metrics))
        direction_predictions["task"] = "direction_classification"
        direction_predictions["horizon_weeks"] = horizon
        prediction_frames.append(direction_predictions)

        return_metrics, return_predictions = evaluate_expected_return_strategy(
            panel=panel,
            feature_sets=FEATURE_SETS,
            split_date=config.split_date,
            test_window_weeks=config.test_window_weeks,
            retrain_step_weeks=config.retrain_step_weeks,
            transaction_cost_bps=config.transaction_cost_bps,
            buffer_bps=config.buffer_bps,
        )
        summary_rows.extend(flatten_metrics("expected_return", horizon, return_metrics))
        return_predictions["task"] = "expected_return"
        return_predictions["horizon_weeks"] = horizon
        prediction_frames.append(return_predictions)

        volatility_metrics, volatility_predictions = evaluate_volatility_forecast(
            panel=panel,
            feature_sets=FEATURE_SETS,
            split_date=config.split_date,
            test_window_weeks=config.test_window_weeks,
            retrain_step_weeks=config.retrain_step_weeks,
            target_column="target_realized_vol_next",
            target_name=f"next_{horizon}_week_realized_volatility",
        )
        summary_rows.extend(flatten_metrics("volatility", horizon, volatility_metrics))
        volatility_predictions["task"] = "volatility"
        volatility_predictions["horizon_weeks"] = horizon
        prediction_frames.append(volatility_predictions)

    summary = pd.DataFrame(summary_rows)
    predictions = pd.concat(prediction_frames, ignore_index=True, sort=False)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_DIR / "horizon_robustness_metrics.csv", index=False)
    save_predictions(predictions, OUTPUT_DIR / "horizon_robustness_predictions.csv")
    save_metrics(
        {
            f"{row['task']}_{row['horizon_weeks']}w_{row['run_id']}": {
                key: value for key, value in row.items() if key not in {"task", "horizon_weeks", "run_id"}
            }
            for row in summary_rows
        },
        OUTPUT_DIR / "horizon_robustness_metrics.json",
    )
    write_markdown(summary, EXPERIMENT_DIR / "horizon_robustness_results.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
