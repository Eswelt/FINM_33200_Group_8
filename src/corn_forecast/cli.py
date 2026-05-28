import argparse
from pathlib import Path

import pandas as pd

from corn_forecast.config import ProjectConfig
from corn_forecast.data.prices import load_prices
from corn_forecast.data.usda import load_usda_releases
from corn_forecast.data.weather import load_weather_features
from corn_forecast.expected_return_strategy import evaluate_expected_return_strategy
from corn_forecast.features import build_feature_panel
from corn_forecast.models import train_evaluate
from corn_forecast.paths import PROJECT_ROOT, ensure_project_dirs
from corn_forecast.price_target_tests import run_price_only_target_tests
from corn_forecast.reports import make_report_artifacts, save_metrics, save_predictions
from corn_forecast.storage import read_table, table_exists, write_table
from corn_forecast.threshold_selection import evaluate_volatility_thresholds
from corn_forecast.volatility import evaluate_volatility_forecast


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Repository root for data/report paths.")
    parser.add_argument("--symbol", default="CORN", help="Yahoo Finance symbol to model.")
    parser.add_argument("--start", default="2011-01-01", help="Start date for data collection.")
    parser.add_argument("--end", default=None, help="End date for data collection.")
    parser.add_argument("--split-date", default="2022-12-31", help="Last week before the first walk-forward test fold.")
    parser.add_argument("--test-window-weeks", type=int, default=13, help="Weeks in each out-of-sample test fold.")
    parser.add_argument("--retrain-step-weeks", type=int, default=13, help="Weeks between expanding-window retrains.")
    parser.add_argument(
        "--validation-scheme",
        choices=("expanding", "rolling"),
        default="expanding",
        help="Use all past data or a fixed-length rolling training window.",
    )
    parser.add_argument("--train-window-weeks", type=int, default=260, help="Training weeks for rolling validation.")
    parser.add_argument("--long-threshold", type=float, default=0.55, help="P(up) needed to hold a long position.")
    parser.add_argument("--short-threshold", type=float, default=0.45, help="P(up) below which shorts are allowed.")
    parser.add_argument("--allow-short", action="store_true", help="Use long/short positions instead of long/flat.")
    parser.add_argument("--transaction-cost-bps", type=float, default=5.0, help="One-way turnover cost in basis points.")
    parser.add_argument("--buffer-bps", type=float, default=25.0, help="Minimum expected-return buffer above costs.")
    parser.add_argument("--fixed-return-threshold", type=float, default=0.02, help="Fixed return band for 3-class target tests.")
    parser.add_argument(
        "--feature-sets",
        default="price_only,price_calendar",
        help="Comma-separated feature sets for modular prediction pipelines.",
    )
    parser.add_argument("--demo", action="store_true", help="Use deterministic offline demo data.")
    parser.add_argument(
        "--threshold-grid",
        default="1.0",
        help="Comma-separated k values for volatility-adjusted target selection.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CORN ETF one-week direction forecasting MVP.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in (
        "fetch-prices",
        "fetch-usda",
        "fetch-weather",
        "build-features",
        "train-evaluate",
        "test-price-targets",
        "classify-move",
        "select-threshold",
        "return-strategy",
        "volatility",
        "make-report",
        "all",
    ):
        add_common_options(subparsers.add_parser(name))
    return parser


def fetch_prices(config: ProjectConfig, demo: bool) -> Path:
    prices = load_prices(symbol=config.symbol, start=config.start, end=config.end, demo=demo)
    path = write_table(prices, config.raw_prices_path)
    print(f"Wrote prices: {path}")
    return path


def fetch_usda(config: ProjectConfig, demo: bool) -> Path:
    releases = load_usda_releases(start=config.start, end=config.end, demo=demo)
    path = write_table(releases, config.raw_usda_path)
    print(f"Wrote USDA releases: {path}")
    return path


def fetch_weather(config: ProjectConfig, demo: bool) -> Path:
    weather = load_weather_features(
        start=config.start,
        end=config.end,
        cache_path=config.weather_path,
        demo=demo,
        bbox=config.corn_belt_bbox,
        catalog_path=config.weather_catalog_path,
    )
    path = write_table(weather, config.weather_path)
    print(f"Wrote weather features: {path}")
    return path


def load_prices_for_config(config: ProjectConfig, demo: bool):
    if not demo and table_exists(config.raw_prices_path):
        return filter_prices_for_config(read_table(config.raw_prices_path), config)
    prices = load_prices(symbol=config.symbol, start=config.start, end=config.end, demo=demo)
    return filter_prices_for_config(prices, config)


def build_features(config: ProjectConfig) -> Path:
    prices = read_table(config.raw_prices_path)
    prices = filter_prices_for_config(prices, config)
    panel = build_model_panel(config, prices)
    path = write_table(panel, config.panel_path)
    print(f"Wrote feature panel: {path}")
    return path


def filter_prices_for_config(prices: pd.DataFrame, config: ProjectConfig) -> pd.DataFrame:
    """Apply the configured research window to cached raw prices."""
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"]).dt.tz_localize(None)
    if config.start:
        frame = frame[frame["date"] >= pd.Timestamp(config.start)]
    if config.end:
        frame = frame[frame["date"] <= pd.Timestamp(config.end)]
    return frame.sort_values("date").reset_index(drop=True)


def build_model_panel(config: ProjectConfig, prices):
    weather = read_table(config.weather_path) if table_exists(config.weather_path) else None
    usda = read_table(config.raw_usda_path) if table_exists(config.raw_usda_path) else None
    panel = build_feature_panel(prices=prices, weather=weather, usda_releases=usda)
    for extra_path in (config.text_features_path, config.ai_features_path, config.gdelt_features_path):
        if table_exists(extra_path):
            extra = read_table(extra_path)
            if "week" not in extra.columns:
                raise ValueError(f"Weekly feature table must include a week column: {extra_path}")
            extra = extra.copy()
            if extra_path == config.gdelt_features_path:
                extra["week"] = pd.to_datetime(extra["week"]).dt.to_period("W-FRI").dt.end_time.dt.normalize()
                extra = extra.rename(
                    columns={
                        column: f"gdelt_{column}"
                        for column in extra.columns
                        if column != "week" and not column.startswith("gdelt_")
                    }
                )
            else:
                extra["week"] = pd.to_datetime(extra["week"]).dt.normalize()
            panel = panel.merge(extra, on="week", how="left")
    return panel


def train_and_evaluate(config: ProjectConfig) -> None:
    panel = read_table(config.panel_path)
    metrics, predictions = train_evaluate(
        panel=panel,
        split_date=config.split_date,
        test_window_weeks=config.test_window_weeks,
        retrain_step_weeks=config.retrain_step_weeks,
        long_threshold=config.long_threshold,
        short_threshold=config.short_threshold,
        allow_short=config.allow_short,
        transaction_cost_bps=config.transaction_cost_bps,
    )
    save_metrics(metrics, config.metrics_path)
    save_predictions(predictions, config.predictions_path)
    print(f"Wrote metrics: {config.metrics_path}")
    print(f"Wrote predictions: {config.predictions_path}")


def test_price_targets(config: ProjectConfig, demo: bool) -> None:
    prices = load_prices_for_config(config, demo=demo)
    panel = build_model_panel(config, prices)
    feature_sets = [value.strip() for value in config.feature_sets.split(",") if value.strip()]
    metrics, predictions = run_price_only_target_tests(
        panel=panel,
        feature_sets=feature_sets,
        split_date=config.split_date,
        test_window_weeks=config.test_window_weeks,
        retrain_step_weeks=config.retrain_step_weeks,
        three_class_threshold=getattr(config, "fixed_return_threshold", 0.02),
    )
    save_metrics(metrics, config.price_target_metrics_path)
    save_predictions(predictions, config.price_target_predictions_path)
    print(f"Wrote price target metrics: {config.price_target_metrics_path}")
    print(f"Wrote price target predictions: {config.price_target_predictions_path}")


def select_threshold(config: ProjectConfig, demo: bool, threshold_grid: str) -> None:
    prices = load_prices_for_config(config, demo=demo)
    panel = build_feature_panel(prices=prices)
    k_values = [float(value.strip()) for value in threshold_grid.split(",") if value.strip()]
    metrics, predictions = evaluate_volatility_thresholds(
        panel=panel,
        k_values=k_values,
        split_date=config.split_date,
        test_window_weeks=config.test_window_weeks,
        retrain_step_weeks=config.retrain_step_weeks,
        long_probability_threshold=config.long_threshold,
        short_probability_threshold=config.short_threshold,
        allow_short=config.allow_short,
        transaction_cost_bps=config.transaction_cost_bps,
        validation_scheme=getattr(config, "validation_scheme", "expanding"),
        train_window_weeks=getattr(config, "train_window_weeks", 260),
    )
    save_metrics(metrics, config.threshold_metrics_path)
    save_predictions(predictions, config.threshold_predictions_path)
    print(f"Wrote threshold selection metrics: {config.threshold_metrics_path}")
    print(f"Wrote threshold selection predictions: {config.threshold_predictions_path}")


def run_return_strategy(config: ProjectConfig, demo: bool) -> None:
    prices = load_prices_for_config(config, demo=demo)
    panel = build_model_panel(config, prices)
    feature_sets = [value.strip() for value in config.feature_sets.split(",") if value.strip()]
    metrics, predictions = evaluate_expected_return_strategy(
        panel=panel,
        feature_sets=feature_sets,
        split_date=config.split_date,
        test_window_weeks=config.test_window_weeks,
        retrain_step_weeks=config.retrain_step_weeks,
        transaction_cost_bps=config.transaction_cost_bps,
        buffer_bps=config.buffer_bps,
        allow_short=config.allow_short,
        validation_scheme=config.validation_scheme,
        train_window_weeks=config.train_window_weeks,
    )
    save_metrics(metrics, config.expected_return_metrics_path)
    save_predictions(predictions, config.expected_return_predictions_path)
    print(f"Wrote expected-return metrics: {config.expected_return_metrics_path}")
    print(f"Wrote expected-return predictions: {config.expected_return_predictions_path}")


def run_volatility_forecast(config: ProjectConfig, demo: bool) -> None:
    prices = load_prices_for_config(config, demo=demo)
    panel = build_model_panel(config, prices)
    feature_sets = [value.strip() for value in config.feature_sets.split(",") if value.strip()]
    metrics, predictions = evaluate_volatility_forecast(
        panel=panel,
        feature_sets=feature_sets,
        split_date=config.split_date,
        test_window_weeks=config.test_window_weeks,
        retrain_step_weeks=config.retrain_step_weeks,
        validation_scheme=config.validation_scheme,
        train_window_weeks=config.train_window_weeks,
    )
    save_metrics(metrics, config.volatility_metrics_path)
    save_predictions(predictions, config.volatility_predictions_path)
    print(f"Wrote volatility metrics: {config.volatility_metrics_path}")
    print(f"Wrote volatility predictions: {config.volatility_predictions_path}")


def make_report(config: ProjectConfig) -> None:
    make_report_artifacts(
        metrics_path=config.metrics_path,
        predictions_path=config.predictions_path,
        report_path=config.report_path,
        figures_dir=config.root / "reports" / "figures",
    )
    print(f"Wrote report: {config.report_path}")


def run(args: argparse.Namespace) -> int:
    config = ProjectConfig.from_args(args)
    ensure_project_dirs(config.root)

    if args.command == "fetch-prices":
        fetch_prices(config, demo=args.demo)
    elif args.command == "fetch-usda":
        fetch_usda(config, demo=args.demo)
    elif args.command == "fetch-weather":
        fetch_weather(config, demo=args.demo)
    elif args.command == "build-features":
        build_features(config)
    elif args.command == "train-evaluate":
        train_and_evaluate(config)
    elif args.command == "test-price-targets":
        test_price_targets(config, demo=args.demo)
    elif args.command == "classify-move":
        test_price_targets(config, demo=args.demo)
    elif args.command == "select-threshold":
        select_threshold(config, demo=args.demo, threshold_grid=args.threshold_grid)
    elif args.command == "return-strategy":
        run_return_strategy(config, demo=args.demo)
    elif args.command == "volatility":
        run_volatility_forecast(config, demo=args.demo)
    elif args.command == "make-report":
        make_report(config)
    elif args.command == "all":
        fetch_prices(config, demo=args.demo)
        fetch_usda(config, demo=args.demo)
        fetch_weather(config, demo=args.demo)
        build_features(config)
        train_and_evaluate(config)
        make_report(config)
    else:
        raise ValueError(f"Unknown command: {args.command}")
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
