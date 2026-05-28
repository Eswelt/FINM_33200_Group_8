# FINM 33200 Group 8: CORN ETF Trading Signal Pipeline

This repository contains a modular weekly forecasting pipeline for `CORN`, the Teucrium Corn ETF. The final project emphasizes forward realized volatility because direction and expected-return forecasts are less stable out of sample.

One auxiliary task is a fixed-threshold three-class classification problem:

```text
Y =  1 if next_week_return >= +2%
Y =  0 if -2% < next_week_return < +2%
Y = -1 if next_week_return <= -2%
```

The implementation stores next-week log returns and converts this arithmetic 2% band to log-return bounds.

The current experiments compare:

- `price_only`: historical price features
- `price_ai`: historical price features plus USDA/GLM scores
- `price_gdelt`: historical price features plus GDELT news scores
- `price_calendar`: historical price features plus agricultural seasonality
- combined calendar, USDA/GLM, and GDELT feature sets

The final write-up focuses on whether crop-season timing, USDA/GLM report scores, and GDELT news scores can forecast the future risk environment.

## Quick Start

```bash
uv sync --python 3.12 --extra dev --extra docs
uv run --extra dev doit baseline
```

This writes:

- `docs_src/reports/price_target_tests.json`
- `docs_src/reports/price_target_predictions.csv`

Generated report outputs are ignored by git. Cached data files live under `data/` and are kept separate from report generation.

## pydoit Workflow

All recurring run commands are collected in `dodo.py`.

List tasks:

```bash
uv run --extra dev doit list
```

Run the current classification baseline:

```bash
uv run --extra dev doit baseline
```

Run the main research experiments and regenerate the notebook/HTML report:

```bash
uv run --extra dev doit research
```

Refresh external data sources explicitly:

```bash
uv run --extra dev doit refresh_data
```

Build the ChartBook documentation site:

```bash
uv run --extra dev --extra docs doit docs
```

Open the generated HTML files on macOS:

```bash
open docs_src/reports/chartbook/index.html
open docs_src/reports/html/corn_forecast_workflow.html
```

Run the full local workflow:

```bash
uv run --extra dev --extra docs doit all
```

Run tests:

```bash
uv run --extra dev doit tests
```

`chartbook` requires Python 3.10 or newer. The existing local Python 3.9 environment can still run the forecasting code and generated notebook script, but the ChartBook site build should be run from Python 3.10+.

The default `baseline`, `research`, and `docs` tasks use the cached frozen data already under `data/`. Run `refresh_data` only when you intentionally want to refresh external sources.

## Underlying CLI Commands

Equivalent CLI command for the current classification baseline:

```bash
PYTHONPATH=src uv run python -m cli classify-move \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --fixed-return-threshold 0.02 \
  --feature-sets price_only,price_calendar
```

Build a shared feature panel after weekly feature tables have been placed under `data/interim/`:

```bash
PYTHONPATH=src uv run python -m cli fetch-prices
PYTHONPATH=src uv run python -m cli build-features
```

Run the auxiliary expected-return pipeline:

```bash
PYTHONPATH=src uv run python -m cli return-strategy \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --feature-sets price_only,price_calendar \
  --transaction-cost-bps 5 \
  --buffer-bps 25
```

The expected-return pipeline predicts next-week log return directly and trades only when the predicted return exceeds transaction costs plus a buffer. It is an auxiliary experiment; the current main target is the fixed 2% arithmetic-return classification task. Internally, the 2% band is converted to log-return bounds before comparing with `target_log_return_next`.

Run the auxiliary volatility pipeline:

```bash
PYTHONPATH=src uv run python -m cli volatility \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --feature-sets price_only,price_calendar,price_calendar_ai
```

The volatility pipeline predicts `abs(next_week_log_return)` and reports both regression diagnostics and a high-volatility classification check based on each training window's 70th percentile absolute return.

## Project Documents

- `docs_src/research_design.md`: research design, target definition, time split, and validation logic
- `docs_src/pipeline_contract.md`: feature-table contract and modular pipeline interface
- `docs_src/project_workflow.md`: consolidated ChartBook workflow documentation
- `chartbook.toml`: ChartBook pipeline metadata, dataframes, notes, and notebook registry
- `dodo.py`: pydoit task graph for all routine commands

## Data Interface

Price data are pulled from Yahoo Finance through `yfinance`.

Weekly feature tables can be added under `data/interim/`:

```text
data/interim/text_weekly.parquet
data/interim/ai_weekly.parquet
data/interim/gdelt_weekly_scores.parquet
```

CSV files with the same stems are also accepted.

Each table must include:

```text
week
```

Column naming convention:

```text
text_*      numeric text features
ai_*        AI-extracted structured features
report_text optional free-text field for TF-IDF
```

Example feature sets:

```text
price_only
price_calendar
price_calendar_text
price_ai
price_gdelt
price_ai_gdelt
price_calendar_ai
price_calendar_gdelt
price_calendar_ai_gdelt
```

## Modeling Design

Main classification target:

```text
next-week arithmetic return down / flat / up using a fixed 2% band
```

Price features:

- 1/2/4/12-week lagged returns
- 4/12-week rolling volatility
- 4/12-week momentum
- 4-week volume change

Calendar features:

- month and quarter
- week-of-year sine/cosine
- planting season dummy
- pollination/weather-risk season dummy
- harvest season dummy
- winter storage season dummy

Models:

- Classification baseline: `LogisticRegression(class_weight="balanced")`
- Auxiliary return models: `Ridge` and `HistGradientBoostingRegressor`
- If `report_text` is present, TF-IDF features are fit inside the model pipeline using training data only.

Validation:

- Main validation: expanding walk-forward
- Out-of-sample period starts after `2022-12-31`
- Test window: 13 weeks
- Retrain step: 13 weeks
- Robustness option: rolling 5-year training window

Evaluation:

- Classification: accuracy, balanced accuracy, macro F1, confusion matrix
- Strategy: total return, annualized return, volatility, Sharpe, max drawdown, turnover
- Volatility: MAE, RMSE, R2, Spearman rank correlation, high-volatility balanced accuracy

## Useful CLI Options

- `--symbol CORN`: Yahoo Finance ticker
- `--start 2011-01-01`: data start date
- `--end YYYY-MM-DD`: data end date
- `--split-date 2022-12-31`: final week before the first out-of-sample fold
- `--test-window-weeks 13`: weeks per test fold
- `--retrain-step-weeks 13`: retraining interval
- `--feature-sets price_only,price_calendar`: comma-separated feature-set list
- `--fixed-return-threshold 0.02`: fixed classification threshold
- `--validation-scheme expanding`: expanding or rolling validation
- `--train-window-weeks 260`: rolling window length
- `--root PATH`: output root
- `--demo`: use deterministic offline sample data

## Tests

```bash
uv run --extra dev doit tests
```

The tests cover target construction, feature joins, pipeline feature-set selection, walk-forward splits, backtest accounting, and CLI smoke tests.
