# CORN ETF Daily-Decision Lead-by-Lead Results

This directory stores one completed run of the weather-based CORN ETF experiment from:

```text
../test_corn_etf_cfsv2_daily_decision_leadbylead_expanding_yearly.py
```

The run uses CFSv2 weather forecasts, ERA5/GPCP observed weather, and CORN ETF prices to test whether lead-specific weather forecast factors improve daily return prediction and trading performance.

## Run Configuration

The exact run metadata is saved in:

```text
cfsv2_corn_etf_daily_decision_metadata.json
```

Key settings from the saved metadata:

```text
CFSv2 lead days: +7, +14, +21, +28, +30
Forecast years loaded: 2011-2025
Out-of-sample years: 2022-2025
Training design: expanding yearly
Regression target: future 5-trading-day CORN ETF return
Trading return: daily-rebalanced one-day realized return
Climatology mode: expanding
Climatology window: 10 calendar days
Initialization observed anomaly window: trailing 7 days, shifted by 1 day
Signal buffer: 0.003
Transaction cost: 5 bps per turnover unit
```

## Main CSV Files

### `cfsv2_corn_etf_daily_decision_feature_panel.csv`

Daily modeling panel before regression prediction.

Important column groups:

```text
decision_date, close
```

CORN ETF price and daily decision date.

```text
target_next_1d_return
target_return
target_class
```

Return targets. `target_return` is the future 5-trading-day return. `target_next_1d_return` is used for daily-rebalanced trading metrics.

```text
price_return_lag_*
price_vol_*
price_momentum_*
month, quarter, weekofyear_*, dayofweek_*
is_planting_season, is_pollination_season, is_harvest_season, is_winter_storage_season
```

Price/calendar baseline features.

```text
weather_cfsv2_t2m_*_l{lead}
weather_cfsv2_spfh_*_l{lead}
weather_cfsv2_precip_*_l{lead}
```

Raw CFSv2 forecast values, CFSv2 model-climatology anomalies, z-scores, and grid-count diagnostics by lead day.

```text
weather_heat_forecast_z_l{lead}
weather_dryness_forecast_z_l{lead}
weather_heat_x_dryness_l{lead}
```

Forecast anomaly factors used by the weather model. Dryness is defined as negative precipitation z-score.

```text
init_obs_t2m_z
init_obs_precip_z
init_obs_heat_z
init_obs_dryness_z
```

Initialization observed weather anomaly features from ERA5/GPCP.

```text
weather_heat_projected_change_l{lead}
weather_dryness_projected_change_l{lead}
weather_projected_heat_x_dryness_l{lead}
```

Projected-change weather factors, defined as forecast anomaly minus initialization observed anomaly.

### `cfsv2_corn_etf_daily_decision_regression_predictions.csv`

Out-of-sample prediction rows for each lead/model combination.

Important columns:

```text
decision_date
test_year
lead_day
model
feature_set
predicted_return
target_return
target_next_1d_return
position
turnover
strategy_return_daily_rebalanced
strategy_return_5td_signal_proxy
```

This file is useful for reconstructing equity curves, comparing predicted and realized returns, or checking positions through time.

### `cfsv2_corn_etf_daily_decision_regression_metrics.csv`

Summary table by lead day and model.

Important columns:

```text
oos_r2_vs_train_mean
rmse_5td_target
mae_5td_target
corr_pred_actual_5td
direction_accuracy_5td
daily_rebalanced_total_return
daily_rebalanced_annual_return
daily_rebalanced_annual_vol
daily_rebalanced_sharpe
daily_rebalanced_max_drawdown
daily_rebalanced_cash_share
```

`oos_r2_vs_train_mean` compares the regression forecast against the expanding training-window mean return. Positive values mean the model beats that train-mean benchmark in squared error.

### `cfsv2_corn_etf_daily_decision_metadata.json`

Machine-readable record of input paths, lead days, training/test years, transaction costs, signal buffer, climatology settings, and output paths from the original Derecho run.

## Threshold Summary Files

These files summarize additional signal-buffer checks generated after the main run.

### `signal_buffer_0p0_0p5pct_summary.csv`

Performance table for signal buffers from 0.0% to 0.5%.

The buffer changes the trading rule:

```text
long  if predicted_return > buffer
short if predicted_return < -buffer
cash  otherwise
```

The regression predictions and OOS R2 are unchanged by the buffer. Strategy return, Sharpe, drawdown, turnover, and cash share change because the position rule changes.

### `signal_buffer_0p1_1p0pct_summary.csv`

Same structure as above, but for buffers from 0.1% to 1.0%.

### `signal_buffer_0p0_0p5pct_daily_strategy_returns_long.csv`

Long-format daily strategy returns for the 0.0% to 0.5% buffer comparison.

### `signal_buffer_0p0_0p5pct_daily_strategy_returns_wide.csv`

Wide-format version of the same daily strategy return series.

### `signal_buffer_0p0_0p5pct_best_by_threshold_daily_returns_wide.csv`

Daily returns for the best lead/model choice selected within each signal-buffer threshold.

### `signal_buffer_0p0_0p5pct_benchmark_metrics.csv`

Reference benchmark performance, including:

```text
price_calendar baseline
CORN buy-and-hold
```

## `plots/`

Top-level plots from the saved run:

```text
lead_07_daily_rebalanced_equity.png
lead_14_daily_rebalanced_equity.png
lead_21_daily_rebalanced_equity.png
lead_28_daily_rebalanced_equity.png
lead_30_daily_rebalanced_equity.png
```

Each lead-specific equity plot compares:

```text
price_calendar
forecast_anom
forecast_anom_projected_change
```

The y-axis is cumulative growth of $1 from the daily-rebalanced trading strategy.

```text
daily_decision_oos_r2_summary.png
```

Bar chart of out-of-sample R2 by lead day and model.

```text
daily_decision_sharpe_summary.png
```

Bar chart of daily-rebalanced Sharpe ratio by lead day and model.

## `signal_buffer_0p0pct/`

This subdirectory keeps the no-buffer version of the same regression outputs:

```text
cfsv2_corn_etf_daily_decision_regression_predictions.csv
cfsv2_corn_etf_daily_decision_regression_metrics.csv
cfsv2_corn_etf_daily_decision_metadata.json
plots/
```

The `plots/` subdirectory contains the same lead-level equity curves plus summary plots for the 0.0% signal-buffer case.

## Interpretation Notes

The weather models are intended to answer whether CFSv2 forecast information improves prediction relative to a price/calendar-only baseline.

The main comparison is:

```text
price_calendar vs forecast_anom vs forecast_anom_projected_change
```

The strongest evidence for useful weather information would be:

```text
higher OOS R2
higher correlation between predicted and actual 5-trading-day returns
higher daily-rebalanced Sharpe
lower max drawdown
reasonable cash share and turnover
```

Trading metrics are exploratory. They do not include all real-world frictions, borrow constraints, ETF liquidity details, or tax effects.
