"""Generate the CORN workflow notebook and a standalone HTML rendering."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import shutil
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Iterable, List, Optional

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DOCS_SRC = ROOT / "docs_src"
DEFAULT_NOTEBOOK = ROOT / "reports" / "notebooks" / "corn_forecast_workflow.ipynb"
DEFAULT_HTML = ROOT / "reports" / "html" / "corn_forecast_workflow.html"
DEFAULT_REPORT_MD = DOCS_SRC / "final_report.md"
FIGURE_DIR = ROOT / "reports" / "figures"
DOCS_FIGURE_DIR = DOCS_SRC / "figures"


PERCENT_COLUMNS = {
    "accuracy",
    "balanced_accuracy",
    "balanced_accuracy_present_classes",
    "macro_f1",
    "f1",
    "roc_auc",
    "direction_accuracy",
    "strategy_total_return",
    "benchmark_total_return",
    "strategy_annual_return",
    "strategy_annual_vol",
    "max_drawdown",
    "trade_frequency",
    "hit_rate_traded_weeks",
    "turnover",
    "extreme_event_rate",
    "tradeable_event_rate",
}


INTEGER_COLUMNS = {
    "rows",
    "columns",
    "n_down",
    "n_flat",
    "n_up",
    "n_test",
    "n_folds",
    "n_train",
    "trade_count",
    "price_features",
    "calendar_features",
    "weather_features",
    "text_features",
    "ai_features",
}


DISPLAY_NAMES = {
    "artifact": "artifact",
    "rows": "rows",
    "columns": "cols",
    "run": "run",
    "model": "model",
    "feature_set": "features",
    "estimator": "model",
    "validation_scheme": "validation",
    "accuracy": "accuracy",
    "balanced_accuracy": "balanced acc",
    "balanced_accuracy_present_classes": "balanced acc",
    "macro_f1": "macro F1",
    "f1": "F1",
    "roc_auc": "ROC-AUC",
    "mae": "MAE",
    "rmse": "RMSE",
    "r2": "R2",
    "direction_accuracy": "direction acc",
    "strategy_total_return": "strategy return",
    "strategy_sharpe": "Sharpe",
    "max_drawdown": "max drawdown",
    "trade_frequency": "trade freq",
    "n_down": "down",
    "n_flat": "flat",
    "n_up": "up",
    "n_test": "OOS rows",
    "n_folds": "folds",
    "k": "k",
}


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_table(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _clean_value(value):
    if value is None:
        return ""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value


def _metrics_frame(metrics: Optional[dict]) -> pd.DataFrame:
    if not metrics:
        return pd.DataFrame()
    rows = []
    for name, values in metrics.items():
        row = {"run": name}
        for key, value in values.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                row[key] = _clean_value(value)
        rows.append(row)
    return pd.DataFrame(rows)


def _metric_float(row: pd.Series, column: str, default: float = float("nan")) -> float:
    value = row.get(column, default)
    return float(value) if value not in ("", None) and not pd.isna(value) else default


def _format_cell(column: str, value) -> str:
    value = _clean_value(value)
    if value == "":
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if column in INTEGER_COLUMNS:
            return f"{value:,.0f}"
        if column in PERCENT_COLUMNS:
            return f"{value:.1%}"
        if column in {"strategy_sharpe", "benchmark_sharpe"}:
            return f"{value:.3f}"
        if column in {"mae", "rmse", "r2", "log_loss"}:
            return f"{value:.4f}"
        if abs(value) >= 100:
            return f"{value:,.0f}"
        return f"{value:.3f}"
    return str(value)


def _display_frame(frame: pd.DataFrame, columns: List[str], max_rows: int = 20) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    available = [column for column in columns if column in frame.columns]
    view = frame.loc[:, available].head(max_rows).copy()
    for column in view.columns:
        view[column] = view[column].map(lambda value, col=column: _format_cell(col, value))
    return view.rename(columns={column: DISPLAY_NAMES.get(column, column) for column in view.columns})


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame is None or frame.empty:
        return "No local artifact available."
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(row[column]).replace("\n", " ") for column in columns) + " |")
    return "\n".join(lines)


def _sort_desc(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    if frame is None or frame.empty or column not in frame.columns:
        return frame if frame is not None else pd.DataFrame()
    return frame.sort_values(column, ascending=False, na_position="last").reset_index(drop=True)


def _shape_rows(paths: Iterable[Path]) -> pd.DataFrame:
    rows = []
    for path in paths:
        if not path.exists():
            rows.append({"artifact": str(path.relative_to(ROOT)), "exists": False, "rows": "", "columns": ""})
            continue
        frame = _read_table(path)
        rows.append(
            {
                "artifact": str(path.relative_to(ROOT)),
                "exists": True,
                "rows": len(frame),
                "columns": len(frame.columns),
            }
        )
    return pd.DataFrame(rows)


def _source_map() -> pd.DataFrame:
    rows = [
        ("Task graph", "dodo.py", "Single pydoit entrypoint for data, models, reports, ChartBook, tests."),
        ("CLI orchestration", "src/corn_forecast/cli.py", "Command surface used by pydoit; now reuses cached prices when available."),
        ("Configuration", "src/corn_forecast/config.py", "Research defaults, dates, paths, thresholds, feature-set names."),
        ("Data adapters", "data/prices.py, data/weather.py, data/usda.py", "Price pulls, weather cache/demo adapter, USDA text adapter."),
        ("Feature panel", "src/corn_forecast/features.py", "Weekly price, calendar, weather, text, AI feature joins."),
        ("Main target test", "src/corn_forecast/price_target_tests.py", "Fixed 2 percent three-class target plus return-regression diagnostics."),
        ("Return strategy", "src/corn_forecast/expected_return_strategy.py", "Expected-return models, trading threshold, strategy returns."),
        ("Threshold robustness", "src/corn_forecast/threshold_selection.py", "Volatility-adjusted 3-class target selection."),
        ("Binary direction", "src/corn_forecast/models.py, strategy.py", "Secondary up/down classifier and trading backtest."),
        ("WWCB/AI text", "src/corn_forecast/text/*.py, scripts/*.py", "PDF download/parse and GLM/mock structured AI features."),
        ("Report generation", "src/corn_forecast/reports.py, scripts/build_project_notebook.py", "Figures, markdown, notebook, standalone HTML."),
        ("Tests", "tests/*.py", "37 tests covering adapters, features, models, targets, strategy, parser, AI features."),
    ]
    return pd.DataFrame(rows, columns=["area", "files", "role"])


def _task_map() -> pd.DataFrame:
    rows = [
        ("baseline", "Current fixed 2 percent classification baseline", "price_target_tests.json, price_target_predictions.csv"),
        ("research", "Main experiment bundle", "classification, expected-return, threshold, notebook"),
        ("core", "Feature panel plus binary direction report", "feature_panel.parquet, metrics.json, figures"),
        ("docs", "Final report, notebook, ChartBook", "reports/html, reports/notebooks, reports/chartbook"),
        ("refresh_data", "Explicit network refresh", "Yahoo prices, USDA releases, weather cache/catalog"),
        ("wwcb_*", "Optional text/AI feature pipeline", "WWCB manifest, parsed text, ai_weekly.parquet"),
        ("tests", "Project test suite", "37 tests"),
    ]
    return pd.DataFrame(rows, columns=["task", "purpose", "main outputs"])


def _prediction_summary(path: Path) -> dict:
    frame = _read_table(path)
    if frame is None or frame.empty or "week" not in frame.columns:
        return {"rows": 0, "weeks": 0, "first_week": "", "last_week": ""}
    weeks = pd.to_datetime(frame["week"])
    return {"rows": len(frame), "weeks": weeks.nunique(), "first_week": weeks.min().date(), "last_week": weeks.max().date()}


def _build_report_context() -> dict:
    feature_panel = _read_table(ROOT / "data" / "processed" / "feature_panel.parquet")
    price_metrics = _metrics_frame(_read_json(ROOT / "reports" / "price_target_tests.json"))
    expected_metrics = _metrics_frame(_read_json(ROOT / "reports" / "expected_return_metrics.json"))
    binary_metrics = _metrics_frame(_read_json(ROOT / "reports" / "metrics.json"))
    threshold_metrics = _metrics_frame(_read_json(ROOT / "reports" / "threshold_selection.json"))

    artifact_shapes = _shape_rows(
        [
            ROOT / "data" / "raw" / "prices_CORN.csv",
            ROOT / "data" / "raw" / "usda_releases.csv",
            ROOT / "data" / "interim" / "weather_weekly.parquet",
            ROOT / "data" / "interim" / "ai_weekly.parquet",
            ROOT / "data" / "processed" / "feature_panel.parquet",
            ROOT / "reports" / "price_target_predictions.csv",
            ROOT / "reports" / "expected_return_predictions.csv",
            ROOT / "reports" / "threshold_selection_predictions.csv",
            ROOT / "reports" / "predictions.csv",
        ]
    )

    if feature_panel is not None and not feature_panel.empty:
        feature_summary = pd.DataFrame(
            [
                {
                    "rows": len(feature_panel),
                    "columns": len(feature_panel.columns),
                    "first_week": pd.to_datetime(feature_panel["week"]).min().date(),
                    "last_week": pd.to_datetime(feature_panel["week"]).max().date(),
                    "price_features": sum(column.startswith("price_") for column in feature_panel.columns),
                    "calendar_features": sum(column.startswith("calendar_") for column in feature_panel.columns),
                    "weather_features": sum(column.startswith("weather_") for column in feature_panel.columns),
                    "text_features": sum(column.startswith("text_") for column in feature_panel.columns),
                    "ai_features": sum(column.startswith("ai_") for column in feature_panel.columns),
                }
            ]
        )
    else:
        feature_summary = pd.DataFrame()

    class_metrics = price_metrics[price_metrics.get("target", pd.Series(dtype=str)).astype(str).str.contains("3class", na=False)].copy()
    return_metrics = price_metrics[price_metrics.get("target", pd.Series(dtype=str)).astype(str).eq("next_week_log_return")].copy()
    expected_metrics = _sort_desc(expected_metrics, "strategy_sharpe")
    threshold_metrics = _sort_desc(threshold_metrics, "strategy_sharpe")
    binary_metrics = _sort_desc(binary_metrics, "strategy_sharpe")
    class_metrics = _sort_desc(class_metrics, "balanced_accuracy_present_classes")
    return_metrics = _sort_desc(return_metrics, "direction_accuracy")

    oos = _prediction_summary(ROOT / "reports" / "price_target_predictions.csv")
    best_class = class_metrics.iloc[0] if not class_metrics.empty else pd.Series(dtype=object)
    best_expected = expected_metrics.iloc[0] if not expected_metrics.empty else pd.Series(dtype=object)
    best_threshold = threshold_metrics.iloc[0] if not threshold_metrics.empty else pd.Series(dtype=object)
    best_binary = binary_metrics.iloc[0] if not binary_metrics.empty else pd.Series(dtype=object)

    cards = pd.DataFrame(
        [
            {
                "item": "Frozen sample",
                "result": (
                    f"{feature_summary.iloc[0]['first_week']} to {feature_summary.iloc[0]['last_week']}, "
                    f"{int(feature_summary.iloc[0]['rows'])} weekly rows"
                    if not feature_summary.empty
                    else "missing feature panel"
                ),
            },
            {
                "item": "OOS window",
                "result": f"{oos['first_week']} to {oos['last_week']}, {oos['weeks']} weeks / {oos['rows']} prediction rows",
            },
            {
                "item": "Main fixed-band classifier",
                "result": (
                    f"{best_class.get('feature_set', '')}: balanced acc "
                    f"{_format_cell('balanced_accuracy_present_classes', _metric_float(best_class, 'balanced_accuracy_present_classes'))}, "
                    f"macro F1 {_format_cell('macro_f1', _metric_float(best_class, 'macro_f1'))}"
                    if not best_class.empty
                    else "not generated"
                ),
            },
            {
                "item": "Best expected-return strategy",
                "result": (
                    f"{best_expected.get('run', '')}: return "
                    f"{_format_cell('strategy_total_return', _metric_float(best_expected, 'strategy_total_return'))}, "
                    f"Sharpe {_format_cell('strategy_sharpe', _metric_float(best_expected, 'strategy_sharpe'))}"
                    if not best_expected.empty
                    else "not generated"
                ),
            },
            {
                "item": "Best volatility-threshold strategy",
                "result": (
                    f"{best_threshold.get('run', '')}: return "
                    f"{_format_cell('strategy_total_return', _metric_float(best_threshold, 'strategy_total_return'))}, "
                    f"Sharpe {_format_cell('strategy_sharpe', _metric_float(best_threshold, 'strategy_sharpe'))}"
                    if not best_threshold.empty
                    else "not generated"
                ),
            },
            {
                "item": "Secondary binary direction result",
                "result": (
                    f"{best_binary.get('run', '')}: return "
                    f"{_format_cell('strategy_total_return', _metric_float(best_binary, 'strategy_total_return'))}, "
                    f"Sharpe {_format_cell('strategy_sharpe', _metric_float(best_binary, 'strategy_sharpe'))}"
                    if not best_binary.empty
                    else "not generated"
                ),
            },
        ]
    )

    class_distribution = pd.DataFrame()
    if not class_metrics.empty:
        class_row = class_metrics.iloc[0]
        class_distribution = pd.DataFrame(
            [
                {"class": "down <= -2%", "weeks": _metric_float(class_row, "n_down", 0)},
                {"class": "flat", "weeks": _metric_float(class_row, "n_flat", 0)},
                {"class": "up >= +2%", "weeks": _metric_float(class_row, "n_up", 0)},
            ]
        )

    strategy_frames = []
    for label, frame in (
        ("expected return", expected_metrics),
        ("vol threshold", threshold_metrics),
        ("binary secondary", binary_metrics),
    ):
        if not frame.empty and "strategy_sharpe" in frame.columns:
            temp = frame[["run", "strategy_sharpe", "strategy_total_return"]].copy()
            temp["objective"] = label
            temp["label"] = temp["objective"] + " / " + temp["run"].astype(str)
            strategy_frames.append(temp)
    strategy_comparison = (
        pd.concat(strategy_frames, ignore_index=True).sort_values("strategy_sharpe", ascending=False).head(10)
        if strategy_frames
        else pd.DataFrame()
    )

    caveats = _build_caveats(class_metrics, expected_metrics, threshold_metrics, binary_metrics)
    return {
        "feature_panel": feature_panel,
        "artifact_shapes": artifact_shapes,
        "feature_summary": feature_summary,
        "price_metrics": price_metrics,
        "class_metrics": class_metrics,
        "return_metrics": return_metrics,
        "expected_metrics": expected_metrics,
        "threshold_metrics": threshold_metrics,
        "binary_metrics": binary_metrics,
        "cards": cards,
        "class_distribution": class_distribution,
        "strategy_comparison": strategy_comparison,
        "caveats": caveats,
        "source_map": _source_map(),
        "task_map": _task_map(),
    }


def _build_caveats(
    class_metrics: pd.DataFrame,
    expected_metrics: pd.DataFrame,
    threshold_metrics: pd.DataFrame,
    binary_metrics: pd.DataFrame,
) -> List[str]:
    caveats = []
    if not class_metrics.empty:
        row = class_metrics.iloc[0]
        n_test = _metric_float(row, "n_test", 0)
        n_flat = _metric_float(row, "n_flat", 0)
        if n_test:
            caveats.append(
                "The fixed 2 percent target is imbalanced: "
                f"{int(n_flat)} of {int(n_test)} OOS weeks are flat. Accuracy alone is not enough."
            )
        price_only = class_metrics[class_metrics["feature_set"] == "price_only"]
        price_calendar = class_metrics[class_metrics["feature_set"] == "price_calendar"]
        if not price_only.empty and not price_calendar.empty:
            delta = _metric_float(price_calendar.iloc[0], "balanced_accuracy_present_classes") - _metric_float(
                price_only.iloc[0], "balanced_accuracy_present_classes"
            )
            if delta < 0:
                caveats.append(
                    "Calendar seasonality does not improve the main fixed-band classifier in this run; "
                    f"balanced accuracy is {abs(delta):.1%} lower than price-only."
                )
    if not expected_metrics.empty and expected_metrics["r2"].dropna().lt(0).all():
        caveats.append("All expected-return regressions have negative OOS R2, so trading metrics should be treated as fragile.")
    if threshold_metrics.empty:
        caveats.append("Volatility-threshold selection outputs are missing; run `uv run --extra dev doit select_threshold`.")
    if not binary_metrics.empty:
        caveats.append("The binary direction results use a different target (`target_up_next`) and are secondary, not the main 2 percent classification result.")
    caveats.append("Optional weather/text/AI data exist locally, but the main default feature sets are still `price_only` and `price_calendar`.")
    caveats.append("Generated report and data outputs are ignored by git; rerun `uv run --extra dev doit docs` before submission.")
    return caveats


def _build_final_report_markdown(context: dict, generated_at: str) -> str:
    class_table = _display_frame(
        context["class_metrics"],
        ["feature_set", "accuracy", "balanced_accuracy_present_classes", "macro_f1", "n_down", "n_flat", "n_up", "n_test", "n_folds"],
    )
    expected_table = _display_frame(
        context["expected_metrics"],
        ["run", "feature_set", "estimator", "mae", "rmse", "r2", "direction_accuracy", "trade_frequency", "strategy_total_return", "strategy_sharpe", "max_drawdown"],
    )
    threshold_table = _display_frame(
        context["threshold_metrics"],
        ["run", "k", "feature_set", "accuracy", "balanced_accuracy_present_classes", "macro_f1", "strategy_total_return", "strategy_sharpe", "max_drawdown"],
    )
    binary_table = _display_frame(
        context["binary_metrics"],
        ["run", "accuracy", "balanced_accuracy", "f1", "roc_auc", "strategy_total_return", "strategy_sharpe", "max_drawdown"],
    )
    figure_lines = []
    for figure in context.get("chartbook_figure_paths", context.get("figure_paths", [])):
        title = figure.stem.replace("_", " ").title()
        rel = os.path.relpath(figure, DEFAULT_REPORT_MD.parent)
        figure_lines.extend([f"### {title}", "", f"![{title}]({Path(rel).as_posix()})", ""])
    lines = [
        "# Final Report: CORN ETF Trading Signal Pipeline",
        "",
        f"Generated: `{generated_at}`.",
        "",
        "## How To Open",
        "",
        "```bash",
        "open reports/chartbook/index.html",
        "open reports/html/corn_forecast_workflow.html",
        "```",
        "",
        "## Executive Summary",
        "",
        _markdown_table(_display_frame(context["cards"], ["item", "result"])),
        "",
        "## Strategy Ranking Snapshot",
        "",
        _markdown_table(_display_frame(context["strategy_comparison"], ["objective", "run", "strategy_total_return", "strategy_sharpe"], max_rows=10)),
        "",
        "## Main Result: Fixed 2 Percent Three-Class Target",
        "",
        _markdown_table(class_table),
        "",
        "Interpretation: the current fixed-band classifier is weak; the price-only baseline is stronger than price+calendar on balanced accuracy in this run.",
        "",
        "## Auxiliary Expected-Return Strategy",
        "",
        _markdown_table(expected_table),
        "",
        "## Volatility-Adjusted Threshold Check",
        "",
        _markdown_table(threshold_table),
        "",
        "## Secondary Binary Direction Pipeline",
        "",
        _markdown_table(binary_table),
        "",
        "## Figures",
        "",
        *(figure_lines if figure_lines else ["No generated figures available.", ""]),
        "## Data And Code Coverage",
        "",
        _markdown_table(_display_frame(context["feature_summary"], list(context["feature_summary"].columns))),
        "",
        _markdown_table(_display_frame(context["artifact_shapes"], ["artifact", "exists", "rows", "columns"], max_rows=30)),
        "",
        _markdown_table(_display_frame(context["source_map"], ["area", "files", "role"], max_rows=30)),
        "",
        "## Problems And Caveats",
        "",
    ]
    lines.extend([f"- {item}" for item in context["caveats"]])
    lines.extend(
        [
            "",
            "## Reproducibility Commands",
            "",
            "```bash",
            "uv sync --python 3.12 --extra dev --extra docs",
            "uv run --extra dev doit research",
            "uv run --extra dev doit docs",
            "uv run --extra dev doit tests",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def _html_table(frame: pd.DataFrame, max_rows: int = 20) -> str:
    if frame is None or frame.empty:
        return "<p>No local artifact available.</p>"
    view = frame.head(max_rows).copy()
    return view.to_html(index=False, escape=True, border=0, classes="dataframe")


def _html_bar_chart(frame: pd.DataFrame, label_col: str, value_col: str, value_name: str, percent: bool = False) -> str:
    if frame is None or frame.empty or label_col not in frame.columns or value_col not in frame.columns:
        return "<p>No local artifact available.</p>"
    data = frame[[label_col, value_col]].dropna().copy()
    if data.empty:
        return "<p>No local artifact available.</p>"
    max_abs = max(abs(float(value)) for value in data[value_col])
    max_abs = max_abs if max_abs else 1.0
    rows = [
        "<div class='bar-chart'>",
        "<style>.bar-row{display:grid;grid-template-columns:220px 1fr 90px;gap:10px;align-items:center;margin:7px 0}.bar-track{height:16px;background:#eef1f4;border-radius:3px;overflow:hidden}.bar-fill{height:16px;background:#2f6f9f}.bar-fill.neg{background:#b95f4b}.bar-label{font-size:13px}.bar-value{font-variant-numeric:tabular-nums;text-align:right;font-size:13px}</style>",
    ]
    for _, row in data.iterrows():
        value = float(row[value_col])
        width = abs(value) / max_abs * 100.0
        formatted = f"{value:.1%}" if percent else (f"{value:,.0f}" if value.is_integer() else f"{value:.3f}")
        rows.append(
            "<div class='bar-row'>"
            f"<div class='bar-label'>{escape(str(row[label_col]))}</div>"
            "<div class='bar-track'>"
            f"<div class='bar-fill {'neg' if value < 0 else ''}' style='width:{width:.1f}%'></div>"
            "</div>"
            f"<div class='bar-value'>{escape(formatted)}</div>"
            "</div>"
        )
    rows.append(f"<p><strong>{escape(value_name)}</strong></p>")
    rows.append("</div>")
    return "\n".join(rows)


def _save_figure(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_class_distribution(context: dict) -> Optional[Path]:
    frame = context["class_distribution"]
    if frame.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#b95f4b", "#7a8699", "#2f6f9f"]
    ax.bar(frame["class"], frame["weeks"], color=colors)
    ax.set_title("OOS fixed 2 percent class distribution")
    ax.set_ylabel("Weeks")
    ax.grid(axis="y", alpha=0.25)
    for index, value in enumerate(frame["weeks"]):
        ax.text(index, float(value), f"{int(value)}", ha="center", va="bottom", fontsize=9)
    return _save_figure(fig, FIGURE_DIR / "final_class_distribution.png")


def _plot_strategy_bar(context: dict, column: str, title: str, filename: str, percent: bool = False) -> Optional[Path]:
    frame = context["strategy_comparison"]
    if frame.empty or column not in frame.columns:
        return None
    data = frame[["label", column]].dropna().copy().sort_values(column, ascending=True).tail(10)
    if data.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, max(4.5, 0.45 * len(data) + 1.2)))
    colors = ["#b95f4b" if value < 0 else "#2f6f9f" for value in data[column]]
    ax.barh(data["label"], data[column], color=colors)
    ax.axvline(0, color="#40454f", linewidth=0.9)
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.25)
    ax.tick_params(axis="y", labelsize=8)
    for index, value in enumerate(data[column]):
        label = f"{value:.1%}" if percent else f"{value:.3f}"
        offset = 0.003 if percent else 0.01
        ax.text(value + (offset if value >= 0 else -offset), index, label, va="center", ha="left" if value >= 0 else "right", fontsize=8)
    return _save_figure(fig, FIGURE_DIR / filename)


def _plot_cumulative_returns(path: Path, group_col: str, filename: str, title: str, max_models: int = 6) -> Optional[Path]:
    frame = _read_table(path)
    required = {"week", group_col, "cum_strategy_return", "cum_benchmark_return"}
    if frame is None or frame.empty or not required.issubset(frame.columns):
        return None
    data = frame.copy()
    data["week"] = pd.to_datetime(data["week"])
    models = list(data[group_col].dropna().astype(str).unique())[:max_models]
    if not models:
        return None
    fig, ax = plt.subplots(figsize=(9, 4.8))
    palette = ["#2f6f9f", "#3f8f62", "#8a6bb8", "#c47a3a", "#5b8fa8", "#b95f4b"]
    for index, model in enumerate(models):
        subset = data[data[group_col].astype(str) == model].sort_values("week")
        ax.plot(subset["week"], subset["cum_strategy_return"], label=model, linewidth=1.7, color=palette[index % len(palette)])
    benchmark = data.sort_values("week").drop_duplicates("week")
    ax.plot(benchmark["week"], benchmark["cum_benchmark_return"], label="buy and hold", color="#202124", linestyle="--", linewidth=1.3)
    ax.axhline(0, color="#40454f", linewidth=0.8, alpha=0.7)
    ax.set_title(title)
    ax.set_ylabel("Cumulative return")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    ax.yaxis.set_major_formatter(lambda value, _pos: f"{value:.0%}")
    return _save_figure(fig, FIGURE_DIR / filename)


def _plot_fixed_confusion_matrices(context: dict) -> Optional[Path]:
    metrics = _read_json(ROOT / "reports" / "price_target_tests.json") or {}
    run_names = ["price_only_three_class_fixed", "price_calendar_three_class_fixed"]
    runs = [(name, metrics[name]) for name in run_names if name in metrics and "confusion_matrix" in metrics[name]]
    if not runs:
        return None
    fig, axes = plt.subplots(1, len(runs), figsize=(4.6 * len(runs), 4))
    if len(runs) == 1:
        axes = [axes]
    labels = ["down", "flat", "up"]
    for ax, (name, values) in zip(axes, runs):
        matrix = values["confusion_matrix"]
        image = ax.imshow(matrix, cmap="Blues")
        ax.set_title(str(values.get("feature_set", name)))
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_xticks(range(3), labels)
        ax.set_yticks(range(3), labels)
        for y_index, matrix_row in enumerate(matrix):
            for x_index, value in enumerate(matrix_row):
                ax.text(x_index, y_index, str(value), ha="center", va="center", fontsize=9)
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    return _save_figure(fig, FIGURE_DIR / "final_fixed_target_confusion.png")


def _generate_report_figures(context: dict) -> List[Path]:
    figure_paths = [
        _plot_class_distribution(context),
        _plot_strategy_bar(context, "strategy_sharpe", "Generated strategy Sharpe comparison", "final_strategy_sharpe.png"),
        _plot_strategy_bar(context, "strategy_total_return", "Generated strategy total return", "final_strategy_return.png", percent=True),
        _plot_cumulative_returns(
            ROOT / "reports" / "expected_return_predictions.csv",
            "model",
            "final_expected_return_cumulative.png",
            "Expected-return strategy cumulative returns",
        ),
        _plot_cumulative_returns(
            ROOT / "reports" / "threshold_selection_predictions.csv",
            "model",
            "final_threshold_cumulative.png",
            "Volatility-threshold strategy cumulative returns",
        ),
        _plot_fixed_confusion_matrices(context),
    ]
    return [path for path in figure_paths if path is not None]


def _sync_chartbook_figures(paths: Iterable[Path]) -> List[Path]:
    DOCS_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for path in paths:
        destination = DOCS_FIGURE_DIR / path.name
        shutil.copy2(path, destination)
        copied.append(destination)
    return copied


def _markdown_cell(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip() + "\n"}


def _code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.strip() + "\n",
    }


def _html_output_cell(title: str, html: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"title": title},
        "outputs": [
            {
                "output_type": "display_data",
                "metadata": {},
                "data": {"text/html": html, "text/plain": title},
            }
        ],
        "source": f"# {title}\n",
    }


def _image_markdown(path: Path) -> str:
    rel = os.path.relpath(path, DEFAULT_NOTEBOOK.parent)
    title = path.stem.replace("_", " ").title()
    return f"### {title}\n\n![{title}]({Path(rel).as_posix()})"


def build_notebook() -> dict:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    context = _build_report_context()
    context["figure_paths"] = _generate_report_figures(context)
    context["chartbook_figure_paths"] = _sync_chartbook_figures(context["figure_paths"])
    final_report_markdown = _build_final_report_markdown(context, generated_at)

    cells: List[dict] = [
        _markdown_cell(
            f"""
# Final Report: CORN ETF Trading Signal Pipeline

Generated at `{generated_at}`.

This report is generated by `uv run --extra dev doit docs`. It consolidates the code map, data inventory, main results, auxiliary results, figures, and known problems for the CORN ETF weekly trading-signal project.
"""
        ),
        _markdown_cell(
            """
## Open The HTML Outputs

```bash
open reports/chartbook/index.html
open reports/html/corn_forecast_workflow.html
```
"""
        ),
        _markdown_cell(
            """
## Research Design In One Paragraph

The project treats CORN ETF forecasting as a weekly trading-signal problem. The main target is a fixed 2 percent next-week return band:

```text
Y =  1 if next_week_return >= +2%
Y =  0 if -2% < next_week_return < +2%
Y = -1 if next_week_return <= -2%
```

The main comparison is `price_only` versus `price_calendar` under expanding walk-forward validation after `2022-12-31`. Auxiliary checks include expected-return trading, volatility-adjusted target selection, and a secondary binary up/down pipeline.
"""
        ),
        _html_output_cell("Executive summary", _html_table(_display_frame(context["cards"], ["item", "result"]))),
        _html_output_cell(
            "OOS fixed-band class distribution",
            _html_bar_chart(context["class_distribution"], "class", "weeks", "OOS weeks by fixed 2 percent class"),
        ),
        _html_output_cell(
            "Strategy Sharpe comparison",
            _html_bar_chart(context["strategy_comparison"], "label", "strategy_sharpe", "Sharpe by generated strategy"),
        ),
        _html_output_cell(
            "Main fixed 2 percent classification result",
            _html_table(
                _display_frame(
                    context["class_metrics"],
                    ["feature_set", "accuracy", "balanced_accuracy_present_classes", "macro_f1", "n_down", "n_flat", "n_up", "n_test", "n_folds"],
                )
            ),
        ),
        _html_output_cell(
            "Return-regression diagnostic inside target test",
            _html_table(_display_frame(context["return_metrics"], ["feature_set", "mae", "rmse", "r2", "direction_accuracy", "n_test", "n_folds"])),
        ),
        _html_output_cell(
            "Auxiliary expected-return strategy",
            _html_table(
                _display_frame(
                    context["expected_metrics"],
                    ["run", "feature_set", "estimator", "mae", "rmse", "r2", "direction_accuracy", "trade_frequency", "strategy_total_return", "strategy_sharpe", "max_drawdown"],
                )
            ),
        ),
        _html_output_cell(
            "Volatility-adjusted threshold check",
            _html_table(
                _display_frame(
                    context["threshold_metrics"],
                    ["run", "k", "feature_set", "accuracy", "balanced_accuracy_present_classes", "macro_f1", "strategy_total_return", "strategy_sharpe", "max_drawdown"],
                )
            ),
        ),
        _html_output_cell(
            "Secondary binary direction pipeline",
            _html_table(
                _display_frame(
                    context["binary_metrics"],
                    ["run", "accuracy", "balanced_accuracy", "f1", "roc_auc", "strategy_total_return", "strategy_sharpe", "max_drawdown"],
                )
            ),
        ),
        _html_output_cell("Feature panel summary", _html_table(_display_frame(context["feature_summary"], list(context["feature_summary"].columns)))),
        _html_output_cell("Data and report artifacts", _html_table(_display_frame(context["artifact_shapes"], ["artifact", "exists", "rows", "columns"], max_rows=30))),
        _html_output_cell("Code coverage map", _html_table(_display_frame(context["source_map"], ["area", "files", "role"], max_rows=30))),
        _html_output_cell("pydoit task map", _html_table(_display_frame(context["task_map"], ["task", "purpose", "main outputs"], max_rows=20))),
        _markdown_cell("## Problems And Caveats\n\n" + "\n".join(f"- {item}" for item in context["caveats"])),
        _code_cell(
            """
from pathlib import Path
import pandas as pd

root = Path("..").resolve().parent
feature_panel = pd.read_parquet(root / "data/processed/feature_panel.parquet")
price_metrics = pd.read_json(root / "reports/price_target_tests.json").T
expected_return_metrics = pd.read_json(root / "reports/expected_return_metrics.json").T
threshold_metrics = pd.read_json(root / "reports/threshold_selection.json").T
feature_panel.tail()
"""
        ),
    ]

    figure_paths = [Path(path) for path in context.get("figure_paths", [])]
    generated = {path.resolve() for path in figure_paths}
    legacy_paths = [path for path in sorted(FIGURE_DIR.glob("*.png")) if path.resolve() not in generated]
    if figure_paths:
        cells.append(_markdown_cell("## Final Report Figures"))
        for figure in figure_paths:
            cells.append(_markdown_cell(_image_markdown(figure)))
    if legacy_paths:
        cells.append(_markdown_cell("## Secondary Binary Direction Figures"))
        for figure in legacy_paths:
            cells.append(_markdown_cell(_image_markdown(figure)))

    cells.append(
        _markdown_cell(
            """
## Generated Outputs

```text
reports/notebooks/corn_forecast_workflow.ipynb
reports/html/corn_forecast_workflow.html
reports/chartbook/index.html
```

Open the HTML outputs on macOS:

```bash
open reports/chartbook/index.html
open reports/html/corn_forecast_workflow.html
```

The notebook and HTML report are generated artifacts. Source documentation lives in `docs_src/project_workflow.md`; ChartBook configuration lives in `chartbook.toml`; workflow automation lives in `dodo.py`.
"""
        )
    )

    DEFAULT_REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT_MD.write_text(final_report_markdown, encoding="utf-8")

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html_lines = []
    in_code = False
    code_lines = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            close_list()
            if in_code:
                html_lines.append("<pre><code>" + escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if stripped.startswith("<img "):
            close_list()
            html_lines.append(stripped)
            continue
        if stripped.startswith("#"):
            close_list()
            level = min(len(stripped) - len(stripped.lstrip("#")), 6)
            text = stripped[level:].strip()
            html_lines.append(f"<h{level}>{escape(text)}</h{level}>")
        elif stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{escape(stripped[2:])}</li>")
        elif stripped:
            close_list()
            html_lines.append(f"<p>{escape(stripped)}</p>")
        else:
            close_list()
    close_list()
    return "\n".join(html_lines)


def _image_to_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_html(notebook: dict) -> str:
    body = []
    for cell in notebook["cells"]:
        if cell["cell_type"] == "markdown":
            source = cell.get("source", "")
            if "![" in source and "](" in source:
                source = _embed_markdown_images(source)
            body.append(_markdown_to_html(source))
        elif cell["cell_type"] == "code":
            source = cell.get("source", "")
            if source.strip():
                body.append("<details><summary>Code</summary><pre><code>" + escape(source) + "</code></pre></details>")
            for output in cell.get("outputs", []):
                html = output.get("data", {}).get("text/html")
                if html:
                    body.append(html)
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>CORN ETF Trading Signal Workflow Report</title>"
        "<style>"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:40px;line-height:1.55;color:#202124;}"
        "h1,h2,h3{line-height:1.2;margin-top:1.6em;} code,pre{background:#f6f8fa;border-radius:6px;}"
        "pre{padding:12px;overflow:auto;} code{padding:2px 4px;} table.dataframe{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 28px;}"
        "table.dataframe th,table.dataframe td{border:1px solid #d0d7de;padding:6px 8px;text-align:left;vertical-align:top;}"
        "table.dataframe th{background:#f6f8fa;} img{max-width:100%;height:auto;border:1px solid #d0d7de;}"
        "details{margin:12px 0;}"
        "</style></head><body>"
        + "\n".join(body)
        + "</body></html>"
    )


def _embed_markdown_images(source: str) -> str:
    result = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("![") and "](" in stripped and stripped.endswith(")"):
            alt = stripped[2 : stripped.index("]")]
            rel = stripped[stripped.index("](") + 2 : -1]
            path = (DEFAULT_NOTEBOOK.parent / rel).resolve()
            if path.exists() and path.suffix.lower() == ".png":
                result.append(f'<img alt="{escape(alt)}" src="{_image_to_data_uri(path)}">')
                continue
        result.append(line)
    return "\n".join(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build project workflow notebook and HTML report.")
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    notebook = build_notebook()
    args.notebook.parent.mkdir(parents=True, exist_ok=True)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.notebook.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    args.html.write_text(render_html(notebook), encoding="utf-8")
    print(f"Wrote notebook: {args.notebook}")
    print(f"Wrote HTML: {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
