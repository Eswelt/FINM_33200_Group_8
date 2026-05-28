#!/usr/bin/env python3

from pathlib import Path
import datetime as dt
import re
import shutil

import numpy as np
import pandas as pd
import xarray as xr


DAILY_DIR = Path("/glade/work/jiachengye/33200/gpcp/daily")
OUT_DIR = Path("/glade/work/jiachengye/33200/gpcp/stats")

START_DATE = "2011-01-01"
END_DATE = "2025-12-31"
REGION = [49.0, -104.0, 37.0, -80.0]  # [north, west, south, east]

CSV = OUT_DIR / "gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.csv"
NC = OUT_DIR / "gpcp_daily_area_stats_20110101_20251231_north49_west104_south37_west80.nc"

DATE_RE = re.compile(r"_d(\d{8})_")


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak_{stamp}")
    shutil.copy2(path, backup_path)
    print(f"Backed up {path} -> {backup_path}")


def date_from_file(path: Path) -> pd.Timestamp:
    match = DATE_RE.search(path.name)
    if match is None:
        raise ValueError(f"Cannot parse date from {path}")
    return pd.Timestamp(match.group(1))


def local_files_by_date() -> dict[pd.Timestamp, Path]:
    files = {}
    for path in sorted(DAILY_DIR.glob("*/*.nc")):
        day = date_from_file(path)
        files[day] = path
    return files


def lon_intervals(west: float, east: float) -> list[tuple[float, float]]:
    west = west % 360.0
    east = east % 360.0
    if west < east:
        return [(west, east)]
    return [(west, 360.0), (0.0, east)]


def overlap_width(bounds: np.ndarray, intervals: list[tuple[float, float]]) -> np.ndarray:
    low = np.minimum(bounds[:, 0], bounds[:, 1]) % 360.0
    high = np.maximum(bounds[:, 0], bounds[:, 1]) % 360.0
    high = np.where(high == 0.0, 360.0, high)

    width = np.zeros(bounds.shape[0])
    for left, right in intervals:
        width += np.maximum(0.0, np.minimum(high, right) - np.maximum(low, left))
    return width


def area_weights(ds: xr.Dataset, region: list[float]) -> xr.DataArray:
    north, west, south, east = region

    lat_bounds = ds["lat_bounds"].values.astype(float)
    lon_bounds = ds["lon_bounds"].values.astype(float)

    lat_low = np.maximum(np.minimum(lat_bounds[:, 0], lat_bounds[:, 1]), south)
    lat_high = np.minimum(np.maximum(lat_bounds[:, 0], lat_bounds[:, 1]), north)
    lat_weight = np.maximum(
        0.0,
        np.sin(np.deg2rad(lat_high)) - np.sin(np.deg2rad(lat_low)),
    )

    lon_width = overlap_width(lon_bounds, lon_intervals(west, east))
    weights = lat_weight[:, None] * np.deg2rad(lon_width[None, :])

    return xr.DataArray(
        weights,
        dims=("latitude", "longitude"),
        coords={
            "latitude": ds["latitude"],
            "longitude": ds["longitude"],
        },
    )


def clean_precip(precip: xr.DataArray) -> xr.DataArray:
    valid = np.isfinite(precip)

    missing_value = precip.attrs.get("missing_value")
    if missing_value is not None:
        valid = valid & (precip != float(np.asarray(missing_value).ravel()[0]))

    fill_value = precip.attrs.get("_FillValue")
    if fill_value is not None:
        valid = valid & (precip != float(np.asarray(fill_value).ravel()[0]))

    valid_range = precip.attrs.get("valid_range")
    if valid_range is not None:
        low, high = np.asarray(valid_range, dtype=float).ravel()[:2]
        valid = valid & (precip >= low) & (precip <= high)
    else:
        valid = valid & (precip >= 0.0) & (precip <= 100.0)

    return precip.where(valid)


def weighted_mean_std(path: Path) -> tuple[float, float, int]:
    with xr.open_dataset(path, mask_and_scale=False) as ds:
        precip = ds["precip"].isel(time=0).astype(float)
        precip = clean_precip(precip)

        weights = area_weights(ds, REGION)
        valid = np.isfinite(precip) & (weights > 0.0)

        weights = weights.where(valid, 0.0)
        precip = precip.where(valid)

        total_weight = weights.sum()
        mean = (precip * weights).sum(skipna=True) / total_weight
        variance = (((precip - mean) ** 2) * weights).sum(skipna=True) / total_weight

        return (
            float(mean.item()),
            float(np.sqrt(variance.item())),
            int(valid.sum().item()),
        )


def main() -> None:
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    files = local_files_by_date()

    missing = [day for day in dates if day not in files]
    if missing:
        raise FileNotFoundError(f"Missing {len(missing)} local files. First missing: {missing[:5]}")

    rows = []
    for i, day in enumerate(dates, start=1):
        path = files[day]
        mean, std, n_valid = weighted_mean_std(path)

        rows.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "mean_mm_day": mean,
                "std_mm_day": std,
                "n_valid_grid_cells": n_valid,
                "source_file": str(path),
            }
        )

        print(f"{day:%Y-%m-%d}: mean={mean:.4g}, std={std:.4g}, n={n_valid} ({i}/{len(dates)})")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backup(CSV)
    backup(NC)

    df = pd.DataFrame(rows)
    df.to_csv(CSV, index=False)

    ds_out = xr.Dataset(
        data_vars={
            "precip_area_weighted_mean": ("time", df["mean_mm_day"].to_numpy(), {"units": "mm/day"}),
            "precip_area_weighted_std": ("time", df["std_mm_day"].to_numpy(), {"units": "mm/day"}),
            "n_valid_grid_cells": ("time", df["n_valid_grid_cells"].to_numpy()),
        },
        coords={"time": pd.to_datetime(df["date"])},
        attrs={
            "title": "GPCP daily regional precipitation statistics",
            "region_north_west_south_east": str(REGION),
            "masking": "masked missing_value, _FillValue, and values outside valid_range",
            "weighting": "spherical cell-area overlap using lat_bounds and lon_bounds",
        },
    )
    ds_out.to_netcdf(NC)

    print()
    print(f"Wrote {CSV}")
    print(f"Wrote {NC}")


if __name__ == "__main__":
    main()
