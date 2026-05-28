#!/usr/bin/env python3
"""
Expanding-yearly CORN ETF return regressions with lead-specific CFSv2 factors.

Unlike the weekly script, this version uses every trading day with an available
CFSv2 initialization.  The main target is the future 5-trading-day CORN ETF
return.  Trading metrics use a daily-rebalanced position so the equity curves
are interpretable as a daily strategy, while the regression target remains the
5-trading-day forward return.  Regression training and OOS evaluation rows are
restricted to the requested season window, which defaults to the full year.
For each OOS test year Y, each lead/model specification is cross-validated on
rows from the training start year through Y-1, then refit on that full expanding
training window and evaluated on year Y. Equity plots use a continuous
decision-date axis.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LOCAL_PRICE_CSV = SCRIPT_DIR / "corn_etf_prices.csv"
DEFAULT_CFSV2_ROOT = Path("/glade/work/jiachengye/33200/cfsv2/validtime_yearly")
DEFAULT_ERA5_PATH = Path("/glade/work/jiachengye/33200/era5_daily_surface_stats_2011_2025_n49_w104_s37_e80.nc")
DEFAULT_GPCP_PATH = Path(
    "/glade/work/jiachengye/33200/gpcp/stats/"
    "gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.nc"
)
DEFAULT_OUT_DIR = Path("/glade/work/jiachengye/33200/cfsv2/corn_etf_daily_decision_leadbylead_expanding_yearly")
DEFAULT_LEAD_DAYS = (7, 14, 21, 28, 30)

VARIABLE_SPECS = {
    "t2m": {
        "forecast_var": "t2m_mean",
        "count_var": "t2m_n_valid_grid_points",
        "scale": 1.0,
        "units": "K",
    },
    "spfh": {
        "forecast_var": "spfh_mean",
        "count_var": "spfh_n_valid_grid_points",
        "scale": 1.0,
        "units": "kg kg-1",
    },
    "precip": {
        "forecast_var": "precip_mean",
        "count_var": "precip_n_valid_grid_points",
        "scale": 4.0,
        "units": "mm/day equivalent",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Expanding-yearly CORN ETF return regressions with lead-specific CFSv2 weather factors."
        )
    )
    parser.add_argument("--cfsv2-root", type=Path, default=DEFAULT_CFSV2_ROOT)
    parser.add_argument("--era5-path", type=Path, default=DEFAULT_ERA5_PATH)
    parser.add_argument("--gpcp-path", type=Path, default=DEFAULT_GPCP_PATH)
    parser.add_argument("--price-csv", type=Path, default=None, help="Optional local CORN price CSV.")
    parser.add_argument("--symbol", default="CORN", help="Yahoo Finance ticker if --price-csv is not supplied.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--start-year", type=int, default=2011)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--lead-days",
        default=",".join(str(day) for day in DEFAULT_LEAD_DAYS),
        help="Comma-separated CFSv2 lead days. Default: 7,14,21,28,30.",
    )
    parser.add_argument("--horizon-trading-days", type=int, default=5)
    parser.add_argument("--split-date", default="2022-12-31", help="Retained for compatibility; expanding-yearly mode ignores this.")
    parser.add_argument("--season-start", default="01-01", help="Inclusive month-day for seasonal sample start.")
    parser.add_argument("--season-end", default="12-31", help="Inclusive month-day for seasonal sample end.")
    parser.add_argument("--train-start-year", type=int, default=2011)
    parser.add_argument("--train-end-year", type=int, default=2021, help="Retained for compatibility; expanding-yearly mode trains through test_year - 1.")
    parser.add_argument("--test-start-year", type=int, default=2022)
    parser.add_argument("--test-end-year", type=int, default=2025)
    parser.add_argument("--cv-splits", type=int, default=5)
    parser.add_argument("--fixed-return-threshold", type=float, default=0.02)
    parser.add_argument("--test-window-days", type=int, default=63, help="Retained for compatibility; expanding-yearly mode ignores this.")
    parser.add_argument("--retrain-step-days", type=int, default=63, help="Retained for compatibility; expanding-yearly mode ignores this.")
    parser.add_argument("--min-train-days", type=int, default=756)
    parser.add_argument("--transaction-cost-bps", type=float, default=5.0)
    parser.add_argument("--signal-buffer", type=float, default=0.0)
    parser.add_argument(
        "--climatology-mode",
        choices=("expanding", "full"),
        default="expanding",
        help="Use past-only expanding climatology or full-sample climatology for weather anomalies.",
    )
    parser.add_argument("--climatology-window-days", type=int, default=10)
    parser.add_argument("--min-climatology-count", type=int, default=5)
    parser.add_argument("--init-obs-window-days", type=int, default=7)
    parser.add_argument("--ridge-alphas", default="0.01,0.1,1,10,100")
    parser.add_argument(
        "--min-weather-coverage",
        type=float,
        default=1.0,
        help="Minimum weather_cfsv2_coverage_7_30 required for a trading day.",
    )
    parser.add_argument("--make-plots", action="store_true")
    parser.add_argument("--plot-dpi", type=int, default=180)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def parse_month_day(value: str) -> tuple[int, int]:
    parts = value.split("-")
    if len(parts) != 2:
        raise ValueError(f"Expected MM-DD, got {value!r}")
    month, day = int(parts[0]), int(parts[1])
    if month < 1 or month > 12 or day < 1 or day > 31:
        raise ValueError(f"Invalid MM-DD value: {value!r}")
    return month, day


def in_month_day_window(dates: pd.Series, start: tuple[int, int], end: tuple[int, int]) -> pd.Series:
    timestamps = pd.to_datetime(dates)
    values = timestamps.dt.month * 100 + timestamps.dt.day
    start_value = start[0] * 100 + start[1]
    end_value = end[0] * 100 + end[1]
    if start_value <= end_value:
        return (values >= start_value) & (values <= end_value)
    return (values >= start_value) | (values <= end_value)


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak_{stamp}")
    shutil.copy2(path, backup_path)
    print(f"Backed up {path} -> {backup_path}", flush=True)


def prepare_output(path: Path, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return
    if not overwrite:
        raise FileExistsError(f"{path} exists; pass --overwrite to replace it")
    backup(path)


def yyyymmdd_to_dates(values: np.ndarray) -> pd.Series:
    labels = []
    for value in values:
        integer = int(value)
        labels.append(f"{integer:08d}" if integer > 0 else None)
    return pd.Series(pd.to_datetime(labels, format="%Y%m%d", errors="coerce")).dt.normalize()


def seasonal_day_index(dates: pd.Series) -> np.ndarray:
    result = []
    base = dt.date(2001, 1, 1)
    for value in pd.to_datetime(dates):
        if pd.isna(value):
            result.append(np.nan)
            continue
        month = int(value.month)
        day = int(value.day)
        if month == 2 and day == 29:
            month, day = 2, 28
        comparable = dt.date(2001, month, day)
        result.append((comparable - base).days + 1)
    return np.asarray(result, dtype=float)


def circular_day_distance(left: np.ndarray, right: float) -> np.ndarray:
    distance = np.abs(left - right)
    return np.minimum(distance, 365.0 - distance)


def cfsv2_year_path(root: Path, year: int) -> Path:
    return root / f"cfsv2_daily00z_validtime_{year}.nc"


def load_cfsv2_long(root: Path, start_year: int, end_year: int, lead_days: list[int]) -> pd.DataFrame:
    rows = []

    for year in range(start_year, end_year + 1):
        path = cfsv2_year_path(root, year)
        if not path.exists():
            raise FileNotFoundError(path)

        print(f"Loading CFSv2 {path}", flush=True)
        with xr.open_dataset(path, decode_times=False) as ds:
            required = ["valid_date_yyyymmdd", "source_init_date_yyyymmdd", "lead_time"]
            for spec in VARIABLE_SPECS.values():
                required.extend([spec["forecast_var"], spec["count_var"]])
            missing = [name for name in required if name not in ds]
            if missing:
                raise KeyError(f"{path} missing required fields: {missing}")

            valid_dates = yyyymmdd_to_dates(np.asarray(ds["valid_date_yyyymmdd"].values))
            init_date_values = np.asarray(ds["source_init_date_yyyymmdd"].values)
            lead_hours = np.asarray(ds["lead_time"].values, dtype=np.int32)
            lead_day_values = (lead_hours // 24).astype(np.int32)
            source_found = np.asarray(ds["source_file_found"].values, dtype=float) if "source_file_found" in ds else None

            values_by_var = {}
            counts_by_var = {}
            for variable, spec in VARIABLE_SPECS.items():
                values_by_var[variable] = np.asarray(ds[spec["forecast_var"]].values, dtype=float) * float(spec["scale"])
                counts_by_var[variable] = np.asarray(ds[spec["count_var"]].values, dtype=float)

        for lead_index, lead_day in enumerate(lead_day_values):
            lead_day_int = int(lead_day)
            if lead_day_int not in lead_days:
                continue
            init_dates = yyyymmdd_to_dates(init_date_values[:, lead_index])
            frame = pd.DataFrame(
                {
                    "decision_date": init_dates,
                    "valid_date": valid_dates,
                    "lead_day": lead_day_int,
                    "source_file_found": source_found[:, lead_index] if source_found is not None else 1.0,
                }
            )
            for variable in VARIABLE_SPECS:
                value = values_by_var[variable][:, lead_index]
                count = counts_by_var[variable][:, lead_index]
                value = np.where(np.isfinite(count) & (count > 0), value, np.nan)
                frame[f"{variable}_forecast"] = value
                frame[f"{variable}_grid_count"] = count
            rows.append(frame.dropna(subset=["decision_date", "valid_date"]))

    if not rows:
        raise ValueError("No CFSv2 rows loaded")
    out = pd.concat(rows, ignore_index=True)
    out["decision_date"] = pd.to_datetime(out["decision_date"]).dt.normalize()
    out["valid_date"] = pd.to_datetime(out["valid_date"]).dt.normalize()
    return out.sort_values(["lead_day", "valid_date", "decision_date"]).reset_index(drop=True)


def add_smoothed_climatology(
    frame: pd.DataFrame,
    date_col: str,
    value_col: str,
    out_prefix: str,
    group_cols: list[str],
    window_days: int,
    min_count: int,
    mode: str,
) -> pd.DataFrame:
    out = frame.copy()
    out[f"{out_prefix}_clim"] = np.nan
    out[f"{out_prefix}_clim_std"] = np.nan
    half_window = max(float(window_days) / 2.0, 0.0)
    pieces = []
    grouped = out.groupby(group_cols, dropna=False, group_keys=False) if group_cols else [(None, out)]

    for _, group in grouped:
        group = group.sort_values(date_col).copy()
        dates = pd.to_datetime(group[date_col]).to_numpy()
        season_day = seasonal_day_index(group[date_col])
        values = group[value_col].to_numpy(dtype=float)
        clim = np.full(len(group), np.nan, dtype=float)
        clim_std = np.full(len(group), np.nan, dtype=float)

        for index in range(len(group)):
            if not np.isfinite(season_day[index]):
                continue
            mask = circular_day_distance(season_day, season_day[index]) <= half_window
            if mode == "expanding":
                mask &= dates < dates[index]
            elif mode == "full":
                mask &= np.arange(len(group)) != index
            else:
                raise ValueError(f"Unknown climatology mode: {mode}")
            mask &= np.isfinite(values)
            if int(mask.sum()) < min_count:
                continue
            clim[index] = float(np.mean(values[mask]))
            std = float(np.std(values[mask], ddof=1)) if int(mask.sum()) > 1 else np.nan
            clim_std[index] = std if np.isfinite(std) and std > 0.0 else np.nan

        group[f"{out_prefix}_clim"] = clim
        group[f"{out_prefix}_clim_std"] = clim_std
        pieces.append(group)

    out = pd.concat(pieces, ignore_index=True).sort_index()
    out[f"{out_prefix}_anom"] = out[value_col] - out[f"{out_prefix}_clim"]
    out[f"{out_prefix}_z"] = out[f"{out_prefix}_anom"] / out[f"{out_prefix}_clim_std"]
    return out


def add_model_forecast_climatology(frame: pd.DataFrame, window_days: int, min_count: int, mode: str) -> pd.DataFrame:
    out = frame.copy()
    for variable in VARIABLE_SPECS:
        out = add_smoothed_climatology(
            out,
            date_col="valid_date",
            value_col=f"{variable}_forecast",
            out_prefix=f"{variable}_forecast",
            group_cols=["lead_day"],
            window_days=window_days,
            min_count=min_count,
            mode=mode,
        )
    return out


def choose_existing_var(ds: xr.Dataset, candidates: tuple[str, ...], path: Path) -> str:
    for name in candidates:
        if name in ds:
            return name
    raise KeyError(f"None of {candidates} found in {path}; available variables: {list(ds.data_vars)}")


def read_observation_series(path: Path, candidates: tuple[str, ...], out_name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        date_col = next((col for col in ("date", "time", "Date", "Time") if col in df.columns), None)
        if date_col is None:
            raise KeyError(f"No date/time column found in {path}")
        value_col = next((col for col in candidates if col in df.columns), None)
        if value_col is None:
            raise KeyError(f"None of {candidates} found in {path}; available columns: {list(df.columns)}")
        out = df[[date_col, value_col]].copy()
        out.columns = ["date", out_name]
    else:
        with xr.open_dataset(path) as ds:
            value_col = choose_existing_var(ds, candidates, path)
            series = ds[value_col].to_series()
        out = series.rename(out_name).reset_index()
        if "time" not in out.columns:
            raise KeyError(f"{path} variable {value_col} does not have a time coordinate")
        out = out[["time", out_name]].rename(columns={"time": "date"})

    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out[out_name] = pd.to_numeric(out[out_name], errors="coerce")
    return out.dropna(subset=["date"]).groupby("date", as_index=False)[out_name].mean()


def load_observed_weather(era5_path: Path, gpcp_path: Path) -> pd.DataFrame:
    t2m = read_observation_series(era5_path, ("t2m_mean",), "t2m_obs")
    spfh = read_observation_series(era5_path, ("q2m_mean",), "spfh_obs")
    precip = read_observation_series(gpcp_path, ("precip_area_weighted_mean", "mean_mm_day"), "precip_obs")
    return t2m.merge(spfh, on="date", how="outer").merge(precip, on="date", how="outer").sort_values("date")


def add_observed_climatology(observed: pd.DataFrame, window_days: int, min_count: int, mode: str) -> pd.DataFrame:
    out = observed.copy()
    for variable in VARIABLE_SPECS:
        out = add_smoothed_climatology(
            out,
            date_col="date",
            value_col=f"{variable}_obs",
            out_prefix=f"{variable}_obs",
            group_cols=[],
            window_days=window_days,
            min_count=min_count,
            mode=mode,
        )
    return out.sort_values("date").reset_index(drop=True)


def make_initial_observed_features(observed: pd.DataFrame, window_days: int) -> pd.DataFrame:
    daily = observed.set_index("date").sort_index()
    rows = pd.DataFrame({"decision_date": daily.index})
    for variable in VARIABLE_SPECS:
        rows[f"init_obs_{variable}_anom"] = daily[f"{variable}_obs_anom"].rolling(window_days, min_periods=1).mean().shift(1).to_numpy()
        rows[f"init_obs_{variable}_z"] = daily[f"{variable}_obs_z"].rolling(window_days, min_periods=1).mean().shift(1).to_numpy()
    rows["decision_date"] = pd.to_datetime(rows["decision_date"]).dt.normalize()
    return rows.reset_index(drop=True)


def make_weather_features(cfsv2_long: pd.DataFrame, init_observed: pd.DataFrame, lead_days: list[int]) -> pd.DataFrame:
    rows = []
    for _, row in cfsv2_long.iterrows():
        lead_day = int(row["lead_day"])
        record = {"decision_date": row["decision_date"]}
        record[f"weather_cfsv2_source_found_l{lead_day}"] = row["source_file_found"]
        for variable in VARIABLE_SPECS:
            record[f"weather_cfsv2_{variable}_l{lead_day}"] = row[f"{variable}_forecast"]
            record[f"weather_cfsv2_{variable}_anom_l{lead_day}"] = row[f"{variable}_forecast_anom"]
            record[f"weather_cfsv2_{variable}_z_l{lead_day}"] = row[f"{variable}_forecast_z"]
            record[f"weather_cfsv2_{variable}_grid_count_l{lead_day}"] = row[f"{variable}_grid_count"]
        heat = row["t2m_forecast_z"]
        dryness = -row["precip_forecast_z"]
        record[f"weather_heat_forecast_z_l{lead_day}"] = heat
        record[f"weather_dryness_forecast_z_l{lead_day}"] = dryness
        record[f"weather_spfh_forecast_z_l{lead_day}"] = row["spfh_forecast_z"]
        record[f"weather_heat_x_dryness_l{lead_day}"] = heat * dryness
        rows.append(record)

    weather = pd.DataFrame(rows).groupby("decision_date", as_index=False).first()
    weather["decision_date"] = pd.to_datetime(weather["decision_date"]).dt.normalize()
    weather = weather.merge(init_observed, on="decision_date", how="left")

    for variable in VARIABLE_SPECS:
        anom_cols = [f"weather_cfsv2_{variable}_anom_l{lead}" for lead in lead_days if f"weather_cfsv2_{variable}_anom_l{lead}" in weather]
        raw_cols = [f"weather_cfsv2_{variable}_l{lead}" for lead in lead_days if f"weather_cfsv2_{variable}_l{lead}" in weather]
        weather[f"weather_cfsv2_{variable}_anom_7_30_mean"] = weather[anom_cols].mean(axis=1, skipna=True)
        weather[f"weather_cfsv2_{variable}_raw_7_30_mean"] = weather[raw_cols].mean(axis=1, skipna=True)

    heat_cols = [f"weather_heat_forecast_z_l{lead}" for lead in lead_days if f"weather_heat_forecast_z_l{lead}" in weather]
    dry_cols = [f"weather_dryness_forecast_z_l{lead}" for lead in lead_days if f"weather_dryness_forecast_z_l{lead}" in weather]
    interaction_cols = [f"weather_heat_x_dryness_l{lead}" for lead in lead_days if f"weather_heat_x_dryness_l{lead}" in weather]
    weather["weather_heat_forecast_z_7_30_mean"] = weather[heat_cols].mean(axis=1, skipna=True)
    weather["weather_dryness_forecast_z_7_30_mean"] = weather[dry_cols].mean(axis=1, skipna=True)
    weather["weather_heat_x_dryness_7_30_mean"] = weather[interaction_cols].mean(axis=1, skipna=True)

    weather["init_obs_heat_z"] = weather["init_obs_t2m_z"]
    weather["init_obs_dryness_z"] = -weather["init_obs_precip_z"]
    weather["init_obs_spfh_z"] = weather["init_obs_spfh_z"]

    for lead in lead_days:
        heat_col = f"weather_heat_forecast_z_l{lead}"
        dry_col = f"weather_dryness_forecast_z_l{lead}"
        spfh_col = f"weather_spfh_forecast_z_l{lead}"
        if heat_col in weather:
            weather[f"weather_heat_projected_change_l{lead}"] = weather[heat_col] - weather["init_obs_heat_z"]
        if dry_col in weather:
            weather[f"weather_dryness_projected_change_l{lead}"] = weather[dry_col] - weather["init_obs_dryness_z"]
        if spfh_col in weather:
            weather[f"weather_spfh_projected_change_l{lead}"] = weather[spfh_col] - weather["init_obs_spfh_z"]
        if f"weather_heat_projected_change_l{lead}" in weather and f"weather_dryness_projected_change_l{lead}" in weather:
            weather[f"weather_projected_heat_x_dryness_l{lead}"] = (
                weather[f"weather_heat_projected_change_l{lead}"]
                * weather[f"weather_dryness_projected_change_l{lead}"]
            )

    projected_heat_cols = [f"weather_heat_projected_change_l{lead}" for lead in lead_days if f"weather_heat_projected_change_l{lead}" in weather]
    projected_dry_cols = [f"weather_dryness_projected_change_l{lead}" for lead in lead_days if f"weather_dryness_projected_change_l{lead}" in weather]
    projected_interaction_cols = [
        f"weather_projected_heat_x_dryness_l{lead}"
        for lead in lead_days
        if f"weather_projected_heat_x_dryness_l{lead}" in weather
    ]
    weather["weather_heat_projected_change_7_30_mean"] = weather[projected_heat_cols].mean(axis=1, skipna=True)
    weather["weather_dryness_projected_change_7_30_mean"] = weather[projected_dry_cols].mean(axis=1, skipna=True)
    weather["weather_projected_heat_x_dryness_7_30_mean"] = weather[projected_interaction_cols].mean(axis=1, skipna=True)

    source_cols = [f"weather_cfsv2_source_found_l{lead}" for lead in lead_days if f"weather_cfsv2_source_found_l{lead}" in weather]
    weather["weather_cfsv2_coverage_7_30"] = weather[source_cols].mean(axis=1)
    return weather.sort_values("decision_date").reset_index(drop=True)


def fetch_price_yfinance(symbol: str, start: str, end: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("Install yfinance or pass --price-csv") from exc

    data = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError(f"Yahoo Finance returned no rows for {symbol}")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    close_col = "Close" if "Close" in data.columns else "Adj Close"
    if close_col not in data.columns:
        raise KeyError(f"Could not find Close or Adj Close in Yahoo Finance columns: {list(data.columns)}")

    reset = data.reset_index()
    date_col = next((col for col in ("Date", "Datetime", "date", "datetime", "index") if col in reset.columns), None)
    if date_col is None:
        date_col = reset.columns[0]
    out = reset[[date_col, close_col]].copy()
    out.columns = ["date", "close"]
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    return out.dropna(subset=["date", "close"]).sort_values("date")


def read_price_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    date_col = next((col for col in ("date", "Date", "datetime", "Datetime", "time") if col in df.columns), None)
    close_col = next((col for col in ("close", "Close", "adj_close", "Adj Close", "Adj_Close") if col in df.columns), None)
    if date_col is None or close_col is None:
        raise KeyError(f"Price CSV needs date and close columns; got {list(df.columns)}")
    out = df[[date_col, close_col]].copy()
    out.columns = ["date", "close"]
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    return out.dropna(subset=["date", "close"]).sort_values("date")


def load_prices(args: argparse.Namespace) -> pd.DataFrame:
    if args.price_csv is not None:
        print(f"Reading price CSV {args.price_csv}", flush=True)
        return read_price_csv(args.price_csv)
    start = f"{args.start_year}-01-01"
    end = f"{args.end_year + 1}-02-01"
    print(f"Downloading {args.symbol} prices from Yahoo Finance: {start} to {end}", flush=True)
    try:
        return fetch_price_yfinance(args.symbol, start, end)
    except Exception as exc:
        if DEFAULT_LOCAL_PRICE_CSV.exists():
            print(
                f"Yahoo Finance price download failed ({exc}); "
                f"reading local price CSV {DEFAULT_LOCAL_PRICE_CSV}",
                flush=True,
            )
            return read_price_csv(DEFAULT_LOCAL_PRICE_CSV)
        raise


def build_daily_price_panel(
    daily_prices: pd.DataFrame,
    horizon_trading_days: int,
    class_threshold: float,
) -> pd.DataFrame:
    panel = daily_prices.drop_duplicates("date").sort_values("date").copy()
    panel = panel.rename(columns={"date": "decision_date"})
    panel["return_1d"] = panel["close"].pct_change()
    panel["log_return_1d"] = np.log(panel["close"] / panel["close"].shift(1))
    panel["target_next_1d_return"] = panel["close"].shift(-1) / panel["close"] - 1.0
    panel["target_return"] = panel["close"].shift(-horizon_trading_days) / panel["close"] - 1.0
    panel["target_class"] = 0
    panel.loc[panel["target_return"] >= class_threshold, "target_class"] = 1
    panel.loc[panel["target_return"] <= -class_threshold, "target_class"] = -1

    for lag in (1, 2, 5, 10, 21):
        panel[f"price_return_lag_{lag}d"] = panel["return_1d"].shift(lag)
    for window in (5, 10, 21, 63):
        panel[f"price_vol_{window}d"] = panel["return_1d"].rolling(window).std()
        panel[f"price_momentum_{window}d"] = panel["close"] / panel["close"].shift(window) - 1.0

    panel["month"] = panel["decision_date"].dt.month
    panel["quarter"] = panel["decision_date"].dt.quarter
    iso_week = panel["decision_date"].dt.isocalendar().week.astype(float)
    panel["weekofyear_sin"] = np.sin(2.0 * np.pi * iso_week / 52.0)
    panel["weekofyear_cos"] = np.cos(2.0 * np.pi * iso_week / 52.0)
    panel["dayofweek_sin"] = np.sin(2.0 * np.pi * panel["decision_date"].dt.dayofweek / 5.0)
    panel["dayofweek_cos"] = np.cos(2.0 * np.pi * panel["decision_date"].dt.dayofweek / 5.0)
    panel["is_planting_season"] = panel["month"].isin([4, 5]).astype(int)
    panel["is_pollination_season"] = panel["month"].isin([7, 8]).astype(int)
    panel["is_harvest_season"] = panel["month"].isin([9, 10, 11]).astype(int)
    panel["is_winter_storage_season"] = panel["month"].isin([12, 1, 2]).astype(int)
    return panel


def build_model_panel(price_panel: pd.DataFrame, weather: pd.DataFrame, min_weather_coverage: float) -> pd.DataFrame:
    panel = price_panel.merge(weather, on="decision_date", how="left")
    if "weather_cfsv2_coverage_7_30" in panel:
        panel = panel[panel["weather_cfsv2_coverage_7_30"] >= min_weather_coverage].copy()
    return panel.sort_values("decision_date").reset_index(drop=True)


def filter_season_panel(panel: pd.DataFrame, season_start: str, season_end: str) -> pd.DataFrame:
    start = parse_month_day(season_start)
    end = parse_month_day(season_end)
    mask = in_month_day_window(panel["decision_date"], start, end)
    out = panel.loc[mask].copy()
    out["season_year"] = out["decision_date"].dt.year
    return out.sort_values("decision_date").reset_index(drop=True)


def price_calendar_columns(panel: pd.DataFrame) -> list[str]:
    starts = ("price_return_lag_", "price_vol_", "price_momentum_")
    cols = [col for col in panel.columns if col.startswith(starts)]
    cols.extend(
        [
            "month",
            "quarter",
            "weekofyear_sin",
            "weekofyear_cos",
            "dayofweek_sin",
            "dayofweek_cos",
            "is_planting_season",
            "is_pollination_season",
            "is_harvest_season",
            "is_winter_storage_season",
        ]
    )
    return [col for col in cols if col in panel.columns]


def lead_forecast_columns(lead_day: int) -> list[str]:
    return [
        f"weather_heat_forecast_z_l{lead_day}",
        f"weather_dryness_forecast_z_l{lead_day}",
        f"weather_heat_x_dryness_l{lead_day}",
    ]


def lead_projected_change_columns(lead_day: int) -> list[str]:
    return [
        f"weather_heat_projected_change_l{lead_day}",
        f"weather_dryness_projected_change_l{lead_day}",
        f"weather_projected_heat_x_dryness_l{lead_day}",
    ]


def require_columns(panel: pd.DataFrame, columns: list[str], feature_set: str) -> None:
    missing = [column for column in columns if column not in panel.columns]
    if missing:
        raise KeyError(f"{feature_set} missing columns: {missing}")


def make_lead_feature_sets(panel: pd.DataFrame, lead_day: int) -> dict[str, list[str]]:
    baseline = price_calendar_columns(panel)
    forecast = lead_forecast_columns(lead_day)
    projected = lead_projected_change_columns(lead_day)
    feature_sets = {
        f"lead{lead_day:02d}_price_calendar": baseline,
        f"lead{lead_day:02d}_forecast_anom": baseline + forecast,
        f"lead{lead_day:02d}_forecast_anom_projected_change": baseline + forecast + projected,
    }
    for name, columns in feature_sets.items():
        require_columns(panel, columns, name)
    return feature_sets


def make_regression_estimator(alphas: list[float], cv_splits: int):
    try:
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import Ridge
        from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required for the daily ETF return regression test") from exc

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", Ridge()),
        ]
    )
    cv = TimeSeriesSplit(n_splits=cv_splits)
    return GridSearchCV(
        estimator=pipeline,
        param_grid={"model__alpha": np.asarray(alphas, dtype=float)},
        cv=cv,
        scoring="neg_mean_squared_error",
        refit=True,
    )


def fitted_ridge_alpha(estimator) -> float:
    if hasattr(estimator, "best_params_"):
        return float(estimator.best_params_["model__alpha"])
    if hasattr(estimator, "named_steps") and hasattr(estimator.named_steps["model"], "alpha_"):
        return float(estimator.named_steps["model"].alpha_)
    return np.nan


def expanding_yearly_regression_predict(
    panel: pd.DataFrame,
    feature_set_name: str,
    columns: list[str],
    lead_day: int,
    train_start_year: int,
    test_start_year: int,
    test_end_year: int,
    min_train_days: int,
    ridge_alphas: list[float],
    cv_splits: int,
) -> pd.DataFrame:
    usable = panel.dropna(subset=["target_return", "target_next_1d_return"]).sort_values("decision_date").reset_index(drop=True)
    if "season_year" not in usable.columns:
        usable["season_year"] = usable["decision_date"].dt.year

    if cv_splits < 2:
        raise ValueError(f"cv_splits must be at least 2, got {cv_splits}")
    predictions = []
    for test_year in range(test_start_year, test_end_year + 1):
        train = usable[
            (usable["season_year"] >= train_start_year) & (usable["season_year"] <= test_year - 1)
        ].copy()
        test = usable[usable["season_year"] == test_year].copy()
        if len(train) < min_train_days or test.empty:
            continue
        if len(train) <= cv_splits:
            raise ValueError(f"Training rows must exceed cv_splits; got train={len(train)}, cv_splits={cv_splits}")

        estimator = make_regression_estimator(ridge_alphas, cv_splits)
        estimator.fit(train[columns], train["target_return"].astype(float))

        fold = test[["decision_date", "close", "target_return", "target_next_1d_return", "target_class"]].copy()
        fold["season_year"] = test["season_year"].to_numpy()
        fold["test_year"] = test_year
        fold["feature_set"] = feature_set_name
        fold["lead_day"] = lead_day
        fold["model"] = feature_set_name.replace(f"lead{lead_day:02d}_", "")
        fold["predicted_return"] = estimator.predict(test[columns])
        fold["train_mean_return"] = float(train["target_return"].mean())
        fold["ridge_alpha"] = fitted_ridge_alpha(estimator)
        fold["train_start"] = train["decision_date"].min()
        fold["train_end"] = train["decision_date"].max()
        fold["train_n"] = len(train)
        fold["cv_splits"] = cv_splits
        predictions.append(fold)
    if not predictions:
        return pd.DataFrame()
    return pd.concat(predictions, ignore_index=True)


def run_lead_regressions(
    panel: pd.DataFrame,
    lead_days: list[int],
    train_start_year: int,
    test_start_year: int,
    test_end_year: int,
    min_train_days: int,
    ridge_alphas: list[float],
    cv_splits: int,
) -> pd.DataFrame:
    predictions = []
    for lead_day in lead_days:
        feature_sets = make_lead_feature_sets(panel, lead_day)
        for feature_set, columns in feature_sets.items():
            fold_predictions = expanding_yearly_regression_predict(
                panel,
                feature_set,
                columns,
                lead_day,
                train_start_year,
                test_start_year,
                test_end_year,
                min_train_days,
                ridge_alphas,
                cv_splits,
            )
            if not fold_predictions.empty:
                predictions.append(fold_predictions)
    if not predictions:
        raise ValueError("No predictions were produced")
    return pd.concat(predictions, ignore_index=True)


def add_strategy_returns(predictions: pd.DataFrame, transaction_cost_bps: float, signal_buffer: float) -> pd.DataFrame:
    frames = []
    cost = transaction_cost_bps / 10000.0
    for feature_set, frame in predictions.groupby("feature_set", sort=False):
        frame = frame.sort_values("decision_date").copy()
        predicted = frame["predicted_return"].astype(float)
        frame["position"] = 0
        frame.loc[predicted > signal_buffer, "position"] = 1
        frame.loc[predicted < -signal_buffer, "position"] = -1
        frame["turnover"] = frame["position"].diff().abs().fillna(frame["position"].abs())
        frame["strategy_return_daily_rebalanced"] = (
            frame["position"] * frame["target_next_1d_return"].astype(float) - cost * frame["turnover"]
        )
        frame["strategy_return_5td_signal_proxy"] = (
            frame["position"] * frame["target_return"].astype(float) - cost * frame["turnover"]
        )
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def max_drawdown(simple_returns: pd.Series) -> float:
    equity = (1.0 + simple_returns.fillna(0.0)).cumprod()
    peak = equity.cummax()
    drawdown = equity / peak - 1.0
    return float(drawdown.min())


def strategy_summary(prefix: str, simple_returns: pd.Series, turnover: pd.Series, position: pd.Series) -> dict[str, float]:
    daily_mean = float(simple_returns.mean())
    daily_std = float(simple_returns.std(ddof=1))
    total_return = float((1.0 + simple_returns.fillna(0.0)).prod() - 1.0)
    n_obs = len(simple_returns)
    return {
        f"{prefix}_total_return": total_return,
        f"{prefix}_annual_return": (1.0 + total_return) ** (252.0 / n_obs) - 1.0 if n_obs else np.nan,
        f"{prefix}_annual_vol": daily_std * np.sqrt(252.0),
        f"{prefix}_sharpe": daily_mean / daily_std * np.sqrt(252.0) if daily_std > 0.0 else np.nan,
        f"{prefix}_max_drawdown": max_drawdown(simple_returns),
        f"{prefix}_mean_turnover": float(turnover.mean()),
        f"{prefix}_mean_position": float(position.mean()),
        f"{prefix}_cash_share": float((position == 0).mean()),
    }


def regression_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    rows = []
    for feature_set, frame in predictions.groupby("feature_set", sort=False):
        actual = frame["target_return"].astype(float).to_numpy()
        predicted = frame["predicted_return"].astype(float).to_numpy()
        train_mean = frame["train_mean_return"].astype(float).to_numpy()
        mse_model = float(np.mean((predicted - actual) ** 2))
        mse_train_mean = float(np.mean((train_mean - actual) ** 2))
        corr = np.corrcoef(predicted, actual)[0, 1] if np.std(predicted) > 0 and np.std(actual) > 0 else np.nan
        row = {
            "lead_day": int(frame["lead_day"].iloc[0]),
            "model": frame["model"].iloc[0],
            "feature_set": feature_set,
            "n_oos": len(frame),
            "start_date": frame["decision_date"].min().strftime("%Y-%m-%d"),
            "end_date": frame["decision_date"].max().strftime("%Y-%m-%d"),
            "oos_r2_vs_train_mean": 1.0 - mse_model / mse_train_mean if mse_train_mean > 0.0 else np.nan,
            "rmse_5td_target": float(np.sqrt(mean_squared_error(actual, predicted))),
            "mae_5td_target": float(mean_absolute_error(actual, predicted)),
            "corr_pred_actual_5td": corr,
            "direction_accuracy_5td": float(np.mean(np.sign(predicted) == np.sign(actual))),
            "mean_predicted_return": float(np.mean(predicted)),
            "mean_actual_5td_return": float(np.mean(actual)),
            "mean_ridge_alpha": float(frame["ridge_alpha"].mean()),
        }
        row.update(
            strategy_summary(
                "daily_rebalanced",
                frame["strategy_return_daily_rebalanced"],
                frame["turnover"],
                frame["position"],
            )
        )
        row.update(
            strategy_summary(
                "signal_5td_proxy",
                frame["strategy_return_5td_signal_proxy"],
                frame["turnover"],
                frame["position"],
            )
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["lead_day", "model"]).reset_index(drop=True)


def setup_matplotlib():
    config_dir = Path(tempfile.gettempdir()) / "matplotlib"
    config_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(config_dir))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def equity_curve_with_initial_point(frame: pd.DataFrame, return_col: str) -> tuple[pd.Series, pd.Series]:
    frame = frame.sort_values("decision_date")
    equity = (1.0 + frame[return_col].fillna(0.0)).cumprod()
    if frame.empty:
        return frame["decision_date"], equity
    first_date = pd.to_datetime(frame["decision_date"].iloc[0])
    initial_date = first_date - pd.Timedelta(days=1)
    dates = pd.concat([pd.Series([initial_date]), frame["decision_date"].reset_index(drop=True)], ignore_index=True)
    values = pd.concat([pd.Series([1.0]), equity.reset_index(drop=True)], ignore_index=True)
    return dates, values


def make_plots(predictions: pd.DataFrame, metrics: pd.DataFrame, out_dir: Path, overwrite: bool, dpi: int) -> list[Path]:
    plt = setup_matplotlib()
    plot_dir = out_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    label_order = ["price_calendar", "forecast_anom", "forecast_anom_projected_change"]
    for lead_day, lead_frame in predictions.groupby("lead_day", sort=True):
        fig, ax = plt.subplots(figsize=(9, 4.8))
        for model in label_order:
            frame = lead_frame[lead_frame["model"] == model].sort_values("decision_date")
            if frame.empty:
                continue
            dates, equity = equity_curve_with_initial_point(frame, "strategy_return_daily_rebalanced")
            ax.plot(dates, equity, label=model)
        ax.set_title(f"CORN ETF Daily-Rebalanced Strategy (+{int(lead_day)} Lead Only)")
        ax.set_xlabel("Decision Date")
        ax.set_ylabel("Growth of $1")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        path = plot_dir / f"lead_{int(lead_day):02d}_daily_rebalanced_equity.png"
        prepare_output(path, overwrite)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        paths.append(path)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    pivot = metrics.pivot(index="lead_day", columns="model", values="oos_r2_vs_train_mean").sort_index()
    columns = [col for col in label_order if col in pivot.columns]
    x = np.arange(len(pivot.index))
    width = 0.24
    offsets = np.linspace(-width, width, len(columns))
    for offset, column in zip(offsets, columns):
        ax.bar(x + offset, pivot[column], width=width, label=column)
    ax.axhline(0.0, color="0.35", linewidth=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"+{lead}" for lead in pivot.index])
    ax.set_xlabel("CFSv2 Lead Day")
    ax.set_ylabel("OOS R2 vs expanding train mean")
    ax.set_title("Daily-Decision Return Regression OOS R2")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8)
    path = plot_dir / "daily_decision_oos_r2_summary.png"
    prepare_output(path, overwrite)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    pivot = metrics.pivot(index="lead_day", columns="model", values="daily_rebalanced_sharpe").sort_index()
    columns = [col for col in label_order if col in pivot.columns]
    x = np.arange(len(pivot.index))
    width = 0.24
    offsets = np.linspace(-width, width, len(columns))
    for offset, column in zip(offsets, columns):
        ax.bar(x + offset, pivot[column], width=width, label=column)
    ax.axhline(0.0, color="0.35", linewidth=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"+{lead}" for lead in pivot.index])
    ax.set_xlabel("CFSv2 Lead Day")
    ax.set_ylabel("Daily-rebalanced Sharpe")
    ax.set_title("Daily-Decision Strategy Sharpe")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8)
    path = plot_dir / "daily_decision_sharpe_summary.png"
    prepare_output(path, overwrite)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)
    return paths


def write_metadata(args: argparse.Namespace, lead_days: list[int], ridge_alphas: list[float], paths: dict[str, Path], plot_paths: list[Path]) -> None:
    metadata = {
        "created_utc": dt.datetime.now(dt.UTC).isoformat(),
        "cfsv2_root": str(args.cfsv2_root),
        "era5_path": str(args.era5_path),
        "gpcp_path": str(args.gpcp_path),
        "price_csv": str(args.price_csv) if args.price_csv else None,
        "symbol": args.symbol,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "lead_days": lead_days,
        "horizon_trading_days": args.horizon_trading_days,
        "split_date": args.split_date,
        "train_start_year": args.train_start_year,
        "train_end_year": "test_year_minus_1",
        "test_start_year": args.test_start_year,
        "test_end_year": args.test_end_year,
        "cv_splits": args.cv_splits,
        "season_start": args.season_start,
        "season_end": args.season_end,
        "test_window_days": args.test_window_days,
        "retrain_step_days": args.retrain_step_days,
        "min_train_days": args.min_train_days,
        "signal_buffer": args.signal_buffer,
        "transaction_cost_bps": args.transaction_cost_bps,
        "climatology_mode": args.climatology_mode,
        "climatology_window_days": args.climatology_window_days,
        "min_climatology_count": args.min_climatology_count,
        "init_obs_window_days": args.init_obs_window_days,
        "ridge_alphas": ridge_alphas,
        "target_note": "Regression target is future N-trading-day CORN ETF return for each daily decision date.",
        "sample_note": (
            "Regression training and OOS evaluation rows are restricted by decision_date to the inclusive "
            "season window. Price lags, weather climatology, and initial observed rolling weather features are "
            "computed before this seasonal row filter."
        ),
        "training_note": (
            "For each test year Y and each lead/model, Ridge alpha is selected by time-series cross-validation "
            "within rows from train_start_year through Y-1. The final pipeline is then refit on that full "
            "expanding training window and evaluated on year Y."
        ),
        "strategy_note": (
            "Daily equity curves use daily-rebalanced one-day realized returns with the sign of the "
            "N-trading-day predicted return. signal_5td_proxy metrics compound overlapping N-trading-day "
            "signal returns and should be interpreted as a signal diagnostic, not a directly investable portfolio."
        ),
        "outputs": {name: str(path) for name, path in paths.items()},
        "plots": [str(path) for path in plot_paths],
    }
    metadata_path = args.out_dir / "cfsv2_corn_etf_daily_decision_metadata.json"
    prepare_output(metadata_path, args.overwrite)
    with metadata_path.open("w") as out:
        json.dump(metadata, out, indent=2, sort_keys=True)
        out.write("\n")
    print(f"Wrote {metadata_path}", flush=True)


def main() -> None:
    args = parse_args()
    lead_days = parse_int_list(args.lead_days)
    ridge_alphas = parse_float_list(args.ridge_alphas)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    cfsv2 = load_cfsv2_long(args.cfsv2_root, args.start_year, args.end_year, lead_days)
    cfsv2 = add_model_forecast_climatology(
        cfsv2,
        args.climatology_window_days,
        args.min_climatology_count,
        args.climatology_mode,
    )
    observed = load_observed_weather(args.era5_path, args.gpcp_path)
    observed = add_observed_climatology(
        observed,
        args.climatology_window_days,
        args.min_climatology_count,
        args.climatology_mode,
    )
    init_observed = make_initial_observed_features(observed, args.init_obs_window_days)
    weather = make_weather_features(cfsv2, init_observed, lead_days)
    prices = load_prices(args)
    price_panel = build_daily_price_panel(prices, args.horizon_trading_days, args.fixed_return_threshold)
    panel = build_model_panel(price_panel, weather, args.min_weather_coverage)
    panel = filter_season_panel(panel, args.season_start, args.season_end)
    predictions = run_lead_regressions(
        panel,
        lead_days,
        args.train_start_year,
        args.test_start_year,
        args.test_end_year,
        args.min_train_days,
        ridge_alphas,
        args.cv_splits,
    )
    predictions = add_strategy_returns(predictions, args.transaction_cost_bps, args.signal_buffer)
    metrics = regression_metrics(predictions)

    paths = {
        "feature_panel": args.out_dir / "cfsv2_corn_etf_daily_decision_feature_panel.csv",
        "regression_predictions": args.out_dir / "cfsv2_corn_etf_daily_decision_regression_predictions.csv",
        "regression_metrics": args.out_dir / "cfsv2_corn_etf_daily_decision_regression_metrics.csv",
    }
    for path in paths.values():
        prepare_output(path, args.overwrite)
    panel.to_csv(paths["feature_panel"], index=False)
    predictions.to_csv(paths["regression_predictions"], index=False)
    metrics.to_csv(paths["regression_metrics"], index=False)

    plot_paths = []
    if args.make_plots:
        plot_paths = make_plots(predictions, metrics, args.out_dir, args.overwrite, args.plot_dpi)
    write_metadata(args, lead_days, ridge_alphas, paths, plot_paths)
    print(f"Wrote {paths['feature_panel']}", flush=True)
    print(f"Wrote {paths['regression_predictions']}", flush=True)
    print(f"Wrote {paths['regression_metrics']}", flush=True)


if __name__ == "__main__":
    main()
