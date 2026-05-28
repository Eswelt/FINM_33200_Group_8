# CORN ETF Trading Signal Workflow

This document is the project-level workflow guide used by ChartBook. It consolidates the research design, command surface, data contracts, modeling tasks, and report-generation path into one reproducible sequence.

## Objective

The project frames CORN ETF forecasting as a weekly trading-signal problem. The main question is:

```text
Can calendar seasonality improve weekly CORN ETF trading signals beyond historical price baselines?
```

The main target is a fixed-threshold three-class next-week arithmetic return label:

```text
Y =  1 if next_week_return >= +2%
Y =  0 if -2% < next_week_return < +2%
Y = -1 if next_week_return <= -2%
```

Because the model panel stores next-week log return, the implementation converts the +/-2% arithmetic band to `log(0.98)` and `log(1.02)` before assigning labels.

The auxiliary experiment predicts next-week log return directly and trades only when the predicted return clears transaction costs plus a buffer.

## Research Timeline

| Setting | Value |
| --- | --- |
| Raw price start | `2011-01-01` |
| Frozen data end | `2026-05-15` |
| Weekly timestamp | Friday close, `W-FRI` |
| Main split date | `2022-12-31` |
| First out-of-sample week | `2023-01-06` |
| Test fold size | 13 weeks |
| Retrain step | 13 weeks |
| Main validation | Expanding walk-forward |
| Robustness validation | Rolling 260-week training window |

Random train/test splits are not used, because the intended deployment is a weekly retrained trading signal.

## Unified pydoit Entrypoints

Install the task runner and project extras:

```bash
uv sync --python 3.12 --extra dev --extra docs
```

List available tasks:

```bash
uv run --extra dev doit list
```

Run the current main baseline:

```bash
uv run --extra dev doit baseline
```

Run the main research experiments and regenerate the notebook report source:

```bash
uv run --extra dev doit research
```

Run the model experiment bundle only:

```bash
uv run --extra dev doit experiments
```

Delete generated reports/docs before a manual fresh rebuild:

```bash
uv run --extra dev doit clean_outputs
```

Refresh external data sources when network access is intended:

```bash
uv run --extra dev doit refresh_data
```

Build the ChartBook site:

```bash
uv run --extra dev --extra docs doit docs
```

Open the generated ChartBook site on macOS:

```bash
open output/report/chartbook/index.html
```

Run the full local workflow:

```bash
uv run --extra dev --extra docs doit
```

Run tests:

```bash
uv run --extra dev doit tests
```

`uv run --extra dev --extra docs doit all` is the explicit task-name form of the same command. `chartbook` requires Python 3.10 or newer. The forecasting package itself remains compatible with the existing project runtime, but the ChartBook documentation extra should be run in a Python 3.10+ environment.

The default `all`, `baseline`, `experiments`, `research`, and `docs` tasks use local cached data. Generated report and documentation tasks clean their previous outputs under `output/report/` before rewriting them, so reruns do not accumulate duplicate ChartBook/report files. The `refresh_data` task is intentionally separate so report generation does not unexpectedly call external services.

## Task Map

| pydoit task | Underlying command | Main outputs |
| --- | --- | --- |
| `fetch_prices` | `cli fetch-prices` | `data/raw/prices_CORN.csv` |
| `fetch_usda` | `cli fetch-usda` | `data/raw/usda_releases.csv` |
| `fetch_weather` | `cli fetch-weather` | `data/interim/weather_weekly.parquet` |
| `refresh_data` | `fetch_prices`, `fetch_usda`, `fetch_weather` | Explicit external data refresh |
| `clean_outputs` | local cleanup callables | Generated `output/report/` cleanup without touching cached raw/interim data |
| `build_features` | `cli build-features` | `data/processed/feature_panel.parquet` |
| `train_evaluate` | `cli train-evaluate` | `output/report/metrics.json`, `output/report/predictions.csv` |
| `model_report` | `cli make-report` | `output/report/model_report.md`, `output/report/figures/*.png` |
| `classify_move` | `cli classify-move` | `output/report/price_target_tests.json`, `output/report/price_target_predictions.csv` |
| `return_strategy` | `cli return-strategy` | `output/report/expected_return_metrics.json`, `output/report/expected_return_predictions.csv` |
| `volatility` | `cli volatility` | `output/report/volatility_metrics.json`, `output/report/volatility_predictions.csv` |
| `select_threshold` | `cli select-threshold` | `output/report/threshold_selection.json`, `output/report/threshold_selection_predictions.csv` |
| `horizon_robustness` | `src/scripts/run_horizon_robustness.py` | `output/report/horizon_robustness_metrics.csv`, `output/report/horizon_robustness_predictions.csv` |
| `experiments` | `classify_move`, `return_strategy`, `volatility`, `select_threshold`, `horizon_robustness` | Full model experiment bundle |
| `notebook` | `src/scripts/build_project_notebook.py` | `output/report/notebooks/corn_forecast_workflow.ipynb`, `output/report/final_report.md` |
| `chartbook_build` | `chartbook build` plus local figure asset sync | `output/report/chartbook/index.html` |
| `all` | `core`, `research`, `docs`, `tests` | Full cached local workflow |

Optional WWCB tasks are also exposed:

```bash
uv run --extra dev doit wwcb_download
uv run --extra dev doit wwcb_download_dry_run
uv run --extra dev doit wwcb_parse
uv run --extra dev doit wwcb_ai_features
uv run --extra dev doit wwcb_ai_features_mock
uv run --extra dev doit wwcb_pipeline_mock
```

The real AI feature task requires a GLM API key. The mock task is deterministic and useful for offline checks.

## Data Flow

The pipeline uses one weekly panel as the modeling contract:

```text
raw prices -> weekly price features -> calendar features -> optional weather/text/AI joins -> model panel
```

The shared model panel is:

```text
data/processed/feature_panel.parquet
```

Each row represents:

```text
week_t, point-in-time X_t, target label/return for t+1
```

Feature families follow prefix conventions:

| Prefix | Meaning |
| --- | --- |
| `price_` | Lagged returns, rolling volatility, momentum, and volume change |
| `calendar_` | Month, quarter, week-of-year cyclic terms, crop-season dummies |
| `weather_` | Optional Corn Belt weather observations and forecasts |
| `text_` | Optional numeric text features from USDA reports |
| `ai_` | Optional structured AI scores extracted from WWCB text |
| `report_text` | Optional free text consumed by TF-IDF inside model pipelines |

Optional teammate-produced feature tables can be dropped into `data/interim/` with a required `week` column:

```text
data/interim/weather_weekly.parquet
data/interim/text_weekly.parquet
data/interim/ai_weekly.parquet
```

CSV files with the same stems are accepted as fallbacks.

## Modeling Design

The main experiment compares:

| Feature set | Description |
| --- | --- |
| `price_only` | Historical price features only |
| `price_calendar` | Price features plus agricultural seasonality |

The fixed 2 percent three-class task uses logistic regression with class balancing. The same walk-forward folds are used for every feature set.

The auxiliary expected-return task compares:

| Estimator | Role |
| --- | --- |
| `ridge` | Linear sanity-check baseline |
| `hgb` | Nonlinear tabular baseline |

The expected-return strategy is long/flat by default:

```text
long if predicted_return > transaction_cost_bps + buffer_bps
flat otherwise
```

Default trading assumptions:

```text
transaction_cost_bps = 5
buffer_bps = 25
trade_threshold = 30 bps
```

## Validation

The main validation scheme is expanding walk-forward:

```text
Fold 1 train: all weeks <= 2022-12-30
Fold 1 test:  2023-01-06 through 2023-03-31

Fold 2 train: all weeks <= 2023-03-31
Fold 2 test:  2023-04-07 through 2023-06-30
```

The rolling robustness scheme uses the latest 260 weeks before each test fold:

```bash
uv run --extra dev doit select_threshold_rolling
```

## Reports

The documentation task writes:

```text
output/report/final_report.md
output/report/data_glimpses.md
output/report/figures/*.png
output/report/notebooks/corn_forecast_workflow.ipynb
output/report/chartbook/index.html
```

Open the HTML outputs:

```bash
open output/report/chartbook/index.html
```

The notebook and final-report markdown summarize current local outputs, including metric tables, prediction file shapes, and generated figures. ChartBook uses `chartbook.toml` to render the notebook and workflow notes into the generated documentation site.

For the most compact submission-ready summary, open `output/report/chartbook/cb/final_report.html`.

## Operational Notes

- Generated data and reports are intentionally ignored by git.
- Use `--demo` CLI options for deterministic offline smoke runs.
- Real price downloads require Yahoo Finance access through `yfinance`.
- Real USDA and WWCB downloads require network access.
- Real AI extraction requires a GLM API key in the environment or `.env.local`.
- Do not compare model variants across different split dates or data-end dates.
