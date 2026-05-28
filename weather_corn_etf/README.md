# Weather-Based CORN ETF Return Test

This folder contains the CFSv2 weather experiment for predicting CORN ETF returns.

The main script is:

```bash
python test_corn_etf_cfsv2_daily_decision_leadbylead_expanding_yearly.py --help
```

The stored outputs from one run are in:

```text
corn_etf_daily_decision_leadbylead_expanding_yearly/
```

## Goal

The experiment tests whether short-horizon weather forecasts add predictive information for CORN ETF returns beyond price/calendar controls.

For each daily decision date, the target is the future 5-trading-day CORN ETF return:

```text
target_return_t = CORN_close_{t+5 trading days} / CORN_close_t - 1
```

The trading backtest uses a daily-rebalanced return, but the regression signal is still the predicted 5-trading-day return.

## Input Data

The script is designed to run on GLADE/Derecho and defaults to these paths:

```text
CFSv2 forecasts:
/glade/work/jiachengye/33200/cfsv2/validtime_yearly/

ERA5 observed surface weather:
/glade/work/jiachengye/33200/era5_daily_surface_stats_2011_2025_n49_w104_s37_e80.nc

GPCP observed precipitation:
/glade/work/jiachengye/33200/gpcp/stats/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.nc
```

If `--price-csv` is not supplied, CORN ETF prices are downloaded from Yahoo Finance through `yfinance`.

The default CFSv2 lead days are:

```text
+7, +14, +21, +28, +30
```

Each lead is modeled separately.

## Weather Feature Construction

CFSv2 forecast anomalies are computed relative to lead-specific CFSv2 model climatology:

```text
forecast_anom_{t,h} = CFSv2_forecast_{t,h} - CFSv2_climatology_{h, day-of-year}
```

The default climatology mode is `expanding`, so each date only uses earlier dates when estimating climatology. The day-of-year climatology uses a 10-day window.

The script also builds initialization observed anomalies from ERA5/GPCP using a trailing 7-day average shifted by one day to avoid look-ahead.

The main weather variables are:

```text
heat_forecast_z = z-scored CFSv2 temperature anomaly
dryness_forecast_z = -1 * z-scored CFSv2 precipitation anomaly
heat_x_dryness = heat_forecast_z * dryness_forecast_z
```

Projected-change variables compare the forecast anomaly with the initialization observed anomaly:

```text
heat_projected_change = heat_forecast_z - init_obs_heat_z
dryness_projected_change = dryness_forecast_z - init_obs_dryness_z
projected_heat_x_dryness = heat_projected_change * dryness_projected_change
```

Higher heat and higher dryness are both coded as higher supply-risk signals.

## Models

For each lead day, the script fits three Ridge regression specifications.

`price_calendar`:

```text
target_return ~ price lags + volatility + momentum + calendar/season controls
```

`forecast_anom`:

```text
target_return ~ price_calendar + heat_forecast_z + dryness_forecast_z + heat_x_dryness
```

`forecast_anom_projected_change`:

```text
target_return ~ price_calendar
              + heat_forecast_z + dryness_forecast_z + heat_x_dryness
              + heat_projected_change + dryness_projected_change + projected_heat_x_dryness
```

All regressions use:

```text
SimpleImputer(strategy="median")
StandardScaler()
Ridge regression
```

The Ridge alpha is selected by `TimeSeriesSplit` cross-validation.

## Expanding-Yearly Evaluation

The default evaluation uses an expanding yearly out-of-sample design:

```text
Predict 2022 with training years 2011-2021
Predict 2023 with training years 2011-2022
Predict 2024 with training years 2011-2023
Predict 2025 with training years 2011-2024
```

For each test year, the Ridge alpha is selected inside the training window, then the model is refit on the full expanding training set and evaluated on that test year.

## Trading Rule

The predicted 5-trading-day return is converted into a daily position:

```text
if predicted_return > signal_buffer:  position = +1
if predicted_return < -signal_buffer: position = -1
otherwise:                            position = 0
```

The default stored run used:

```text
signal_buffer = 0.003
transaction_cost_bps = 5.0
```

The plotted equity curves use daily-rebalanced one-day realized returns:

```text
strategy_return_t = position_t * next_1d_return_t - transaction_cost
```

The `signal_5td_proxy_*` metrics compound overlapping 5-trading-day signal returns and should be read as signal diagnostics, not as directly investable portfolio returns.

## Main Command

Example Derecho command:

```bash
python test_corn_etf_cfsv2_daily_decision_leadbylead_expanding_yearly.py \
  --cfsv2-root /glade/work/jiachengye/33200/cfsv2/validtime_yearly \
  --era5-path /glade/work/jiachengye/33200/era5_daily_surface_stats_2011_2025_n49_w104_s37_e80.nc \
  --gpcp-path /glade/work/jiachengye/33200/gpcp/stats/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.nc \
  --signal-buffer 0.003 \
  --make-plots \
  --overwrite
```

## Outputs

The script writes:

```text
cfsv2_corn_etf_daily_decision_feature_panel.csv
cfsv2_corn_etf_daily_decision_regression_predictions.csv
cfsv2_corn_etf_daily_decision_regression_metrics.csv
cfsv2_corn_etf_daily_decision_metadata.json
plots/
```

See `corn_etf_daily_decision_leadbylead_expanding_yearly/README.md` for a file-by-file description of the saved results.
