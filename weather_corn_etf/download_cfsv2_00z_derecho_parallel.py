#!/usr/bin/env python3
"""
Download CFSv2 operational 00Z forecasts in parallel and build daily-init
regional statistic NetCDF files.

Default target:
  - NOAA CFSv2 operational 9-month forecast, 6-hourly flux files
  - Daily 00Z initializations
  - Sparse lead times by default:
      week 1, 2, 3, 4 endpoints plus 30-day month 1 through month 9 endpoints
  - Region lon [-104, -80], lat [37, 49]
  - Variables:
      t2m    = TMP at 2 m above ground, K
      spfh   = SPFH at 2 m above ground, kg kg-1
      precip = PRATE at surface converted to mm per 6 h

The script writes one NetCDF per variable per initialization:
  /glade/work/jiachengye/33200/cfsv2/daily00z/2014/t2m_2014010100.nc
  /glade/work/jiachengye/33200/cfsv2/daily00z/2014/spfh_2014010100.nc
  /glade/work/jiachengye/33200/cfsv2/daily00z/2014/precip_2014010100.nc

It downloads one GRIB2 file at a time, reads it directly with cfgrib/eccodes,
crops the requested region in xarray, computes regional mean and variance,
stores only those statistics for one initialization, and removes only temporary
files created by this script.

Parallelism is across initialization dates. Each worker still processes one
initialization sequentially across lead times.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import datetime as dt
import importlib.util
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
import warnings
from pathlib import Path

import numpy as np
import xarray as xr


BASE_URL = (
    "https://www.ncei.noaa.gov/data/climate-forecast-system/access/"
    "operational-9-month-forecast/6-hourly-flux"
)

DEFAULT_OUTPUT_ROOT = Path("/glade/work/jiachengye/33200/cfsv2/daily00z")

VARIABLES = {
    "t2m": {
        "cfgrib_exact_var_name": "t2m",
        "source_abbrev": "TMP",
        "type_of_level": "heightAboveGround",
        "level_coord_candidates": ("heightAboveGround",),
        "level_value": 2.0,
        "units": "K",
        "long_name": "2 m temperature",
    },
    "spfh": {
        "cfgrib_exact_var_name": "sh2",
        "source_abbrev": "SPFH",
        "type_of_level": "heightAboveGround",
        "level_coord_candidates": ("heightAboveGround",),
        "level_value": 2.0,
        "units": "kg kg-1",
        "long_name": "2 m specific humidity",
    },
    "precip": {
        "cfgrib_exact_var_name": "prate",
        "source_abbrev": "PRATE",
        "type_of_level": "surface",
        "level_coord_candidates": ("surface",),
        "level_value": 0.0,
        "units": "mm per 6 h",
        "long_name": "total precipitation over 6-hour output interval",
        "scale": 21600.0,
        "source_units": "kg m-2 s-1",
        "note": "Computed as PRATE * 21600 s. For water, 1 kg m-2 equals 1 mm.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download daily 00Z CFSv2 operational forecasts and write regional stats per variable/init."
    )
    parser.add_argument("--start-date", default="2011-04-01", help="First initialization date, YYYY-MM-DD.")
    parser.add_argument(
        "--end-date",
        default=None,
        help="Last initialization date, YYYY-MM-DD. Default is min(yesterday UTC, 2026-12-31).",
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--lon-min", type=float, default=-104.0)
    parser.add_argument("--lon-max", type=float, default=-80.0)
    parser.add_argument("--lat-min", type=float, default=37.0)
    parser.add_argument("--lat-max", type=float, default=49.0)
    parser.add_argument("--lead-days", type=int, default=270, help="Forecast length in days. Default is 270.")
    parser.add_argument(
        "--lead-schedule",
        choices=["summary", "6hourly"],
        default="summary",
        help=(
            "Lead-time schedule. 'summary' selects week 1-4 endpoints plus 30-day month endpoints; "
            "'6hourly' selects every 6-hour output through --lead-days."
        ),
    )
    parser.add_argument("--init-hour", type=int, default=0, choices=[0, 6, 12, 18])
    parser.add_argument("--download-timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--sleep", type=float, default=0.1, help="Seconds to sleep between downloads.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite daily-init output NetCDF files if present.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary GRIB2/NetCDF files.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned work without downloading.")
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of initialization dates to process in parallel. Default is 10.",
    )
    parser.add_argument(
        "--redownload-last-complete-init",
        action="store_true",
        help=(
            "Before processing, find the last initialization in the selected date range "
            "with all variable outputs present, delete those outputs, and recompute it. "
            "This helps resume safely after a killed job that may have written incomplete statistics."
        ),
    )
    return parser.parse_args()


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += dt.timedelta(days=1)
    return days


def parse_date(value: str) -> dt.date:
    return dt.datetime.strptime(value, "%Y-%m-%d").date()


def lead_hours(args: argparse.Namespace) -> list[int]:
    if args.lead_schedule == "6hourly":
        return list(range(6, args.lead_days * 24 + 1, 6))

    week_days = [7, 14, 21, 28]
    month_days = list(range(30, args.lead_days + 1, 30))
    selected_days = sorted(set(day for day in week_days + month_days if day <= args.lead_days))
    return [day * 24 for day in selected_days]


def describe_leads(leads: list[int]) -> str:
    return ", ".join(f"+{lead // 24}d" if lead % 24 == 0 else f"+{lead}h" for lead in leads)


def full_lead_hours(lead_days: int) -> list[int]:
    return list(range(6, lead_days * 24 + 1, 6))


def url_for(base_url: str, init: dt.datetime, lead_hour: int) -> str:
    valid = init + dt.timedelta(hours=lead_hour)
    y = init.strftime("%Y")
    ym = init.strftime("%Y%m")
    ymd = init.strftime("%Y%m%d")
    init_stamp = init.strftime("%Y%m%d%H")
    valid_stamp = valid.strftime("%Y%m%d%H")
    name = f"flxf{valid_stamp}.01.{init_stamp}.grb2"
    return f"{base_url}/{y}/{ym}/{ymd}/{init_stamp}/{name}"


def require_cfgrib() -> None:
    if importlib.util.find_spec("cfgrib") is None:
        raise RuntimeError(
            "cfgrib was not found. Install it on the remote server, for example: "
            "conda install -c conda-forge cfgrib eccodes"
        )


def download_file(url: str, target: Path, timeout: int, retries: int) -> bool:
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                if response.status != 200:
                    return False
                with target.open("wb") as out:
                    shutil.copyfileobj(response, out)
            return True
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return False
            if attempt == retries:
                print(f"Download failed after {retries} attempts: {url} ({exc})", file=sys.stderr)
                return False
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == retries:
                print(f"Download failed after {retries} attempts: {url} ({exc})", file=sys.stderr)
                return False
        time.sleep(min(2 ** attempt, 30))
    return False


def coord_name(ds: xr.Dataset | xr.DataArray, candidates: tuple[str, ...], standard_name: str) -> str:
    for name in candidates:
        if name in ds.coords:
            return name
    for name, coord in ds.coords.items():
        if coord.attrs.get("standard_name") == standard_name:
            return name
    raise KeyError(f"Could not find {standard_name} coordinate in {list(ds.coords)}")


def scalar_coord_value(da: xr.DataArray, coord_candidates: tuple[str, ...]) -> float | None:
    for coord_name_candidate in coord_candidates:
        if coord_name_candidate not in da.coords:
            continue
        values = np.asarray(da[coord_name_candidate].values)
        if values.size == 1:
            return float(values.reshape(-1)[0])
    return None


def cfgrib_var_matches(name: str, da: xr.DataArray, spec: dict[str, object]) -> bool:
    if name.lower() != spec["cfgrib_exact_var_name"]:
        return False

    expected_type = spec.get("type_of_level")
    if expected_type is not None:
        actual_type = da.attrs.get("GRIB_typeOfLevel")
        if actual_type is not None and actual_type != expected_type:
            return False

    expected_level = spec.get("level_value")
    if expected_level is not None:
        actual_level = scalar_coord_value(da, spec["level_coord_candidates"])
        if actual_level is not None and not np.isclose(actual_level, float(expected_level)):
            return False

    return True


def find_cfgrib_data_array(datasets: list[xr.Dataset], out_name: str) -> xr.DataArray:
    spec = VARIABLES[out_name]
    matches: list[tuple[int, str, xr.DataArray]] = []
    for dataset_index, ds in enumerate(datasets):
        for var_name, da in ds.data_vars.items():
            if cfgrib_var_matches(var_name, da, spec):
                matches.append((dataset_index, var_name, da))

    if len(matches) == 1:
        return matches[0][2]

    if len(matches) > 1:
        detail = ", ".join(f"dataset{idx}:{name}" for idx, name, _ in matches)
        raise KeyError(f"Multiple cfgrib matches for {out_name}: {detail}")

    available = []
    for dataset_index, ds in enumerate(datasets):
        for var_name, da in ds.data_vars.items():
            available.append(
                f"dataset{dataset_index}:{var_name}:"
                f"{da.attrs.get('GRIB_shortName', '')}:"
                f"{da.attrs.get('GRIB_typeOfLevel', '')}:"
                f"{da.attrs.get('GRIB_name', '')}"
            )
    raise KeyError(f"No cfgrib match for {out_name}. Available vars: {available}")


def subset_data_array(
    da: xr.DataArray,
    lon_min: float,
    lon_max: float,
    lat_min: float,
    lat_max: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    da = da.squeeze(drop=True)
    lat_name = coord_name(da, ("lat", "latitude"), "latitude")
    lon_name = coord_name(da, ("lon", "longitude"), "longitude")

    lat_values = np.asarray(da[lat_name].values)
    lon_values = np.asarray(da[lon_name].values)
    if lat_values.ndim != 1 or lon_values.ndim != 1:
        raise ValueError("Expected 1-D latitude and longitude coordinates from cfgrib.")

    lat_mask = (lat_values >= min(lat_min, lat_max)) & (lat_values <= max(lat_min, lat_max))
    if lon_values.max() > 180.0:
        west = lon_min + 360.0 if lon_min < 0.0 else lon_min
        east = lon_max + 360.0 if lon_max < 0.0 else lon_max
    else:
        west = lon_min
        east = lon_max
    if west <= east:
        lon_mask = (lon_values >= west) & (lon_values <= east)
    else:
        lon_mask = (lon_values >= west) | (lon_values <= east)

    lat_indices = np.where(lat_mask)[0]
    lon_indices = np.where(lon_mask)[0]
    if len(lat_indices) == 0 or len(lon_indices) == 0:
        raise ValueError(
            f"Subset is empty for lon [{lon_min}, {lon_max}], lat [{lat_min}, {lat_max}]."
        )

    da = da.isel({lat_name: lat_indices, lon_name: lon_indices})
    if lat_name in da.dims and lon_name in da.dims:
        da = da.transpose(lat_name, lon_name)

    lat = np.asarray(da[lat_name].values, dtype=np.float32)
    lon = np.asarray(da[lon_name].values, dtype=np.float32)
    lon = np.where(lon > 180.0, lon - 360.0, lon).astype(np.float32)
    values = np.asarray(da.values, dtype=np.float32)
    return values, lat, lon


def read_grib_values(
    grib_path: Path,
    lon_min: float,
    lon_max: float,
    lat_min: float,
    lat_max: float,
) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    import cfgrib

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="In a future version of xarray the default value for compat will change",
            category=FutureWarning,
        )
        datasets = cfgrib.open_datasets(
            str(grib_path),
            backend_kwargs={
                "indexpath": "",
                "errors": "ignore",
            },
        )
    try:
        values: dict[str, np.ndarray] = {}
        reference_lat: np.ndarray | None = None
        reference_lon: np.ndarray | None = None
        for out_name, spec in VARIABLES.items():
            da = find_cfgrib_data_array(datasets, out_name)
            arr, lat, lon = subset_data_array(da, lon_min, lon_max, lat_min, lat_max)
            scale = float(spec.get("scale", 1.0))
            if scale != 1.0:
                arr = arr * scale
            values[out_name] = arr
            if reference_lat is None:
                reference_lat = lat
                reference_lon = lon
            elif not (np.array_equal(reference_lat, lat) and np.array_equal(reference_lon, lon)):
                raise ValueError(f"{out_name} grid does not match the first selected variable grid.")
        if reference_lat is None or reference_lon is None:
            raise RuntimeError("No variables were read from GRIB2.")
        return values, reference_lat, reference_lon
    finally:
        for ds in datasets:
            ds.close()


def regional_stats(
    field: np.ndarray,
    lat: np.ndarray,
) -> tuple[np.float32, np.float32, np.int32]:
    values = np.asarray(field, dtype=np.float64)
    valid = np.isfinite(values)
    count = np.int32(valid.sum())
    if count == 0:
        return np.float32(np.nan), np.float32(np.nan), count

    if lat.ndim == 1 and values.ndim >= 2 and values.shape[-2] == lat.size:
        weights = np.cos(np.deg2rad(lat.astype(np.float64)))[:, None]
    elif lat.shape == values.shape:
        weights = np.cos(np.deg2rad(lat.astype(np.float64)))
    else:
        weights = np.ones_like(values, dtype=np.float64)

    weights = np.broadcast_to(weights, values.shape)
    weights = np.where(valid, weights, 0.0)
    total_weight = weights.sum()
    if total_weight <= 0.0:
        return np.float32(np.nan), np.float32(np.nan), count

    mean = np.sum(np.where(valid, values, 0.0) * weights) / total_weight
    variance = np.sum(np.where(valid, (values - mean) ** 2, 0.0) * weights) / total_weight
    return np.float32(mean), np.float32(variance), count


def make_output_dataset(
    var_name: str,
    stats: dict[str, np.ndarray],
    init_time: dt.datetime,
    leads: list[int],
    lat: np.ndarray,
    lon: np.ndarray,
) -> xr.Dataset:
    spec = VARIABLES[var_name]
    init64 = np.datetime64(init_time, "ns")
    lead = np.array(leads, dtype=np.int32)
    valid_time = init64 + lead.astype("timedelta64[h]")

    ds = xr.Dataset(
        data_vars={
            f"{var_name}_mean": (
                "lead_hour",
                stats["mean"],
                {
                    "long_name": f"regional area-weighted mean of {spec['long_name']}",
                    "units": spec["units"],
                    "source_parameter": spec["source_abbrev"],
                    "source_dataset": "NOAA CFSv2 operational 9-month forecast, 6-hourly flux",
                    "weighting": "cos(latitude) weights over the cropped native grid",
                },
            ),
            f"{var_name}_variance": (
                "lead_hour",
                stats["variance"],
                {
                    "long_name": f"regional area-weighted spatial variance of {spec['long_name']}",
                    "units": f"({spec['units']})^2",
                    "source_parameter": spec["source_abbrev"],
                    "source_dataset": "NOAA CFSv2 operational 9-month forecast, 6-hourly flux",
                    "weighting": "cos(latitude) weights over the cropped native grid",
                    "variance_definition": "population weighted variance over space for each lead time",
                },
            ),
            "n_valid_grid_points": (
                "lead_hour",
                stats["count"],
                {"long_name": "number of finite grid points used in regional statistics"},
            ),
            "valid_time": ("lead_hour", valid_time),
        },
        coords={
            "init_time": init64,
            "lead_hour": ("lead_hour", lead, {"units": "hours since initialization"}),
            "lat": ("lat", lat, {"units": "degrees_north", "description": "cropped native-grid latitude values"}),
            "lon": ("lon", lon, {"units": "degrees_east", "description": "cropped native-grid longitude values"}),
        },
        attrs={
            "title": "Regional CFSv2 operational 00Z forecast summary statistics",
            "institution": "NOAA/NCEP; subset generated by download_cfsv2_00z.py",
            "summary_region": "lon [-104, -80], lat [37, 49] by default; see coordinate values for actual native grid points",
            "history": f"Created {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}",
        },
    )
    for stat_name in (f"{var_name}_mean", f"{var_name}_variance"):
        if "source_units" in spec:
            ds[stat_name].attrs["source_units"] = spec["source_units"]
        if "note" in spec:
            ds[stat_name].attrs["note"] = spec["note"]
    return ds


def netcdf_write_options(ds: xr.Dataset) -> tuple[dict[str, dict[str, object]], str | None]:
    if importlib.util.find_spec("netCDF4") is not None:
        engine = "netcdf4"
    elif importlib.util.find_spec("h5netcdf") is not None:
        engine = "h5netcdf"
    elif importlib.util.find_spec("scipy") is not None:
        engine = "scipy"
    else:
        engine = None

    encoding: dict[str, dict[str, object]] = {}
    for name, data_array in ds.data_vars.items():
        if name == "valid_time":
            continue
        if np.issubdtype(data_array.dtype, np.floating):
            encoding[name] = {"dtype": "float32", "_FillValue": np.float32(np.nan)}
        elif np.issubdtype(data_array.dtype, np.integer):
            encoding[name] = {"dtype": "int32"}
        else:
            continue
        if engine in {"netcdf4", "h5netcdf"} and name in encoding:
            encoding[name].update({"zlib": True, "complevel": 4})
    return encoding, engine


def init_stamp(init_time: dt.datetime) -> str:
    return init_time.strftime("%Y%m%d%H")


def output_paths(year_dir: Path, init_time: dt.datetime) -> dict[str, Path]:
    stamp = init_stamp(init_time)
    return {name: year_dir / f"{name}_{stamp}.nc" for name in VARIABLES}


def init_is_complete(year_dir: Path, init_time: dt.datetime) -> bool:
    return all(path.exists() for path in output_paths(year_dir, init_time).values())


def find_last_complete_init(
    init_times: list[dt.datetime],
    output_root: Path,
) -> dt.datetime | None:
    last_complete: dt.datetime | None = None
    for init_time in init_times:
        year_dir = output_root / str(init_time.year)
        if init_is_complete(year_dir, init_time):
            last_complete = init_time
    return last_complete


def redownload_last_complete_init(
    init_times: list[dt.datetime],
    args: argparse.Namespace,
) -> None:
    last_complete = find_last_complete_init(init_times, args.output_root)
    if last_complete is None:
        print("No complete initialization found to redownload.")
        return

    year_dir = args.output_root / str(last_complete.year)
    paths = output_paths(year_dir, last_complete)
    print(f"Last complete initialization in selected range: {last_complete:%Y-%m-%d %HZ}")
    for path in paths.values():
        if args.dry_run:
            print(f"Dry run: would delete {path}")
        elif path.exists():
            path.unlink()
            print(f"Deleted for redownload: {path}")


def write_init_files(
    year_dir: Path,
    stats_by_var: dict[str, dict[str, np.ndarray]],
    init_time: dt.datetime,
    leads: list[int],
    lat: np.ndarray,
    lon: np.ndarray,
    overwrite: bool,
) -> None:
    year_dir.mkdir(parents=True, exist_ok=True)
    paths = output_paths(year_dir, init_time)
    for name, stats in stats_by_var.items():
        out_path = paths[name]
        if out_path.exists() and not overwrite:
            print(f"Skip existing output: {out_path}")
            continue
        tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
        ds = make_output_dataset(name, stats, init_time, leads, lat, lon)
        encoding, engine = netcdf_write_options(ds)
        ds.to_netcdf(tmp_path, encoding=encoding, engine=engine)
        tmp_path.replace(out_path)
        print(f"Wrote {out_path}")


def process_init(
    init_time: dt.datetime,
    leads: list[int],
    year_dir: Path,
    args: argparse.Namespace,
) -> tuple[int, int, bool]:
    if init_is_complete(year_dir, init_time) and not args.overwrite:
        print(f"Init {init_time:%Y-%m-%d %HZ}: all variable files exist; skipping.")
        return 0, 0, True

    stats_by_var: dict[str, dict[str, np.ndarray]] | None = None
    lat: np.ndarray | None = None
    lon: np.ndarray | None = None
    missing = 0
    extracted = 0

    work_parent = year_dir / "_tmp_download_cfsv2_00z"
    work_parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{init_stamp(init_time)}_", dir=work_parent))

    try:
        for j, lead in enumerate(leads):
            url = url_for(args.base_url, init_time, lead)
            grib_path = temp_dir / "input.grb2"

            for path in (grib_path,):
                if path.exists():
                    path.unlink()

            ok = download_file(url, grib_path, args.download_timeout, args.retries)
            if not ok:
                missing += 1
                valid_time = init_time + dt.timedelta(hours=lead)
                print(
                    f"Init {init_time:%Y-%m-%d %HZ}: lead {j + 1}/{len(leads)} "
                    f"+{lead}h valid {valid_time:%Y-%m-%d %HZ}: missing",
                    flush=True,
                )
                continue

            try:
                values, this_lat, this_lon = read_grib_values(
                    grib_path,
                    args.lon_min,
                    args.lon_max,
                    args.lat_min,
                    args.lat_max,
                )
            except Exception as exc:
                missing += 1
                print(f"Failed to extract {url}: {exc}", file=sys.stderr)
                valid_time = init_time + dt.timedelta(hours=lead)
                print(
                    f"Init {init_time:%Y-%m-%d %HZ}: lead {j + 1}/{len(leads)} "
                    f"+{lead}h valid {valid_time:%Y-%m-%d %HZ}: failed",
                    flush=True,
                )
                continue

            if stats_by_var is None:
                lat = this_lat
                lon = this_lon
                stats_by_var = {
                    name: {
                        "mean": np.full(len(leads), np.nan, dtype=np.float32),
                        "variance": np.full(len(leads), np.nan, dtype=np.float32),
                        "count": np.zeros(len(leads), dtype=np.int32),
                    }
                    for name in VARIABLES
                }
                print(f"Init {init_time:%Y-%m-%d %HZ}: subset grid {len(lat)} lat x {len(lon)} lon")

            for name in VARIABLES:
                mean, variance, count = regional_stats(values[name], this_lat)
                stats_by_var[name]["mean"][j] = mean
                stats_by_var[name]["variance"][j] = variance
                stats_by_var[name]["count"][j] = count
            extracted += 1
            valid_time = init_time + dt.timedelta(hours=lead)
            print(
                f"Init {init_time:%Y-%m-%d %HZ}: lead {j + 1}/{len(leads)} "
                f"+{lead}h valid {valid_time:%Y-%m-%d %HZ}: extracted",
                flush=True,
            )

            if args.sleep > 0:
                time.sleep(args.sleep)

        if stats_by_var is None or lat is None or lon is None:
            print(f"Init {init_time:%Y-%m-%d %HZ}: no data extracted; skipped output.", file=sys.stderr)
            return extracted, missing, False

        write_init_files(year_dir, stats_by_var, init_time, leads, lat, lon, args.overwrite)
        return extracted, missing, False
    finally:
        if args.keep_temp:
            print(f"Kept temporary directory: {temp_dir}")
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)


def process_init_worker(
    init_time: dt.datetime,
    leads: list[int],
    year_dir: Path,
    args: argparse.Namespace,
) -> tuple[dt.datetime, int, int, bool]:
    extracted, missing, skipped = process_init(init_time, leads, year_dir, args)
    return init_time, extracted, missing, skipped


def process_year(year: int, init_dates: list[dt.date], args: argparse.Namespace) -> None:
    year_dir = args.output_root / str(year)
    leads = lead_hours(args)
    init_times = [dt.datetime.combine(day, dt.time(args.init_hour)) for day in init_dates]
    print(f"Year {year}: {len(init_times)} initializations, {len(leads)} lead times.")
    print(f"Selected leads: {describe_leads(leads)}")

    if args.dry_run:
        if init_times:
            print(f"First URL: {url_for(args.base_url, init_times[0], leads[0])}")
            print(f"Last URL:  {url_for(args.base_url, init_times[-1], leads[-1])}")
            first_paths = output_paths(year_dir, init_times[0])
            print("First init output files:")
            for path in first_paths.values():
                print(f"  {path}")
        return

    require_cfgrib()
    if args.overwrite:
        work_init_times = init_times
        pre_skipped = 0
    else:
        work_init_times = [init for init in init_times if not init_is_complete(year_dir, init)]
        pre_skipped = len(init_times) - len(work_init_times)

    print(
        f"Year {year}: {pre_skipped} complete initializations already exist; "
        f"{len(work_init_times)} initializations need work."
    )

    total_extracted = 0
    total_missing = 0
    total_skipped = pre_skipped
    total_failed = 0

    if not work_init_times:
        print(f"Year {year}: no incomplete initializations to process.")
    elif args.workers == 1:
        for i, init in enumerate(work_init_times):
            extracted, missing, skipped = process_init(init, leads, year_dir, args)
            total_extracted += extracted
            total_missing += missing
            total_skipped += int(skipped)
            print(
                f"Year {year}: finished init {init:%Y-%m-%d %HZ} "
                f"({i + 1}/{len(work_init_times)}); extracted={extracted}; "
                f"missing={missing}; skipped={skipped}"
            )
    else:
        max_workers = min(args.workers, len(work_init_times))
        print(f"Year {year}: processing with {max_workers} parallel workers.")
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_init = {
                executor.submit(process_init_worker, init, leads, year_dir, args): init
                for init in work_init_times
            }
            for i, future in enumerate(as_completed(future_to_init), start=1):
                init = future_to_init[future]
                try:
                    finished_init, extracted, missing, skipped = future.result()
                except Exception as exc:
                    total_failed += 1
                    print(f"Year {year}: init {init:%Y-%m-%d %HZ} failed: {exc}", file=sys.stderr)
                    continue

                total_extracted += extracted
                total_missing += missing
                total_skipped += int(skipped)
                print(
                    f"Year {year}: finished init {finished_init:%Y-%m-%d %HZ} "
                    f"({i}/{len(work_init_times)}); extracted={extracted}; "
                    f"missing={missing}; skipped={skipped}"
                )

    print(
        f"Year {year}: done. Lead files extracted={total_extracted}; "
        f"missing/skipped leads={total_missing}; skipped complete inits={total_skipped}; "
        f"failed inits={total_failed}"
    )
    if total_failed:
        raise RuntimeError(f"Year {year}: {total_failed} initializations failed.")


def main() -> None:
    args = parse_args()
    start = parse_date(args.start_date)
    if args.end_date is None:
        yesterday = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)
        end = min(yesterday, dt.date(2026, 12, 31))
    else:
        end = parse_date(args.end_date)
    if end < start:
        raise ValueError("--end-date must be >= --start-date")
    if args.lead_days <= 0:
        raise ValueError("--lead-days must be positive")
    if args.workers <= 0:
        raise ValueError("--workers must be positive")

    all_dates = date_range(start, end)
    all_init_times = [dt.datetime.combine(day, dt.time(args.init_hour)) for day in all_dates]
    years = sorted({day.year for day in all_dates})
    print(f"Output root: {args.output_root}")
    print(f"Years: {years[0]}-{years[-1]}")
    print(f"Region: lon [{args.lon_min}, {args.lon_max}], lat [{args.lat_min}, {args.lat_max}]")
    print(f"Lead schedule: {args.lead_schedule}; max lead +{args.lead_days * 24} h")
    print(f"Parallel workers: {args.workers}")

    if args.redownload_last_complete_init:
        redownload_last_complete_init(all_init_times, args)

    for year in years:
        init_dates = [day for day in all_dates if day.year == year]
        process_year(year, init_dates, args)


if __name__ == "__main__":
    main()

