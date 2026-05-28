"""pydoit task graph for the CORN ETF forecasting workflow."""

import shutil
from pathlib import Path


DOIT_CONFIG = {
    "default_tasks": ["all"],
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
DOCS_SRC = ROOT / "docs_src"
OUTPUT = ROOT / "output"
REPORTS = OUTPUT / "report"
FIGURES = REPORTS / "figures"
PYTHON = "PYTHONPATH=src uv run python"

REPORT_FILE_OUTPUTS = [
    REPORTS / "metrics.json",
    REPORTS / "predictions.csv",
    REPORTS / "model_report.md",
    REPORTS / "price_target_tests.json",
    REPORTS / "price_target_predictions.csv",
    REPORTS / "expected_return_metrics.json",
    REPORTS / "expected_return_predictions.csv",
    REPORTS / "volatility_metrics.json",
    REPORTS / "volatility_predictions.csv",
    REPORTS / "threshold_selection.json",
    REPORTS / "threshold_selection_predictions.csv",
    REPORTS / "horizon_robustness_metrics.csv",
    REPORTS / "horizon_robustness_metrics.json",
    REPORTS / "horizon_robustness_predictions.csv",
]

FIGURE_OUTPUTS = [
    FIGURES / "predicted_probabilities.png",
    FIGURES / "roc_curves.png",
    FIGURES / "cumulative_returns.png",
    FIGURES / "final_class_distribution.png",
    FIGURES / "final_expected_return_cumulative.png",
    FIGURES / "final_fixed_target_confusion.png",
    FIGURES / "final_strategy_return.png",
    FIGURES / "final_strategy_sharpe.png",
    FIGURES / "final_threshold_cumulative.png",
]

DOC_OUTPUTS = [
    REPORTS / "final_report.md",
    REPORTS / "data_glimpses.md",
    REPORTS / "figures",
    REPORTS / "notebooks",
    REPORTS / "chartbook",
    ROOT / "reports",
]

LEGACY_REPORT_GLOBS = [
    DOCS_SRC / "reports" / "*.csv",
    DOCS_SRC / "reports" / "*.json",
    DOCS_SRC / "reports" / "*.md",
    DOCS_SRC / "reports" / "figures" / "*",
]

LEGACY_OUTPUTS = [
    DOCS_SRC / "final_report.md",
    DOCS_SRC / "data_glimpses.md",
    DOCS_SRC / "figures",
    DOCS_SRC / "reports" / "notebooks",
    DOCS_SRC / "reports" / "html",
    DOCS_SRC / "reports" / "chartbook",
]


def _path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _existing(paths):
    return [_path(path) for path in paths if path.exists()]


def _cli(command: str, *args: str) -> str:
    return " ".join((f"{PYTHON} -m cli", command, *args))


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _clean_paths(paths) -> None:
    for path in paths:
        if path.exists() or path.is_symlink():
            _remove_path(path)


def _clean_globs(patterns) -> None:
    for pattern in patterns:
        for path in pattern.parent.glob(pattern.name):
            if path.name == ".gitkeep":
                continue
            _remove_path(path)


def _clean_report_files(paths) -> None:
    _clean_paths(paths)


def _clean_model_report_outputs() -> None:
    _clean_paths([REPORTS / "model_report.md", *FIGURE_OUTPUTS[:3]])


def _clean_notebook_outputs() -> None:
    _clean_paths(
        [
            REPORTS / "final_report.md",
            REPORTS / "notebooks",
            *FIGURE_OUTPUTS[3:],
        ]
    )


def _clean_chartbook_glimpses() -> None:
    _clean_paths([REPORTS / "data_glimpses.md"])


def _clean_chartbook_outputs() -> None:
    _clean_paths([REPORTS / "chartbook", ROOT / "reports"])


def _clean_generated_outputs() -> None:
    _clean_paths([*REPORT_FILE_OUTPUTS, *FIGURE_OUTPUTS, *DOC_OUTPUTS])
    _clean_paths(LEGACY_OUTPUTS)
    _clean_globs(LEGACY_REPORT_GLOBS)


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
    optional_deps = [
        DATA_RAW / "usda_releases.csv",
        DATA_INTERIM / "weather_weekly.parquet",
        DATA_INTERIM / "weather_weekly.csv",
        DATA_INTERIM / "text_weekly.parquet",
        DATA_INTERIM / "text_weekly.csv",
        DATA_INTERIM / "ai_weekly.parquet",
        DATA_INTERIM / "ai_weekly.csv",
        DATA_INTERIM / "gdelt_weekly_scores.parquet",
        DATA_INTERIM / "gdelt_weekly_scores.csv",
    ]
    return {
        "actions": [_cli("build-features", *COMMON_ARGS)],
        "file_dep": [_path(DATA_RAW / "prices_CORN.csv")] + _existing(optional_deps),
        "targets": [_path(DATA_PROCESSED / "feature_panel.parquet")],
        "uptodate": [False],
    }


def task_train_evaluate():
    """Run the binary direction pipeline and trading report inputs."""
    return {
        "actions": [
            (_clean_report_files, [[REPORTS / "metrics.json", REPORTS / "predictions.csv"]]),
            _cli("train-evaluate", *COMMON_ARGS),
        ],
        "task_dep": ["build_features"],
        "file_dep": [_path(DATA_PROCESSED / "feature_panel.parquet")],
        "targets": [_path(REPORTS / "metrics.json"), _path(REPORTS / "predictions.csv")],
        "uptodate": [False],
    }


def task_model_report():
    """Generate markdown and figure artifacts for the binary direction pipeline."""
    return {
        "actions": [_clean_model_report_outputs, _cli("make-report")],
        "task_dep": ["train_evaluate"],
        "file_dep": [_path(REPORTS / "metrics.json"), _path(REPORTS / "predictions.csv")],
        "targets": [
            _path(REPORTS / "model_report.md"),
            _path(FIGURES / "predicted_probabilities.png"),
            _path(FIGURES / "roc_curves.png"),
            _path(FIGURES / "cumulative_returns.png"),
        ],
        "uptodate": [False],
    }


def task_classify_move():
    """Run the main fixed 2 percent three-class classification experiment."""
    return {
        "actions": [
            (
                _clean_report_files,
                [[REPORTS / "price_target_tests.json", REPORTS / "price_target_predictions.csv"]],
            ),
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
        "uptodate": [False],
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
            (
                _clean_report_files,
                [[REPORTS / "expected_return_metrics.json", REPORTS / "expected_return_predictions.csv"]],
            ),
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
        "uptodate": [False],
    }


def task_volatility():
    """Run the auxiliary next-week absolute-return volatility forecast."""
    return {
        "actions": [
            (
                _clean_report_files,
                [[REPORTS / "volatility_metrics.json", REPORTS / "volatility_predictions.csv"]],
            ),
            _cli(
                "volatility",
                *COMMON_ARGS,
                "--feature-sets",
                FULL_FEATURE_SETS,
            )
        ],
        "file_dep": [_path(DATA_RAW / "prices_CORN.csv")],
        "targets": [_path(REPORTS / "volatility_metrics.json"), _path(REPORTS / "volatility_predictions.csv")],
        "uptodate": [False],
    }


def task_select_threshold():
    """Run expanding-window volatility-adjusted threshold selection."""
    return {
        "actions": [
            (
                _clean_report_files,
                [[REPORTS / "threshold_selection.json", REPORTS / "threshold_selection_predictions.csv"]],
            ),
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
        "uptodate": [False],
    }


def task_select_threshold_rolling():
    """Run rolling-window threshold selection; this overwrites threshold_selection outputs."""
    return {
        "actions": [
            (
                _clean_report_files,
                [[REPORTS / "threshold_selection.json", REPORTS / "threshold_selection_predictions.csv"]],
            ),
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


def task_horizon_robustness():
    """Run 1-, 4-, and 13-week horizon robustness experiments."""
    return {
        "actions": [
            (
                _clean_report_files,
                [
                    [
                        REPORTS / "horizon_robustness_metrics.csv",
                        REPORTS / "horizon_robustness_metrics.json",
                        REPORTS / "horizon_robustness_predictions.csv",
                    ]
                ],
            ),
            f"{PYTHON} -m scripts.run_horizon_robustness",
        ],
        "file_dep": [_path(DATA_RAW / "prices_CORN.csv")],
        "targets": [
            _path(REPORTS / "horizon_robustness_metrics.csv"),
            _path(REPORTS / "horizon_robustness_metrics.json"),
            _path(REPORTS / "horizon_robustness_predictions.csv"),
            _path(DOCS_SRC / "experiments" / "horizon_robustness_results.md"),
        ],
        "uptodate": [False],
    }


def task_wwcb_download():
    """Download USDA Weekly Weather and Crop Bulletin PDFs and a manifest."""
    return {
        "actions": [
            f"{PYTHON} -m scripts.download_wwcb "
            f"--start {START} --end {END} "
            "--output-dir data/external/wwcb_pdfs "
            "--manifest data/interim/wwcb_manifest.csv"
        ],
        "uptodate": [False],
    }


def task_wwcb_download_dry_run():
    """Preview a small WWCB download without writing PDFs."""
    return {
        "actions": [
            f"{PYTHON} -m scripts.download_wwcb "
            "--start 2026-05-01 --end 2026-05-31 --limit 2 --dry-run"
        ],
        "uptodate": [False],
    }


def task_wwcb_parse():
    """Parse downloaded WWCB PDFs into weekly core text."""
    return {
        "actions": [
            f"{PYTHON} -m scripts.parse_wwcb "
            "data/external/wwcb_pdfs --output data/interim/wwcb_core_text.parquet"
        ],
        "task_dep": ["wwcb_download"],
        "file_dep": [_path(DATA_INTERIM / "wwcb_manifest.csv")],
        "uptodate": [False],
    }


def task_wwcb_ai_features():
    """Extract weekly AI features from parsed WWCB text."""
    return {
        "actions": [f"{PYTHON} -m scripts.extract_wwcb_ai_features"],
        "task_dep": ["wwcb_parse"],
        "file_dep": [_path(DATA_INTERIM / "wwcb_core_text.parquet")],
        "uptodate": [False],
    }


def task_wwcb_ai_features_mock():
    """Extract deterministic mock AI features for offline documentation and tests."""
    return {
        "actions": [f"{PYTHON} -m scripts.extract_wwcb_ai_features --mock"],
        "task_dep": ["wwcb_parse"],
        "file_dep": [_path(DATA_INTERIM / "wwcb_core_text.parquet")],
        "uptodate": [False],
    }


def task_wwcb_pipeline():
    """Run the real WWCB text-to-AI feature pipeline."""
    return {
        "task_dep": ["wwcb_ai_features"],
        "actions": None,
    }


def task_wwcb_pipeline_mock():
    """Run the WWCB parser plus deterministic mock AI features."""
    return {
        "task_dep": ["wwcb_ai_features_mock"],
        "actions": None,
    }


def task_notebook():
    """Generate the project workflow notebook and ChartBook report sources."""
    deps = [
        ROOT / "README.md",
        DOCS_SRC / "research_design.md",
        DOCS_SRC / "pipeline_contract.md",
        DOCS_SRC / "project_workflow.md",
    ]
    return {
        "actions": [_clean_notebook_outputs, f"{PYTHON} -m scripts.build_project_notebook"],
        "task_dep": ["experiments"],
        "file_dep": _existing(deps),
        "uptodate": [False],
        "targets": [
            _path(REPORTS / "notebooks" / "corn_forecast_workflow.ipynb"),
            _path(REPORTS / "final_report.md"),
        ],
    }


def task_chartbook_glimpses():
    """Let ChartBook summarize dataframe outputs discovered from this task graph."""
    return {
        "actions": [_clean_chartbook_glimpses, f"{CHARTBOOK} create-data-glimpses -o output/report"],
        "task_dep": ["experiments"],
        "uptodate": [False],
        "targets": [_path(REPORTS / "data_glimpses.md")],
    }


def task_chartbook_build():
    """Build the ChartBook HTML documentation site."""
    return {
        "actions": [
            _clean_chartbook_outputs,
            f"{CHARTBOOK} build output/report/chartbook -f --project-dir .",
            f"{PYTHON} -m scripts.fix_chartbook_assets",
        ],
        "task_dep": ["notebook", "chartbook_glimpses"],
        "file_dep": [
            "chartbook.toml",
            _path(DOCS_SRC / "project_workflow.md"),
            _path(REPORTS / "final_report.md"),
            _path(REPORTS / "data_glimpses.md"),
        ],
        "targets": [_path(REPORTS / "chartbook" / "index.html")],
        "uptodate": [False],
    }


def task_docs():
    """Build the notebook, final report markdown, and ChartBook documentation site."""
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


def task_clean_outputs():
    """Delete generated reports/docs before a fresh local rebuild."""
    return {
        "actions": [_clean_generated_outputs],
        "uptodate": [False],
    }


def task_core():
    """Run the cached data-to-report binary direction pipeline."""
    return {
        "task_dep": ["model_report"],
        "actions": None,
    }


def task_experiments():
    """Run all model experiments used by the final report."""
    return {
        "task_dep": [
            "classify_move",
            "return_strategy",
            "volatility",
            "select_threshold",
            "horizon_robustness",
        ],
        "actions": None,
    }


def task_research():
    """Run the main research experiments and regenerate the notebook report source."""
    return {
        "task_dep": ["experiments", "notebook"],
        "actions": None,
    }


def task_all():
    """Run the full cached local workflow: models, reports, docs, and tests."""
    return {
        "task_dep": ["core", "research", "docs", "tests"],
        "actions": None,
    }


def task_tests():
    """Run the project test suite."""
    return {
        "actions": ["PYTHONPATH=src uv run --extra dev python -m pytest src/tests"],
    }
