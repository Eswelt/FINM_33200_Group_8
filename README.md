# FINM 33200 Group 8: CORN ETF Forecasting Project

This repository studies whether information beyond recent prices can improve trading signals for `CORN`, the Teucrium Corn ETF. The project combines three information sources:

- historical `CORN` ETF price behavior;
- text and news signals from USDA-style agricultural reports and GDELT corn-market headlines;
- weather forecast and observed-weather signals from CFSv2, ERA5, and GPCP.

The project has two main empirical tracks. The weekly text/news pipeline asks whether price, calendar, USDA/GLM, and GDELT features improve weekly `CORN` ETF prediction. The daily weather pipeline asks whether short-lead CFSv2 weather forecasts add incremental value beyond a price/calendar baseline.

The weekly classification task uses a fixed-threshold three-class target:

```text
Y =  1 if next_week_return >= +2%
Y =  0 if -2% < next_week_return < +2%
Y = -1 if next_week_return <= -2%
```

The weekly experiments compare:

- `price_only`: historical price features
- `price_ai`: historical price features plus USDA/GLM scores
- `price_gdelt`: historical price features plus GDELT news scores
- `price_calendar`: historical price features plus agricultural seasonality
- combined calendar, USDA/GLM, and GDELT feature sets

The weather experiment compares lead-specific daily regression models for `+7 days`, `+14 days`, `+21 days`, `+28 days`, and `+30 days` CFSv2 forecasts. The strongest weather results come from projected changes in Corn Belt heat and dryness risk, especially at short forecast leads.

## Project Components

| Component | Main location | Purpose |
| --- | --- | --- |
| Weekly text/news pipeline | `src/corn_forecast/`, `scripts/`, `data/interim/` | Build weekly price, calendar, USDA/GLM, and GDELT feature panels. |
| Daily weather pipeline | `weather_corn_etf/` | Test CFSv2 weather forecast signals for daily `CORN` ETF decisions. |
| Weather outputs | `weather_corn_etf/corn_etf_daily_decision_leadbylead_expanding_yearly/` | Saved metrics, predictions, feature panels, and plots from the weather run. |
| ChartBook report | `reports/chartbook/` and `docs_src/` | Presentation-style HTML summary of the project, results, and limitations. |

## Quick Start

```bash
uv sync --python 3.12 --extra dev --extra docs
uv run --extra dev doit baseline
```

This writes the baseline weekly classification outputs:

- `reports/price_target_tests.json`
- `reports/price_target_predictions.csv`

Most generated data and report outputs are ignored by git. Selected frozen project outputs are tracked so the main results can be inspected without rerunning every data download.

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
open reports/chartbook/index.html
open reports/html/corn_forecast_workflow.html
```

Run the daily weather experiment with repository-local processed weather data:

```bash
python weather_corn_etf/test_corn_etf_cfsv2_daily_decision_leadbylead_expanding_yearly.py \
  --cfsv2-root weather_corn_etf/weather_data/validtime_yearly \
  --era5-path weather_corn_etf/weather_data/era5_daily_surface_stats_2011_2025_n49_w104_s37_e80.nc \
  --gpcp-path weather_corn_etf/weather_data/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.nc \
  --price-csv weather_corn_etf/corn_etf_prices.csv \
  --out-dir weather_corn_etf/corn_etf_daily_decision_leadbylead_expanding_yearly/signal_buffer_0p0pct \
  --signal-buffer 0.0 \
  --make-plots \
  --overwrite
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

The default `baseline`, `research`, and `docs` tasks use the cached frozen data already under `data/`. Run `refresh_data` only when you intentionally want to refresh external sources. The weather experiment is run directly from `weather_corn_etf/` because it uses processed NetCDF weather inputs and saved daily-decision outputs.

## Underlying CLI Commands

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

Run the auxiliary volatility pipeline:

```bash
uv run python -m corn_forecast.cli volatility \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --feature-sets price_only,price_calendar,price_calendar_ai
```

The volatility pipeline predicts `abs(next_week_log_return)` and reports both regression diagnostics and a high-volatility classification check based on each training window's 70th percentile absolute return.

Run the weather forecast return-regression pipeline:

```bash
python weather_corn_etf/test_corn_etf_cfsv2_daily_decision_leadbylead_expanding_yearly.py --help
```

The main saved no-buffer run can be reproduced with the repository-relative command in the Quick Start section. It uses `+7 days`, `+14 days`, `+21 days`, `+28 days`, and `+30 days` CFSv2 00Z forecast leads as separate lead-by-lead experiments.

## Project Documents

- `step_by_step.md`: research design, target definition, time split, and validation logic
- `pipeline_contract.md`: feature-table contract and modular pipeline interface
- `docs_src/project_readme_workflow.md`: ChartBook project overview page
- `docs_src/final_figure_analysis.md`: weekly text/news, calendar, and price result page
- `docs_src/weather_corn_etf_daily_decision_report.md`: daily weather forecast result page
- `docs_src/limitations_discussion_future_work.md`: project-level limitations and future work
- `weather_corn_etf/README.md`: detailed weather experiment methodology, data provenance, and commands
- `weather_corn_etf/corn_etf_daily_decision_leadbylead_expanding_yearly/README.md`: file-by-file description of saved weather results
- `chartbook.toml`: ChartBook pipeline metadata, dataframes, notes, and notebook registry
- `dodo.py`: pydoit task graph for all routine commands
- `run_classification_baseline.py`: one-command baseline runner

## Data Interface

Price data are pulled from Yahoo Finance through `yfinance`.

Weekly text/news feature tables are stored under `data/interim/`:

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
gdelt_*     GDELT news score features after feature-panel merge
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

Weather inputs are stored under `weather_corn_etf/weather_data/`:

```text
weather_corn_etf/weather_data/validtime_yearly/cfsv2_daily00z_validtime_2011.nc
...
weather_corn_etf/weather_data/validtime_yearly/cfsv2_daily00z_validtime_2025.nc

weather_corn_etf/weather_data/era5_daily_surface_stats_2011_2025_n49_w104_s37_e80.nc

weather_corn_etf/weather_data/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.nc
weather_corn_etf/weather_data/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.csv
```

The weather run also uses:

```text
weather_corn_etf/corn_etf_prices.csv
```

The CFSv2 files are valid-time matched daily 00Z regional statistics. Available summary leads are `+7 days`, `+14 days`, `+21 days`, `+28 days`, `+30 days`, `+60 days`, `+90 days`, `+120 days`, `+150 days`, `+180 days`, `+210 days`, `+240 days`, and `+270 days`. The return-regression experiment uses the short-lead subset: `+7 days`, `+14 days`, `+21 days`, `+28 days`, and `+30 days`.

## Modeling Design

### Weekly Text/News Models

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
- Volatility: MAE, RMSE, R2, Spearman rank correlation, high-volatility balanced accuracy

### Daily Weather Models

The weather target is the future 5-trading-day `CORN` ETF return:

```text
target_return_t = CORN_close_{t+5 trading days} / CORN_close_t - 1
```

For each daily decision date, each CFSv2 lead is modeled separately. For example, the `+7 days` model uses only the CFSv2 forecast valid 7 days after the decision date, while the `+14 days` model uses only the CFSv2 forecast valid 14 days after the decision date.

The three lead-by-lead Ridge regression specifications are:

```text
price_calendar:
target_return ~ price lags + volatility + momentum + calendar/season controls

forecast_anom:
target_return ~ price_calendar
              + heat_forecast_z + dryness_forecast_z + heat_x_dryness

forecast_anom_projected_change:
target_return ~ forecast_anom
              + heat_projected_change + dryness_projected_change
              + projected_heat_x_dryness
```

Weather feature construction:

```text
forecast_anom_{t,h} = CFSv2_forecast_{t,h} - CFSv2_climatology_{h, day-of-year}
heat_forecast_z = z-scored CFSv2 temperature anomaly
dryness_forecast_z = -1 * z-scored CFSv2 precipitation anomaly
heat_projected_change = heat_forecast_z - init_obs_heat_z
dryness_projected_change = dryness_forecast_z - init_obs_dryness_z
```

The default CFSv2 climatology is expanding and lead-specific, with a 10-day day-of-year window. Initialization observed anomalies come from ERA5/GPCP trailing 7-day averages shifted by one day to avoid look-ahead.

Weather validation:

- Predict 2022 with training years 2011-2021
- Predict 2023 with training years 2011-2022
- Predict 2024 with training years 2011-2023
- Predict 2025 with training years 2011-2024

The main stored weather comparison uses a no-buffer long/short rule:

```text
long  if predicted_return > 0.0%
short if predicted_return < 0.0%
```

The plotted strategy is daily rebalanced:

```text
strategy_return_t = position_t * next_1d_return_t - transaction_cost
```

## Main Results Summary

The fixed +/-2% weekly classification problem is difficult because most weeks fall into the flat class. The weekly strategy results are more informative than raw classification accuracy: combined price, calendar, AI/USDA, and GDELT feature sets perform better than price-only baselines in the expected-return strategy comparison.

The daily weather results are strongest at short CFSv2 leads. The `forecast_anom_projected_change` model generally improves over the forecast-anomaly-only model because it asks whether forecasted heat and dryness risk is intensifying relative to the observed initialization state. In the no-buffer weather run, the strongest headline result is the `+14 days` projected-change model, with `+7 days` and `+30 days` also showing meaningful improvements over the price/calendar baseline.

The weather trading metrics are stronger than the regression R2 diagnostics, so these results should be interpreted as exploratory trading-signal evidence rather than as a high-precision return forecast.

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
