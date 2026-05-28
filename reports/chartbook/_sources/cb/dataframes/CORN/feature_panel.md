# Dataframe: `CORN:feature_panel` - Weekly Feature Panel

# CORN ETF Trading Signal Workflow

This document is the project-level workflow guide used by ChartBook. It consolidates the research design, command surface, data contracts, modeling tasks, and report-generation path into one reproducible sequence.

## Objective

The project frames CORN ETF forecasting as a weekly trading-signal problem. The main question is:

```text
Can calendar seasonality improve weekly CORN ETF trading signals beyond historical price baselines?
```

The main target is a fixed-threshold three-class next-week return label:

```text
Y =  1 if next_week_return >= +2%
Y =  0 if -2% < next_week_return < +2%
Y = -1 if next_week_return <= -2%
```

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

Run the main research experiments and regenerate the notebook/HTML report:

```bash
uv run --extra dev doit research
```

Refresh external data sources when network access is intended:

```bash
uv run --extra dev doit refresh_data
```

Build the ChartBook site:

```bash
uv run --extra dev --extra docs doit docs
```

Open the generated HTML files on macOS:

```bash
open reports/chartbook/index.html
open reports/html/corn_forecast_workflow.html
```

Run the full local workflow:

```bash
uv run --extra dev --extra docs doit all
```

Run tests:

```bash
uv run --extra dev doit tests
```

`chartbook` requires Python 3.10 or newer. The forecasting package itself remains compatible with the existing project runtime, but the ChartBook documentation extra should be run in a Python 3.10+ environment.

The default `baseline`, `research`, and `docs` tasks use local cached data. The `refresh_data` task is intentionally separate so report generation does not unexpectedly call external services.

## Task Map

| pydoit task | Underlying command | Main outputs |
| --- | --- | --- |
| `fetch_prices` | `corn_forecast.cli fetch-prices` | `data/raw/prices_CORN.csv` |
| `fetch_usda` | `corn_forecast.cli fetch-usda` | `data/raw/usda_releases.csv` |
| `fetch_weather` | `corn_forecast.cli fetch-weather` | `data/interim/weather_weekly.parquet` |
| `refresh_data` | `fetch_prices`, `fetch_usda`, `fetch_weather` | Explicit external data refresh |
| `build_features` | `corn_forecast.cli build-features` | `data/processed/feature_panel.parquet` |
| `train_evaluate` | `corn_forecast.cli train-evaluate` | `reports/metrics.json`, `reports/predictions.csv` |
| `model_report` | `corn_forecast.cli make-report` | `reports/model_report.md`, `reports/figures/*.png` |
| `classify_move` | `corn_forecast.cli classify-move` | `reports/price_target_tests.json`, `reports/price_target_predictions.csv` |
| `return_strategy` | `corn_forecast.cli return-strategy` | `reports/expected_return_metrics.json`, `reports/expected_return_predictions.csv` |
| `select_threshold` | `corn_forecast.cli select-threshold` | `reports/threshold_selection.json`, `reports/threshold_selection_predictions.csv` |
| `notebook` | `scripts/build_project_notebook.py` | `reports/notebooks/corn_forecast_workflow.ipynb`, `reports/html/corn_forecast_workflow.html` |
| `chartbook_build` | `chartbook build` plus local figure asset sync | `reports/chartbook/index.html` |

Optional WWCB tasks are also exposed:

```bash
uv run --extra dev doit wwcb_download
uv run --extra dev doit wwcb_parse
uv run --extra dev doit wwcb_ai_features
uv run --extra dev doit wwcb_ai_features_mock
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
docs_src/final_report.md
docs_src/figures/final_*.png
reports/figures/final_*.png
reports/notebooks/corn_forecast_workflow.ipynb
reports/html/corn_forecast_workflow.html
reports/chartbook/index.html
```

Open the HTML outputs:

```bash
open reports/chartbook/index.html
open reports/html/corn_forecast_workflow.html
```

The notebook and standalone HTML summarize current local outputs, including metric tables, prediction file shapes, and generated final-report figures. ChartBook uses `chartbook.toml` to include this notebook and the workflow notes in a generated documentation site.

For the most compact submission-ready summary, open `reports/chartbook/cb/final_report.html` or `reports/html/corn_forecast_workflow.html`.

## Operational Notes

- Generated data and reports are intentionally ignored by git.
- Use `--demo` CLI options for deterministic offline smoke runs.
- Real price downloads require Yahoo Finance access through `yfinance`.
- Real USDA and WWCB downloads require network access.
- Real AI extraction requires a GLM API key in the environment or `.env.local`.
- Do not compare model variants across different split dates or data-end dates.



## DataFrame Glimpse

```
Rows: 802
Columns: 33
$ close                                           <f64> 18.530000686645508
$ volume                                          <i64> 2491300
$ week                                   <datetime[μs]> 2026-05-15 00:00:00
$ price_log_close                                 <f64> 2.9193910773531506
$ price_log_return                                <f64> -0.004308026097975315
$ price_lag_return_1w                             <f64> -0.014933545751462773
$ price_lag_return_2w                             <f64> 0.03337225375719077
$ price_lag_return_4w                             <f64> 0.011204641516453062
$ price_lag_return_12w                            <f64> -0.001701093628666328
$ price_rolling_vol_4w                            <f64> 0.021715508151120916
$ price_rolling_vol_12w                           <f64> 0.019799453650763667
$ price_momentum_4w                               <f64> 0.031800919915272896
$ price_momentum_12w                              <f64> 0.05035640921552709
$ price_volume_change_4w                          <f64> -0.4776809031490355
$ target_log_return_next                          <f64> null
$ target_up_next                                  <f64> null
$ calendar_month                                  <i32> 5
$ calendar_quarter                                <i32> 2
$ calendar_week_of_year                           <i64> 20
$ calendar_week_sin                               <f64> 0.6631226582407952
$ calendar_week_cos                               <f64> -0.7485107481711012
$ calendar_is_planting_season                     <i64> 1
$ calendar_is_pollination_weather_season          <i64> 0
$ calendar_is_harvest_season                      <i64> 0
$ calendar_is_winter_storage_season               <i64> 0
$ report_text                                     <str> ''
$ ai_moisture_stress                              <f64> 0.0
$ ai_heat_stress                                  <f64> 0.0
$ ai_excess_rain_risk                             <f64> 0.0
$ ai_planting_delay_risk                          <f64> 1.0
$ ai_harvest_delay_risk                           <f64> 0.0
$ ai_yield_risk                                   <f64> 0.0
$ ai_crop_condition_trend                         <f64> 0.0


```

## Dataframe Manifest

| Dataframe Name                 | Weekly Feature Panel                                                   |
|--------------------------------|--------------------------------------------------------------------------------------|
| Dataframe ID                   | [feature_panel](../dataframes/CORN/feature_panel.md)                                       |
| Data Sources                   | Yahoo Finance, USDA ESMIS, Optional teammate feature tables                                        |
| Data Providers                 | yfinance, USDA, FINM 33200 Group 8                                      |
| Links to Providers             |                              |
| Topic Tags                     | Corn, Etf, Trading Signal, Weekly Forecast                                          |
| Type of Data Access            |                                   |
| How is data pulled?            | Built by corn_forecast.cli build-features through pydoit.                                                    |
| Data available up to (min)     | 2026-05-08 00:00:00                                                             |
| Data available up to (max)     | 2026-05-15 00:00:00                                                             |
| Dataframe Path                 | /private/tmp/FINM_33200_Group_8_three_inputs/data/processed/feature_panel.parquet                                                   |


**Linked Charts:**

- None


## Pipeline Manifest

| Pipeline Name                   | CORN ETF Trading Signal Pipeline                       |
|---------------------------------|--------------------------------------------------------|
| Pipeline ID                     | [CORN](../../../index.md)              |
| Lead Pipeline Developer         | FINM 33200 Group 8             |
| Contributors                    | FINM 33200 Group 8           |
| Git Repo URL                    | local                        |
| Pipeline Web Page               | <a href="file:///private/tmp/FINM_33200_Group_8_three_inputs/docs/index.html">Pipeline Web Page      |
| Date of Last Code Update        | 2026-05-27 22:01:14           |
| OS Compatibility                |  |
| Linked Dataframes               |  [CORN:feature_panel](../../dataframes/CORN/feature_panel.md)<br>  [CORN:price_target_predictions](../../dataframes/CORN/price_target_predictions.md)<br>  [CORN:expected_return_predictions](../../dataframes/CORN/expected_return_predictions.md)<br>  [CORN:volatility_predictions](../../dataframes/CORN/volatility_predictions.md)<br>  [CORN:horizon_robustness_metrics](../../dataframes/CORN/horizon_robustness_metrics.md)<br>  [CORN:horizon_robustness_predictions](../../dataframes/CORN/horizon_robustness_predictions.md)<br>  [CORN:gdelt_weekly_scores](../../dataframes/CORN/gdelt_weekly_scores.md)<br>  |


