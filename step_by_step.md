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
- Main validation scheme: expanding training window
- Robustness validation scheme: rolling 5-year training window, 260 weeks

Main split:

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

Why expanding window is the main specification:

- Weekly CORN ETF data are limited, and the `k=1.0` target creates relatively sparse tradeable up/down events.
- Expanding windows give the model more examples of rare commodity moves.
- Corn returns are strongly tied to weather, crop progress, planting, pollination, harvest, inventories, and seasonal supply/demand mechanisms. These economic mechanisms persist over time even though individual market regimes differ.
- A rolling 5-year window is still useful as a robustness check for regime sensitivity, but it is not the main specification because it discards scarce historical crop-cycle examples.

Rolling 5-year robustness split:

```text
Fold 1:
  train = latest 260 weeks ending before 2023-01-06
  test  = 2023-01-06 through 2023-03-31

Fold 2:
  train = latest 260 weeks ending before 2023-04-07
  test  = 2023-04-07 through 2023-06-30
```

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

## Step 2: Construct Y With Fixed Threshold

Current decision: use `k = 1.0` for the volatility-adjusted three-class threshold.

For each week `t`:

```text
r_{t+1} = log(close_{t+1} / close_t)
vol_t   = rolling 12-week standard deviation of weekly returns
```

Target:

```text
Y_t =  1 if r_{t+1} >  +1.0 * vol_t
Y_t =  0 if -1.0 * vol_t <= r_{t+1} <= +1.0 * vol_t
Y_t = -1 if r_{t+1} <  -1.0 * vol_t
```

Command to reproduce the current threshold run:

```bash
uv run python -m corn_forecast.cli select-threshold \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --validation-scheme expanding \
  --threshold-grid 1.0 \
  --long-threshold 0.45
```

Output:

```text
reports/threshold_selection.json
reports/threshold_selection_predictions.csv
```

Why `k = 1.0`:

- It defines a meaningful move as larger than one trailing weekly volatility.
- It creates a clearer no-trade zone than lower thresholds.
- It is more conservative and closer to an ETF investor's trading problem.
- Robustness checks can still compare `k = 0.25, 0.50, 0.75`.

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

## Step 5: Build Feature Panel

Input:

```text
Y
X_price
X_calendar
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

## Step 6: Define Model Experiments

Current scope: run only price and price + calendar baselines under the same target, split, and trading rule.

```text
A = price_only
B = price_calendar
```

The purpose is to test incremental value:

```text
Does calendar seasonality improve trading signals beyond historical price alone?
```

## Step 7: Train Models With Walk-Forward Validation

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

Robustness protocol:

```text
rolling walk-forward
260-week training window
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

## Step 8: Convert Predictions To Trading Signals

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

## Step 9: Evaluate

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

## Step 10: Final Deliverables

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
Can calendar seasonality improve volatility-adjusted weekly CORN ETF trading signals beyond historical price baselines?
```
