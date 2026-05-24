# FINM 33200 Group 8: CORN ETF Trading Signal Pipeline

This repository contains a modular weekly forecasting pipeline for `CORN`, the Teucrium Corn ETF. The project frames CORN ETF forecasting as a trading-signal problem rather than a pure price-prediction task.

The main task is a fixed-threshold three-class classification problem:

```text
Y =  1 if next_week_return >= +2%
Y =  0 if -2% < next_week_return < +2%
Y = -1 if next_week_return <= -2%
```

The current baseline compares:

- `price_only`: historical price features
- `price_calendar`: historical price features plus agricultural seasonality

The pipeline is designed so that weekly weather, text, and AI-extracted features can be added later through standard feature tables. See `pipeline_contract.md` for the data interface.

## Quick Start

```bash
uv sync --extra dev
uv run python run_classification_baseline.py
```

This writes:

- `reports/price_target_tests.json`
- `reports/price_target_predictions.csv`

Generated data and report outputs are ignored by git.

## Main Commands

Run the current classification baseline:

```bash
uv run python run_classification_baseline.py
```

Equivalent CLI command:

```bash
uv run python -m corn_forecast.cli classify-move \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --fixed-return-threshold 0.02 \
  --feature-sets price_only,price_calendar
```

Build a shared feature panel after weekly feature tables have been placed under `data/interim/`:

```bash
uv run python -m corn_forecast.cli fetch-prices
uv run python -m corn_forecast.cli build-features
```

Run the auxiliary expected-return pipeline:

```bash
uv run python -m corn_forecast.cli return-strategy \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --feature-sets price_only,price_calendar \
  --transaction-cost-bps 5 \
  --buffer-bps 25
```

The expected-return pipeline predicts next-week log return directly and trades only when the predicted return exceeds transaction costs plus a buffer. It is an auxiliary experiment; the current main target is the fixed 2% classification task.

## Project Documents

- `step_by_step.md`: research design, target definition, time split, and validation logic
- `pipeline_contract.md`: feature-table contract and modular pipeline interface
- `run_classification_baseline.py`: one-command baseline runner

## Data Interface

Price data are pulled from Yahoo Finance through `yfinance`.

Optional weekly feature tables can be added under `data/interim/`:

```text
data/interim/weather_weekly.parquet
data/interim/text_weekly.parquet
data/interim/ai_weekly.parquet
```

CSV files with the same stems are also accepted.

Each table must include:

```text
week
```

Column naming convention:

```text
weather_*   weather features
text_*      numeric text features
ai_*        AI-extracted structured features
report_text optional free-text field for TF-IDF
```

Example feature sets:

```text
price_only
price_calendar
price_calendar_weather
price_calendar_text
price_calendar_weather_text
price_calendar_ai
price_calendar_weather_ai
price_calendar_weather_text_ai
```

## Modeling Design

Main classification target:

```text
next-week return down / flat / up using a fixed 2% band
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
uv run pytest
```

The tests cover target construction, feature joins, pipeline feature-set selection, walk-forward splits, backtest accounting, and CLI smoke tests.
