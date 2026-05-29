"""pydoit task graph for the CORN ETF forecasting workflow."""

from pathlib import Path


DOIT_CONFIG = {
    "default_tasks": ["baseline"],
    "backend": "sqlite3",
    "dep_file": ".doit.db",
}


START = "2011-01-01"
END = "2026-05-15"
SPLIT_DATE = "2022-12-31"
FEATURE_SETS = "price_only,price_calendar"
FULL_FEATURE_SETS = (
    "price_only,price_ai,price_gdelt,price_ai_gdelt,"
    "price_calendar,price_calendar_ai,price_calendar_gdelt,price_calendar_ai_gdelt"
)
FIXED_RETURN_THRESHOLD = "0.02"
TRANSACTION_COST_BPS = "5"
BUFFER_BPS = "25"
CHARTBOOK = "PYTHONPATH=src uv run --extra docs chartbook"

ROOT = Path(__file__).resolve().parent
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
CHARTBOOK_DIR = REPORTS / "chartbook"
DOCS_SRC = ROOT / "docs_src"
PYTHON = "PYTHONPATH=src uv run python"


def _path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _existing(paths):
    return [_path(path) for path in paths if path.exists()]


def _cli(command: str, *args: str) -> str:
    return " ".join((f"{PYTHON} -m corn_forecast.cli", command, *args))


COMMON_ARGS = (
    "--start",
    START,
    "--end",
    END,
    "--split-date",
    SPLIT_DATE,
)


def task_sync():
    """Install runtime, dev, and documentation extras."""
    return {
        "actions": ["uv sync --python 3.12 --extra dev --extra docs"],
    }


def task_fetch_prices():
    """Download CORN daily prices from Yahoo Finance."""
    return {
        "actions": [_cli("fetch-prices", *COMMON_ARGS)],
        "uptodate": [False],
    }


def task_fetch_usda():
    """Download raw USDA release text used by optional text features."""
    return {
        "actions": [_cli("fetch-usda", *COMMON_ARGS)],
        "uptodate": [False],
    }


def task_fetch_weather():
    """Load cached weather features or write the request catalog."""
    return {
        "actions": [_cli("fetch-weather", *COMMON_ARGS)],
        "uptodate": [False],
    }


def task_build_features():
    """Build the shared weekly modeling panel."""
    return {
        "actions": [_cli("build-features", *COMMON_ARGS)],
        "file_dep": [_path(DATA_RAW / "prices_CORN.csv")],
        "targets": [_path(DATA_PROCESSED / "feature_panel.parquet")],
    }


def task_train_evaluate():
    """Run the binary direction pipeline and trading report inputs."""
    return {
        "actions": [_cli("train-evaluate", *COMMON_ARGS)],
        "file_dep": [_path(DATA_PROCESSED / "feature_panel.parquet")],
        "targets": [_path(REPORTS / "metrics.json"), _path(REPORTS / "predictions.csv")],
    }


def task_model_report():
    """Generate markdown and figure artifacts for the binary direction pipeline."""
    return {
        "actions": [_cli("make-report")],
        "file_dep": [_path(REPORTS / "metrics.json"), _path(REPORTS / "predictions.csv")],
        "targets": [
            _path(REPORTS / "model_report.md"),
            _path(FIGURES / "predicted_probabilities.png"),
            _path(FIGURES / "roc_curves.png"),
            _path(FIGURES / "cumulative_returns.png"),
        ],
    }


def task_classify_move():
    """Run the main fixed 2 percent three-class classification experiment."""
    return {
        "actions": [
            _cli(
                "classify-move",
                *COMMON_ARGS,
                "--fixed-return-threshold",
                FIXED_RETURN_THRESHOLD,
                "--feature-sets",
                FULL_FEATURE_SETS,
            )
        ],
        "file_dep": [_path(DATA_RAW / "prices_CORN.csv")],
        "targets": [_path(REPORTS / "price_target_tests.json"), _path(REPORTS / "price_target_predictions.csv")],
    }


def task_test_price_targets():
    """Alias for the fixed-threshold target diagnostics command."""
    return {
        "task_dep": ["classify_move"],
        "actions": None,
    }


def task_return_strategy():
    """Run the auxiliary expected-return trading strategy."""
    return {
        "actions": [
            _cli(
                "return-strategy",
                *COMMON_ARGS,
                "--feature-sets",
                FULL_FEATURE_SETS,
                "--transaction-cost-bps",
                TRANSACTION_COST_BPS,
                "--buffer-bps",
                BUFFER_BPS,
            )
        ],
        "file_dep": [_path(DATA_RAW / "prices_CORN.csv")],
        "targets": [_path(REPORTS / "expected_return_metrics.json"), _path(REPORTS / "expected_return_predictions.csv")],
    }


def task_volatility():
    """Run the auxiliary next-week absolute-return volatility forecast."""
    return {
        "actions": [
            _cli(
                "volatility",
                *COMMON_ARGS,
                "--feature-sets",
                FULL_FEATURE_SETS,
            )
        ],
        "file_dep": [_path(DATA_RAW / "prices_CORN.csv")],
        "targets": [_path(REPORTS / "volatility_metrics.json"), _path(REPORTS / "volatility_predictions.csv")],
    }


def task_select_threshold():
    """Run expanding-window volatility-adjusted threshold selection."""
    return {
        "actions": [
            _cli(
                "select-threshold",
                *COMMON_ARGS,
                "--threshold-grid",
                "1.0",
                "--validation-scheme",
                "expanding",
                "--long-threshold",
                "0.45",
            )
        ],
        "file_dep": [_path(DATA_RAW / "prices_CORN.csv")],
        "targets": [_path(REPORTS / "threshold_selection.json"), _path(REPORTS / "threshold_selection_predictions.csv")],
    }


def task_select_threshold_rolling():
    """Run rolling-window threshold selection; this overwrites threshold_selection outputs."""
    return {
        "actions": [
            _cli(
                "select-threshold",
                *COMMON_ARGS,
                "--threshold-grid",
                "1.0",
                "--validation-scheme",
                "rolling",
                "--train-window-weeks",
                "260",
                "--long-threshold",
                "0.45",
            )
        ],
        "uptodate": [False],
    }


def task_wwcb_download():
    """Download USDA Weekly Weather and Crop Bulletin PDFs and a manifest."""
    return {
        "actions": [
            f"{PYTHON} scripts/download_wwcb.py "
            f"--start {START} --end {END} "
            "--output-dir data/external/wwcb_pdfs "
            "--manifest data/interim/wwcb_manifest.csv"
        ],
        "targets": [_path(DATA_INTERIM / "wwcb_manifest.csv")],
    }


def task_wwcb_parse():
    """Parse downloaded WWCB PDFs into weekly core text."""
    return {
        "actions": [
            f"{PYTHON} scripts/parse_wwcb.py "
            "data/external/wwcb_pdfs --output data/interim/wwcb_core_text.parquet"
        ],
        "file_dep": [_path(DATA_INTERIM / "wwcb_manifest.csv")],
        "targets": [_path(DATA_INTERIM / "wwcb_core_text.parquet")],
    }


def task_wwcb_ai_features():
    """Extract weekly AI features from parsed WWCB text."""
    return {
        "actions": [f"{PYTHON} scripts/extract_wwcb_ai_features.py"],
        "file_dep": [_path(DATA_INTERIM / "wwcb_core_text.parquet")],
        "targets": [_path(DATA_INTERIM / "ai_weekly.parquet"), _path(DATA_INTERIM / "ai_wwcb_raw.parquet")],
    }


def task_wwcb_ai_features_mock():
    """Extract deterministic mock AI features for offline documentation and tests."""
    return {
        "actions": [f"{PYTHON} scripts/extract_wwcb_ai_features.py --mock"],
        "file_dep": [_path(DATA_INTERIM / "wwcb_core_text.parquet")],
        "uptodate": [False],
    }


def task_notebook():
    """Generate the project workflow notebook and standalone HTML report."""
    deps = [
        ROOT / "README.md",
        ROOT / "step_by_step.md",
        ROOT / "pipeline_contract.md",
        DOCS_SRC / "project_workflow.md",
    ]
    return {
        "actions": [f"{PYTHON} scripts/build_project_notebook.py"],
        "file_dep": _existing(deps),
        "uptodate": [False],
        "targets": [
            _path(REPORTS / "notebooks" / "corn_forecast_workflow.ipynb"),
            _path(REPORTS / "html" / "corn_forecast_workflow.html"),
            _path(DOCS_SRC / "final_report.md"),
        ],
    }


def task_chartbook_glimpses():
    """Let ChartBook summarize dataframe outputs discovered from this task graph."""
    return {
        "actions": [f"{CHARTBOOK} create-data-glimpses -o docs_src"],
        "uptodate": [False],
        "targets": [_path(DOCS_SRC / "data_glimpses.md")],
    }


def task_chartbook_build():
    """Build the ChartBook HTML documentation site."""
    return {
        "actions": [
            f"{CHARTBOOK} build reports/chartbook -f --project-dir .",
            f"{PYTHON} scripts/fix_chartbook_assets.py",
        ],
        "file_dep": [
            "chartbook.toml",
            "scripts/fix_chartbook_assets.py",
            _path(DOCS_SRC / "final_figure_analysis.md"),
            _path(DOCS_SRC / "weather_corn_etf_daily_decision_report.md"),
            _path(DOCS_SRC / "project_readme_workflow.md"),
        ],
        "targets": [
            _path(CHARTBOOK_DIR / "index.html"),
            _path(CHARTBOOK_DIR / "cb" / "project_readme_workflow.html"),
            _path(CHARTBOOK_DIR / "cb" / "final_figure_analysis.html"),
            _path(CHARTBOOK_DIR / "cb" / "weather_corn_etf_daily_decision.html"),
            _path(CHARTBOOK_DIR / "cb" / "charts.html"),
        ],
    }


def task_docs():
    """Build the current three-page ChartBook documentation site."""
    return {
        "task_dep": ["chartbook_build"],
        "actions": None,
    }


def task_baseline():
    """Run the current main baseline only."""
    return {
        "task_dep": ["classify_move"],
        "actions": None,
    }


def task_refresh_data():
    """Explicitly refresh external data sources that may require network access."""
    return {
        "task_dep": ["fetch_prices", "fetch_usda", "fetch_weather"],
        "actions": None,
    }


def task_core():
    """Run the cached data-to-report binary direction pipeline."""
    return {
        "task_dep": ["build_features", "train_evaluate", "model_report"],
        "actions": None,
    }


def task_research():
    """Run the main research experiments without rebuilding ChartBook."""
    return {
        "task_dep": ["classify_move", "return_strategy", "volatility", "select_threshold", "notebook"],
        "actions": None,
    }


def task_all():
    """Run the full local workflow, including ChartBook docs."""
    return {
        "task_dep": ["core", "research", "docs"],
        "actions": None,
    }


def task_tests():
    """Run the project test suite."""
    return {
        "actions": ["PYTHONPATH=src uv run pytest"],
    }
