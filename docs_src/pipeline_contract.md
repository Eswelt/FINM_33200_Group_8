# Modular Prediction Pipeline Contract

This repository now has three prediction pipelines that share the same weekly feature panel.

## Shared Input Contract

All teammate-produced feature files should be weekly and point-in-time:

```text
week = Friday timestamp for the prediction week
features = information known by that week
```

Place optional teammate outputs here:

```text
data/interim/weather_weekly.parquet
data/interim/text_weekly.parquet
data/interim/ai_weekly.parquet
data/interim/gdelt_weekly_scores.parquet
```

CSV fallback with the same stem is also accepted, for example:

```text
data/interim/weather_weekly.csv
```

Required column:

```text
week
```

Column naming contract:

```text
weather_*   weather features, anomalies, forecasts, reforecast summaries
text_*      numeric text features such as keyword counts or sentiment scores
ai_*        LLM-extracted structured scores
gdelt_*     GDELT-derived news scores
report_text optional free-text report field for TF-IDF
```

Examples:

```text
weather_temp_anomaly_f
weather_precip_anomaly_mm
weather_forecast_temp_week1_f
text_drought_count
text_yield_risk_score
ai_crop_stress_score
ai_bullish_score
report_text
```

After teammates drop these files into `data/interim/`, build the shared panel:

```bash
uv run --extra dev doit build_features
```

Output:

```text
data/processed/feature_panel.parquet
```

## Feature Sets

Both pipelines use the same `--feature-sets` names:

```text
price_only
price_calendar
price_weather
price_weather_text
price_calendar_weather
price_calendar_text
price_calendar_weather_text
price_ai
price_gdelt
price_ai_gdelt
price_calendar_ai
price_calendar_gdelt
price_calendar_ai_gdelt
price_calendar_weather_ai
price_calendar_weather_text_ai
```

Current baseline:

```bash
--feature-sets price_only,price_calendar
```

When weather and text are ready:

```bash
--feature-sets price_only,price_calendar,price_calendar_weather,price_calendar_weather_text_ai
```

## Pipeline 1: Fixed 2% Classification

Goal:

```text
Predict whether next-week CORN ETF arithmetic return is down, flat, or up.
```

Target:

```text
Y =  1 if next_week_return >= +2%
Y =  0 if -2% < next_week_return < +2%
Y = -1 if next_week_return <= -2%
```

The modeling panel stores `target_log_return_next`, so the implementation converts the arithmetic band to log-return bounds before assigning labels.

Command:

```bash
uv run --extra dev doit classify_move
```

Output:

```text
docs_src/reports/price_target_tests.json
docs_src/reports/price_target_predictions.csv
```

Primary metrics:

```text
accuracy
balanced_accuracy_present_classes
macro_f1
confusion_matrix
n_down / n_flat / n_up
```

## Pipeline 2: Expected Return

Goal:

```text
Predict next-week CORN ETF log return directly.
```

Target:

```text
Y = next_week_log_return
```

Trading rule:

```text
long if predicted_return > transaction_cost_bps + buffer_bps
flat otherwise
```

Default:

```text
transaction_cost_bps = 5
buffer_bps = 25
trade_threshold = 30 bps = 0.30%
```

Command:

```bash
uv run --extra dev doit return_strategy
```

Output:

```text
docs_src/reports/expected_return_metrics.json
docs_src/reports/expected_return_predictions.csv
```

Primary forecast diagnostics:

```text
MAE
RMSE
R2
direction_accuracy
```

Trading diagnostics:

```text
strategy_total_return
strategy_sharpe
max_drawdown
trade_frequency
hit_rate_traded_weeks
average_return_traded_weeks
```

## Validation

Main validation:

```bash
--validation-scheme expanding
```

Robustness:

```bash
uv run --extra dev doit select_threshold_rolling
```

All pipelines use walk-forward validation with 13-week test windows by default.

## USDA WWCB Core Text Parser

USDA Weekly Weather and Crop Bulletin PDFs can be reduced to core CORN-relevant text before LLM feature extraction:

First, batch download the raw PDFs from USDA ESMIS:

```bash
PYTHONPATH=src uv run python -m scripts.download_wwcb \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --output-dir data/external/wwcb_pdfs \
  --manifest data/interim/wwcb_manifest.csv
```

For a small test run:

```bash
PYTHONPATH=src uv run python -m scripts.download_wwcb --start 2026-05-01 --end 2026-05-31 --limit 2 --dry-run
```

Then parse downloaded PDFs:

```bash
PYTHONPATH=src uv run python -m scripts.parse_wwcb path/to/wwcb.pdf --output data/interim/wwcb_core_text.parquet
```

The input can also be a folder of PDFs:

```bash
PYTHONPATH=src uv run python -m scripts.parse_wwcb data/external/wwcb_pdfs --output data/interim/wwcb_core_text.parquet
```

Output columns:

```text
source_file
report_date
week_ending
week
weather_highlights
national_ag_summary
corn_section
corn_table_text
report_text
```

`national_ag_summary` is retained as a debug column. The default `report_text` used for LLM feature extraction excludes the full national summary and only includes:

```text
weather_highlights
corn_section
corn_table_text
```

The intended next step is to pass `report_text` or the section columns to an LLM and produce:

```text
week
ai_moisture_stress
ai_heat_stress
ai_excess_rain_risk
ai_planting_delay_risk
ai_harvest_delay_risk
ai_yield_risk
ai_crop_condition_trend
```

Save those features to:

```text
data/interim/ai_weekly.parquet
```

## GLM AI Feature Extraction

The USDA text pipeline uses GLM as a structured feature extractor, not as the price forecaster. GLM reads each parsed `report_text` and returns seven numeric fields:

```text
ai_moisture_stress        0 none to 3 severe
ai_heat_stress            0 none to 3 severe
ai_excess_rain_risk       0 none to 3 severe
ai_planting_delay_risk    0 none to 3 severe
ai_harvest_delay_risk     0 none to 3 severe
ai_yield_risk             0 none to 3 severe
ai_crop_condition_trend  -2 clearly worse to 2 clearly better
```

Small local mock run, no API key required:

```bash
PYTHONPATH=src uv run python -m scripts.extract_wwcb_ai_features \
  --input data/interim/wwcb_core_text.parquet \
  --output data/interim/ai_weekly.parquet \
  --raw-output data/interim/ai_wwcb_raw.parquet \
  --limit 3 \
  --mock
```

GLM run:

```bash
export BIGMODEL_API_KEY=your_key_here

PYTHONPATH=src uv run python -m scripts.extract_wwcb_ai_features \
  --input data/interim/wwcb_core_text.parquet \
  --output data/interim/ai_weekly.parquet \
  --raw-output data/interim/ai_wwcb_raw.parquet \
  --model glm-4.5-flash
```

`ai_weekly.parquet` is the file consumed by the forecasting pipelines. `ai_wwcb_raw.parquet` keeps report-level metadata and token usage for auditing.
