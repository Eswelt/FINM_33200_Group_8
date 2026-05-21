# CORN ETF Trading Signal Pipeline

This project should be framed as a weekly trading-signal problem for CORN ETF investors, not as raw price prediction.

## Fixed Research Timeline

Use a frozen sample while we develop so everyone compares the same rows.

- Raw price start: `2011-01-01`
- Frozen data end for current experiments: `2026-05-15`
- Weekly timestamp: Friday close, `W-FRI`
- Initial training window: `2011-01-07` through `2022-12-30`
- Out-of-sample test window: `2023-01-06` through `2026-05-15`
- Walk-forward fold size: 13 weeks
- Retrain step: 13 weeks

The default split is:

```text
Fold 1:
  train = all weeks <= 2022-12-30
  test  = 2023-01-06 through 2023-03-31

Fold 2:
  train = all weeks <= 2023-03-31
  test  = 2023-04-07 through 2023-06-30

Continue expanding the training window until 2026-05-15.
```

Do not use random train/test splits.

## Step 1: Build Weekly Price Data

Input:

```text
data/raw/prices_CORN.csv
```

Source:

```bash
uv run python -m corn_forecast.cli fetch-prices --start 2011-01-01 --end 2026-05-15
```

Operation:

- Resample daily OHLCV to Friday weekly data.
- Keep weekly close and weekly volume.
- Compute weekly log return.

Output:

```text
week
close
volume
price_log_return
```

Used by:

- Target construction.
- Price baseline features.
- Strategy backtest realized returns.

## Step 2: Construct Candidate Y Thresholds

Today's task is to decide the volatility-adjusted three-class threshold.

For each week `t`:

```text
r_{t+1} = log(close_{t+1} / close_t)
vol_t   = rolling 12-week standard deviation of weekly returns
```

Candidate target:

```text
Y_t =  1 if r_{t+1} >  +k * vol_t
Y_t =  0 if -k * vol_t <= r_{t+1} <= +k * vol_t
Y_t = -1 if r_{t+1} <  -k * vol_t
```

Threshold grid:

```text
k = 0.25, 0.50, 0.75, 1.00
```

Command:

```bash
uv run python -m corn_forecast.cli select-threshold \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --threshold-grid 0.25,0.5,0.75,1.0
```

Output:

```text
reports/threshold_selection.json
reports/threshold_selection_predictions.csv
```

Decision criteria:

- Event rate should not be too sparse.
- Up/down/flat should all appear in out-of-sample tests.
- Macro F1 and balanced recall should not collapse.
- Trading performance after 5 bps cost should be reasonable.
- Trade frequency should be plausible for a weekly ETF strategy.

Recommended starting point if results are similar:

```text
k = 0.50
```

## Step 3: Build Price Baseline X

Input:

```text
weekly price table
```

Features:

```text
price_lag_return_1w
price_lag_return_2w
price_lag_return_4w
price_lag_return_12w
price_rolling_vol_4w
price_rolling_vol_12w
price_momentum_4w
price_momentum_12w
price_volume_change_4w
```

Output:

```text
X_price
```

Used by:

```text
Experiment A: price_only
```

## Step 4: Build Calendar X

Input:

```text
week
```

Features:

```text
calendar_month
calendar_quarter
calendar_week_of_year
calendar_week_sin
calendar_week_cos
calendar_is_planting_season
calendar_is_pollination_weather_season
calendar_is_harvest_season
calendar_is_winter_storage_season
```

Output:

```text
X_calendar
```

Used by:

```text
Experiment B: price_calendar
```

## Step 5: Build USDA Weekly Text X

Input:

```text
data/raw/usda_releases.csv
```

Sources:

```text
USDA Crop Progress
USDA Weekly Weather and Crop Bulletin
```

Operation:

- Align release dates to the Friday week.
- Only use reports available by week `t`.
- Build keyword counts and TF-IDF text features.
- Later add AI-extracted structured scores.

Output:

```text
X_usda_text:
report_text
report_count
text_kw_drought
text_kw_rain
text_kw_heat
text_kw_planting
text_kw_harvest
text_kw_yield
...
```

Used by:

```text
Experiment C: price_calendar_usda
```

## Step 6: Build Weather X

Input:

```text
ERA5 historical weather
CFSv2 or GEFS reforecast / forecast data
```

Operation:

- Aggregate to Corn Belt weekly level.
- Compute weather anomalies against seasonal norms.
- Add week-1 and week-2 forecast variables when available.

Output:

```text
X_weather:
weather_temp_mean_f
weather_precip_mm
weather_gdd
weather_temp_anomaly_f
weather_precip_anomaly_mm
weather_forecast_temp_week1_f
weather_forecast_precip_week1_mm
weather_forecast_temp_week2_f
weather_forecast_precip_week2_mm
```

Used by:

```text
Experiment D: price_calendar_usda_weather
```

## Step 7: Build Feature Panel

Input:

```text
Y
X_price
X_calendar
X_usda_text
X_weather
```

Command:

```bash
uv run python -m corn_forecast.cli build-features
```

Operation:

- Join all tables by `week`.
- Drop rows with missing target.
- Keep all realized next-week returns for backtesting.
- Verify no feature uses information after week `t`.

Output:

```text
data/processed/feature_panel.parquet
```

Each row represents:

```text
week_t
X_t
Y_t
next_week_return
```

## Step 8: Define Model Experiments

Run all experiments under the same target, split, and trading rule.

```text
A = price_only
B = price_calendar
C = price_calendar_usda
D = price_calendar_usda_weather
E = price_calendar_ai_text_weather
```

The purpose is to test incremental value:

```text
Does USDA / weather / AI text extraction improve trading signals beyond price and seasonality?
```

## Step 9: Train Models With Walk-Forward Validation

Input:

```text
data/processed/feature_panel.parquet
```

Models:

```text
Multinomial Logistic Regression
HistGradientBoostingClassifier
```

Training protocol:

```text
expanding walk-forward
13-week test windows
13-week retrain step
```

Output:

```text
reports/predictions.csv
```

Prediction columns:

```text
week
experiment
model
P(down)
P(flat)
P(up)
predicted_class
true_class
next_week_return
```

## Step 10: Convert Predictions To Trading Signals

Main strategy:

```text
if P(up) >= 0.45:
    position = 1
else:
    position = 0
```

Optional long/short strategy:

```text
if P(up) >= 0.45:
    position = 1
elif P(down) >= 0.45:
    position = -1
else:
    position = 0
```

Transaction cost:

```text
5 bps per one-way position change
```

Output:

```text
strategy_return
cumulative_strategy_return
turnover
transaction_cost
```

## Step 11: Evaluate

Classification metrics:

```text
accuracy
balanced accuracy
macro F1
confusion matrix
event rate
```

Trading metrics:

```text
total return
annualized return
Sharpe
max drawdown
trade frequency
hit rate on traded weeks
average return on traded weeks
turnover
transaction-cost-adjusted return
```

Output:

```text
reports/metrics.json
reports/model_report.md
reports/figures/
```

## Step 12: Final Deliverables

Final project outputs:

```text
data/processed/feature_panel.parquet
reports/predictions.csv
reports/metrics.json
reports/model_report.md
reports/figures/cumulative_returns.png
reports/figures/predicted_probabilities.png
reports/figures/confusion_matrix.png
reports/figures/feature_importance.png
```

Final research question:

```text
Can AI-assisted agricultural text and weather information improve volatility-adjusted weekly CORN ETF trading signals beyond historical price and calendar baselines?
```
