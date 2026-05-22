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

## Step 2: Construct Y As Fixed 2% Three-Class Return

Current decision: the main target is a fixed-threshold three-class next-week return label.

For each week `t`:

```text
r_{t+1} = log(close_{t+1} / close_t)
```

Target:

```text
Y_t =  1 if r_{t+1} >= +2%
Y_t =  0 if -2% < r_{t+1} < +2%
Y_t = -1 if r_{t+1} <= -2%
```

Main command:

```bash
uv run python -m corn_forecast.cli test-price-targets \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --fixed-return-threshold 0.02
```

Output:

```text
reports/price_target_tests.json
reports/price_target_predictions.csv
```

Why `2%`:

- It is large enough to be economically meaningful for a weekly ETF trade.
- It avoids noisy labels from tiny weekly moves.
- It is not as sparse as a 5% weekly threshold.
- In the 2023-2026 OOS window, it gives 32 down weeks, 119 flat weeks, and 24 up weeks.
- The expected-return strategy remains available as an auxiliary experiment, not the current main target.

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
Ridge regression
HistGradientBoostingRegressor
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
predicted_return
actual_next_week_return
next_week_return
```

## Step 8: Convert Predictions To Trading Signals

Main strategy:

```text
if predicted_return > transaction_cost + buffer:
    position = 1
else:
    position = 0
```

Optional long/short strategy:

```text
if predicted_return > transaction_cost + buffer:
    position = 1
elif predicted_return < -(transaction_cost + buffer):
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
MAE
RMSE
R2
direction accuracy
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
