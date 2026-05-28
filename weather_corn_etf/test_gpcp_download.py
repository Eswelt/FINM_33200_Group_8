#!/usr/bin/env python3
"""
Download NOAA GPCP daily precipitation and compute two regional time series.

Outputs:
  1. daily source NetCDF files under /glade/work/jiachengye/33200/gpcp/daily/YYYY/
  2. one CSV with area-weighted mean/std
  3. one NetCDF with the same two time series

Default region is [north, west, south, east] = [49, -104, 37, -80].
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import xarray as xr


BASE_URL = "https://noaa-cdr-precip-gpcp-daily-pds.s3.amazonaws.com"
OUTPUT_ROOT = Path("/glade/work/jiachengye/33200/gpcp")
START_DATE = "2011-01-01"
END_DATE = "2025-12-31"
REGION = [49.0, -104.0, 37.0, -80.0]

S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
DATE_RE = re.compile(r"_d(\d{8})_")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download GPCP daily data and compute regional stats.")
    parser.add_argument("--start-date", default=START_DATE)
    parser.add_argument("--end-date", default=END_DATE)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--region", type=float, nargs=4, default=REGION, metavar=("N", "W", "S", "E"))
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--sleep", type=float, default=0.05)
    parser.add_argument("--overwrite-stats", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def date_from_key(key: str) -> dt.date | None:
    match = DATE_RE.search(key)
    if match is None:
        return None
    return dt.datetime.strptime(match.group(1), "%Y%m%d").date()


def list_gpcp_files(year: int, base_url: str, timeout: int) -> dict[dt.date, str]:
    response = requests.get(
        base_url,
        params={"list-type": "2", "prefix": f"data/{year}/"},
        timeout=timeout,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)

    files = {}
    for item in root.findall("s3:Contents", S3_NS):
        key = item.findtext("s3:Key", namespaces=S3_NS)
        if not key:
            continue
        day = date_from_key(key)
        if day is not None:
            files[day] = key
    return files


def requested_dates(start_date: str, end_date: str) -> list[dt.date]:
    start = pd.Timestamp(start_date).date()
    end = pd.Timestamp(end_date).date()
    return [d.date() for d in pd.date_range(start, end, freq="D")]


def local_path(output_root: Path, key: str) -> Path:
    year = key.split("/")[1]
    return output_root / "daily" / year / Path(key).name


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak_{stamp}")
    shutil.copy2(path, backup_path)
    print(f"Backed up existing file: {backup_path}")


def download_file(url: str, path: Path, timeout: int) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with tmp.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    tmp.replace(path)


def lon_intervals(west: float, east: float) -> list[tuple[float, float]]:
    west_360 = west % 360.0
    east_360 = east % 360.0
    if west_360 < east_360:
        return [(west_360, east_360)]
    return [(west_360, 360.0), (0.0, east_360)]


def overlap_width(bounds: np.ndarray, intervals: list[tuple[float, float]]) -> np.ndarray:
    low = np.minimum(bounds[:, 0], bounds[:, 1])
    high = np.maximum(bounds[:, 0], bounds[:, 1])
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
    lat_weight = np.maximum(0.0, np.sin(np.deg2rad(lat_high)) - np.sin(np.deg2rad(lat_low)))

    lon_width = overlap_width(lon_bounds, lon_intervals(west, east))
    weights = lat_weight[:, None] * np.deg2rad(lon_width[None, :])

    return xr.DataArray(
        weights,
        dims=("latitude", "longitude"),
        coords={"latitude": ds["latitude"], "longitude": ds["longitude"]},
    )


def weighted_mean_std(path: Path, region: list[float]) -> tuple[float, float, int]:
    with xr.open_dataset(path) as ds:
        precip = ds["precip"].isel(time=0).astype(float)
        weights = area_weights(ds, region)
        valid = np.isfinite(precip) & (weights > 0)
        weights = weights.where(valid, 0.0)
        total_weight = weights.sum()

        mean = (precip * weights).sum(skipna=True) / total_weight
        variance = (((precip - mean) ** 2) * weights).sum(skipna=True) / total_weight
        n_valid = int(valid.sum().item())
        return float(mean.item()), float(np.sqrt(variance.item())), n_valid


def output_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    north, west, south, east = args.region

    def lon_label(value: float) -> str:
        direction = "east" if value >= 0 else "west"
        return f"{direction}{abs(value):g}"

    tag = f"north{north:g}_{lon_label(west)}_south{south:g}_{lon_label(east)}"
    stem = f"gpcp_daily_area_stats_{args.start_date.replace('-', '')}_{args.end_date.replace('-', '')}_{tag}"
    stats_dir = args.output_root / "stats"
    return stats_dir / f"{stem}.csv", stats_dir / f"{stem}.nc"


def write_outputs(rows: list[dict[str, object]], args: argparse.Namespace) -> None:
    csv_path, nc_path = output_paths(args)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    for path in [csv_path, nc_path]:
        if path.exists() and not args.overwrite_stats:
            raise FileExistsError(f"{path} exists. Use --overwrite-stats to replace it.")
        backup(path)

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    out = xr.Dataset(
        data_vars={
            "precip_area_weighted_mean": ("time", df["mean_mm_day"].to_numpy(), {"units": "mm/day"}),
            "precip_area_weighted_std": ("time", df["std_mm_day"].to_numpy(), {"units": "mm/day"}),
            "n_valid_grid_cells": ("time", df["n_valid_grid_cells"].to_numpy()),
        },
        coords={"time": pd.to_datetime(df["date"])},
        attrs={
            "title": "GPCP daily regional precipitation statistics",
            "source": args.base_url,
            "region_north_west_south_east": str(args.region),
            "weighting": "spherical cell-area overlap using lat_bounds and lon_bounds",
        },
    )
    out.to_netcdf(nc_path)
    print(f"Wrote {csv_path}")
    print(f"Wrote {nc_path}")


def main() -> None:
    args = parse_args()
    dates = requested_dates(args.start_date, args.end_date)
    years = sorted({day.year for day in dates})

    keys_by_date = {}
    for year in years:
        files = list_gpcp_files(year, args.base_url, args.timeout)
        keys_by_date.update(files)
        print(f"Listed {year}: {len(files)} files")

    missing = [day for day in dates if day not in keys_by_date]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} dates from source bucket. First missing: {missing[:5]}")

    csv_path, nc_path = output_paths(args)
    print(f"Dates: {dates[0]} to {dates[-1]} ({len(dates)} days)")
    print(f"Region [north, west, south, east]: {args.region}")
    print(f"Daily files: {args.output_root / 'daily'}")
    print(f"CSV output: {csv_path}")
    print(f"NetCDF output: {nc_path}")
    if args.dry_run:
        return

    rows = []
    for i, day in enumerate(dates, start=1):
        key = keys_by_date[day]
        path = local_path(args.output_root, key)
        url = f"{args.base_url}/{key}"

        download_file(url, path, args.timeout)
        mean, std, n_valid = weighted_mean_std(path, args.region)
        rows.append(
            {
                "date": day.isoformat(),
                "mean_mm_day": mean,
                "std_mm_day": std,
                "n_valid_grid_cells": n_valid,
                "source_file": str(path),
            }
        )
        print(f"{day}: mean={mean:.4g}, std={std:.4g}, n={n_valid} ({i}/{len(dates)})")
        time.sleep(args.sleep)

    write_outputs(rows, args)


if __name__ == "__main__":
    main()

