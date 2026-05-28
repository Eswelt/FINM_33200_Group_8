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

That results directory has its own README with a file-by-file description of the saved CSV, JSON, and plot outputs:

```text
corn_etf_daily_decision_leadbylead_expanding_yearly/README.md
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
If the Yahoo Finance download fails and `corn_etf_prices.csv` exists next to the script, the script falls back to that local CSV.

The repository also includes the processed weather inputs needed to reproduce the saved run:

```text
weather_data/validtime_yearly/cfsv2_daily00z_validtime_2011.nc
...
weather_data/validtime_yearly/cfsv2_daily00z_validtime_2025.nc

weather_data/era5_daily_surface_stats_2011_2025_n49_w104_s37_e80.nc

weather_data/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.nc
weather_data/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.csv
```

## Data Coverage And Provenance

All regional weather statistics use the same Corn Belt bounding box:

```text
north=49, west=-104, south=37, east=-80
```

The CFSv2 forecast data are NOAA CFSv2 operational 9-month forecasts initialized at 00Z. The downloaded source files are 6-hourly forecast products, but the processed yearly files keep a summary set of lead times:

```text
+7, +14, +21, +28, +30, +60, +90, +120, +150, +180, +210, +240, +270 days
```

For a 00Z initialization, these correspond to the following lead hours and valid times:

```text
+7 days   = 168 lead hours  = 00Z valid time 7 days after initialization
+14 days  = 336 lead hours  = 00Z valid time 14 days after initialization
+21 days  = 504 lead hours  = 00Z valid time 21 days after initialization
+28 days  = 672 lead hours  = 00Z valid time 28 days after initialization
+30 days  = 720 lead hours  = 00Z valid time 30 days after initialization
+60 days  = 1440 lead hours
+90 days  = 2160 lead hours
+120 days = 2880 lead hours
+150 days = 3600 lead hours
+180 days = 4320 lead hours
+210 days = 5040 lead hours
+240 days = 5760 lead hours
+270 days = 6480 lead hours
```

The return model uses the short-horizon subset:

```text
+7, +14, +21, +28, +30
```

Each lead is modeled separately. The yearly CFSv2 files are valid-time matched: for a row with valid date `t` and lead `h`, the source initialization date is `t - h`.

ERA5 observed surface weather covers 2011-2025 and is stored here only as a postprocessed regional statistics file because the raw downloaded ERA5 data are too large for the repository. The model reads ERA5 near-surface temperature and specific humidity from:

```text
weather_data/era5_daily_surface_stats_2011_2025_n49_w104_s37_e80.nc
```

GPCP observed precipitation covers 2011-01-01 through 2025-12-31. The repository includes both NetCDF and CSV regional daily precipitation statistics:

```text
weather_data/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.nc
weather_data/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.csv
```

## Data Preparation Scripts

`download_cfsv2_00z_derecho_parallel.py` downloads CFSv2 00Z operational forecast files on Derecho and computes daily-initialization regional forecast statistics for:

```text
t2m, spfh, precip
```

Its default output layout is:

```text
/glade/work/jiachengye/33200/cfsv2/daily00z/YYYY/t2m_YYYYMMDD00.nc
/glade/work/jiachengye/33200/cfsv2/daily00z/YYYY/spfh_YYYYMMDD00.nc
/glade/work/jiachengye/33200/cfsv2/daily00z/YYYY/precip_YYYYMMDD00.nc
```

`test1_era5_load.py` is a legacy/non-parallel version of the CFSv2 daily-initialization processing workflow. Despite the filename, it is not the ERA5 postprocessing script.

`build_cfsv2_validtime_yearly.py` reorganizes those daily-initialization CFSv2 files by valid date and writes:

```text
cfsv2_daily00z_validtime_YYYY.nc
```

`test_gpcp_download.py` downloads GPCP daily precipitation and computes the regional precipitation statistics.

`recompute_gpcp_stats.py` recomputes the same GPCP regional statistics from already downloaded daily GPCP files. This is useful when the daily files already exist on GLADE and only the regional NetCDF/CSV needs to be rebuilt.

The ERA5 regional surface statistics file is an input to this repository. The raw ERA5 download and processing step is not included here because the raw data volume is large.

`download_corn_etf_prices.py` downloads CORN ETF daily prices into the CSV format accepted by the return-regression script.

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

The no-buffer stored run in `corn_etf_daily_decision_leadbylead_expanding_yearly/signal_buffer_0p0pct/` used:

```text
signal_buffer = 0.0
transaction_cost_bps = 5.0
```

The plotted equity curves use daily-rebalanced one-day realized returns:

```text
strategy_return_t = position_t * next_1d_return_t - transaction_cost
```

The `signal_5td_proxy_*` metrics compound overlapping 5-trading-day signal returns and should be read as signal diagnostics, not as directly investable portfolio returns.

## Main Command

Example Derecho command for the no-buffer (`signal_buffer_0p0pct`) result:

```bash
python test_corn_etf_cfsv2_daily_decision_leadbylead_expanding_yearly.py \
  --cfsv2-root /glade/work/jiachengye/33200/cfsv2/validtime_yearly \
  --era5-path /glade/work/jiachengye/33200/era5_daily_surface_stats_2011_2025_n49_w104_s37_e80.nc \
  --gpcp-path /glade/work/jiachengye/33200/gpcp/stats/gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.nc \
  --price-csv corn_etf_prices.csv \
  --out-dir corn_etf_daily_decision_leadbylead_expanding_yearly/signal_buffer_0p0pct \
  --signal-buffer 0.0 \
  --make-plots \
  --overwrite
```

The script can also be run from the repository root by overriding the GLADE defaults with repo-relative paths:

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
