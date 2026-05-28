#!/usr/bin/env python3
"""
Build yearly valid-time-matched CFSv2 daily 00Z regional-stat NetCDF files.

Input files are daily initialization summaries, for example:
  /glade/work/jiachengye/33200/cfsv2/daily00z/2011/t2m_2011112100.nc

Each input file is indexed by lead_hour. This script reorganizes those values
by valid date:
  valid_date = init_date + lead_time

Output files have fixed shape:
  time = 366
  lead_time = 13

Non-leap years use the first 365 rows for Jan 1 through Dec 31 and leave row
366 as missing. Missing input files and missing values inside input files stay
as NaN in the output.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import importlib.util
import os
from pathlib import Path

import numpy as np
import xarray as xr


DEFAULT_INPUT_ROOT = Path("/glade/work/jiachengye/33200/cfsv2/daily00z")
DEFAULT_OUTPUT_ROOT = Path("/glade/work/jiachengye/33200/cfsv2/validtime_yearly")
VARIABLES = ("t2m", "spfh", "precip")

VARIABLE_ATTRS = {
    "t2m": {
        "units": "K",
        "long_name": "2 m temperature",
    },
    "spfh": {
        "units": "kg kg-1",
        "long_name": "2 m specific humidity",
    },
    "precip": {
        "units": "mm per 6 h",
        "long_name": "total precipitation over 6-hour output interval",
        "note": "Computed in source files as PRATE * 21600 s.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reorganize CFSv2 daily-init summary NetCDF files by valid date into yearly files."
    )
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--start-year", type=int, default=2011)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--init-hour", type=int, default=0, choices=[0, 6, 12, 18])
    parser.add_argument("--lead-days", type=int, default=270)
    parser.add_argument(
        "--lead-schedule",
        choices=["summary", "6hourly"],
        default="summary",
        help="Lead schedule used in the daily initialization files.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing yearly output files.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned work without writing output.")
    parser.add_argument("--quiet", action="store_true", help="Reduce progress output.")
    return parser.parse_args()


def lead_hours(lead_days: int, schedule: str) -> list[int]:
    if schedule == "6hourly":
        return list(range(6, lead_days * 24 + 1, 6))

    week_days = [7, 14, 21, 28]
    month_days = list(range(30, lead_days + 1, 30))
    selected_days = sorted(set(day for day in week_days + month_days if day <= lead_days))
    return [day * 24 for day in selected_days]


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += dt.timedelta(days=1)
    return days


def init_stamp(init_date: dt.date, init_hour: int) -> str:
    return f"{init_date:%Y%m%d}{init_hour:02d}"


def input_path(input_root: Path, variable: str, init_date: dt.date, init_hour: int) -> Path:
    return input_root / f"{init_date.year}" / f"{variable}_{init_stamp(init_date, init_hour)}.nc"


def output_path(output_root: Path, year: int) -> Path:
    return output_root / f"cfsv2_daily00z_validtime_{year}.nc"


def yyyymmdd(value: dt.date) -> np.int32:
    return np.int32(value.year * 10000 + value.month * 100 + value.day)


def real_dates_for_year(year: int) -> list[dt.date]:
    return date_range(dt.date(year, 1, 1), dt.date(year, 12, 31))


def make_year_storage(year: int, leads: list[int]) -> dict[str, object]:
    n_time = 366
    n_lead = len(leads)
    data: dict[str, object] = {
        "valid_date_yyyymmdd": np.zeros(n_time, dtype=np.int32),
        "source_init_date_yyyymmdd": np.zeros((n_time, n_lead), dtype=np.int32),
        "source_file_found": np.zeros((n_time, n_lead), dtype=np.int8),
    }

    for day_index, valid_date in enumerate(real_dates_for_year(year)):
        data["valid_date_yyyymmdd"][day_index] = yyyymmdd(valid_date)
        for lead_index, lead in enumerate(leads):
            init_date = valid_date - dt.timedelta(hours=int(lead))
            data["source_init_date_yyyymmdd"][day_index, lead_index] = yyyymmdd(init_date)

    for variable in VARIABLES:
        data[f"{variable}_mean"] = np.full((n_time, n_lead), np.nan, dtype=np.float32)
        data[f"{variable}_variance"] = np.full((n_time, n_lead), np.nan, dtype=np.float32)
        data[f"{variable}_n_valid_grid_points"] = np.full((n_time, n_lead), np.nan, dtype=np.float32)
    return data


def build_year_storages(start_year: int, end_year: int, leads: list[int]) -> dict[int, dict[str, object]]:
    return {year: make_year_storage(year, leads) for year in range(start_year, end_year + 1)}


def output_location_for_valid_date(
    valid_date: dt.date,
    start_year: int,
    end_year: int,
) -> tuple[int, int] | None:
    if valid_date.year < start_year or valid_date.year > end_year:
        return None
    day_index = valid_date.timetuple().tm_yday - 1
    return valid_date.year, day_index


def read_source_values(path: Path, variable: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    mean_name = f"{variable}_mean"
    variance_name = f"{variable}_variance"
    try:
        with xr.open_dataset(path, decode_times=False) as ds:
            required = ("lead_hour", mean_name, variance_name, "n_valid_grid_points")
            missing = [name for name in required if name not in ds]
            if missing:
                return None
            lead = np.asarray(ds["lead_hour"].values, dtype=np.int32)
            mean = np.asarray(ds[mean_name].values, dtype=np.float32)
            variance = np.asarray(ds[variance_name].values, dtype=np.float32)
            count = np.asarray(ds["n_valid_grid_points"].values, dtype=np.float32)
    except Exception:
        return None
    return lead, mean, variance, count


def scatter_file_to_valid_dates(
    storages: dict[int, dict[str, object]],
    variable: str,
    init_date: dt.date,
    source_path: Path,
    lead_to_index: dict[int, int],
    start_year: int,
    end_year: int,
) -> int:
    values = read_source_values(source_path, variable)
    if values is None:
        return 0

    source_leads, mean_values, variance_values, count_values = values
    filled = 0
    for source_index, lead in enumerate(source_leads):
        lead_int = int(lead)
        if lead_int not in lead_to_index:
            continue

        location = output_location_for_valid_date(
            init_date + dt.timedelta(hours=lead_int),
            start_year,
            end_year,
        )
        if location is None:
            continue

        year, day_index = location
        lead_index = lead_to_index[lead_int]
        storage = storages[year]
        storage["source_file_found"][day_index, lead_index] = 1

        count = count_values[source_index]
        if not np.isfinite(count) or count <= 0:
            continue

        mean = mean_values[source_index]
        variance = variance_values[source_index]
        if np.isfinite(mean):
            storage[f"{variable}_mean"][day_index, lead_index] = mean
        if np.isfinite(variance):
            storage[f"{variable}_variance"][day_index, lead_index] = variance
        storage[f"{variable}_n_valid_grid_points"][day_index, lead_index] = count
        filled += 1
    return filled


def init_dates_to_scan(start_year: int, end_year: int, leads: list[int]) -> list[dt.date]:
    max_lead_days = max(leads) // 24
    start = dt.date(start_year, 1, 1) - dt.timedelta(days=max_lead_days)
    end = dt.date(end_year, 12, 31) - dt.timedelta(days=min(leads) // 24)
    return date_range(start, end)


def populate_storages(
    storages: dict[int, dict[str, object]],
    input_root: Path,
    start_year: int,
    end_year: int,
    init_hour: int,
    leads: list[int],
    quiet: bool,
) -> dict[str, int]:
    lead_to_index = {lead: index for index, lead in enumerate(leads)}
    init_dates = init_dates_to_scan(start_year, end_year, leads)
    counts = {
        "expected_source_files": 0,
        "existing_source_files": 0,
        "filled_values": 0,
    }

    for index, init_date in enumerate(init_dates, start=1):
        if not quiet and (index == 1 or index % 250 == 0 or index == len(init_dates)):
            print(f"Scanning init {index}/{len(init_dates)}: {init_date}", flush=True)
        for variable in VARIABLES:
            counts["expected_source_files"] += 1
            path = input_path(input_root, variable, init_date, init_hour)
            if not path.exists():
                continue
            counts["existing_source_files"] += 1
            counts["filled_values"] += scatter_file_to_valid_dates(
                storages,
                variable,
                init_date,
                path,
                lead_to_index,
                start_year,
                end_year,
            )
    return counts


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
        if np.issubdtype(data_array.dtype, np.floating):
            encoding[name] = {"dtype": "float32", "_FillValue": np.float32(np.nan)}
        elif np.issubdtype(data_array.dtype, np.integer):
            encoding[name] = {"dtype": str(data_array.dtype)}
        if engine in {"netcdf4", "h5netcdf"} and name in encoding:
            encoding[name].update({"zlib": True, "complevel": 4})
    return encoding, engine


def make_year_dataset(year: int, storage: dict[str, object], leads: list[int]) -> xr.Dataset:
    lead_array = np.asarray(leads, dtype=np.int32)
    lead_day = (lead_array // 24).astype(np.int32)
    time_index = np.arange(1, 367, dtype=np.int32)
    is_leap = calendar.isleap(year)

    data_vars: dict[str, object] = {
        "valid_date_yyyymmdd": (
            "time",
            storage["valid_date_yyyymmdd"],
            {
                "long_name": "valid date encoded as YYYYMMDD; 0 marks padded non-leap row",
            },
        ),
        "source_init_date_yyyymmdd": (
            ("time", "lead_time"),
            storage["source_init_date_yyyymmdd"],
            {
                "long_name": "expected source initialization date encoded as YYYYMMDD",
                "description": "For each valid date and lead_time, source_init_date = valid_date - lead_time.",
            },
        ),
        "source_file_found": (
            ("time", "lead_time"),
            storage["source_file_found"],
            {
                "long_name": "whether at least one source variable file existed for this valid date and lead_time",
                "values": "0 = no source file found, 1 = at least one source file found",
            },
        ),
    }

    for variable in VARIABLES:
        attrs = VARIABLE_ATTRS[variable]
        data_vars[f"{variable}_mean"] = (
            ("time", "lead_time"),
            storage[f"{variable}_mean"],
            {
                "long_name": f"valid-time matched regional area-weighted mean of {attrs['long_name']}",
                "units": attrs["units"],
            },
        )
        data_vars[f"{variable}_variance"] = (
            ("time", "lead_time"),
            storage[f"{variable}_variance"],
            {
                "long_name": f"valid-time matched regional area-weighted spatial variance of {attrs['long_name']}",
                "units": f"({attrs['units']})^2",
            },
        )
        data_vars[f"{variable}_n_valid_grid_points"] = (
            ("time", "lead_time"),
            storage[f"{variable}_n_valid_grid_points"],
            {
                "long_name": f"number of finite grid points used for {variable} regional statistics",
                "description": "NaN means the source file, lead, or source value was missing.",
            },
        )
        if "note" in attrs:
            data_vars[f"{variable}_mean"][2]["note"] = attrs["note"]
            data_vars[f"{variable}_variance"][2]["note"] = attrs["note"]

    return xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": (
                "time",
                time_index,
                {
                    "long_name": "day-of-year slot",
                    "description": "1-365/366 are calendar days; non-leap years use slot 366 as all-missing padding.",
                },
            ),
            "lead_time": (
                "lead_time",
                lead_array,
                {
                    "long_name": "forecast lead time",
                    "unit_label": "hours",
                    "description": "forecast lead time in hours since initialization",
                },
            ),
            "lead_day": (
                "lead_time",
                lead_day,
                {
                    "long_name": "forecast lead time in days",
                    "unit_label": "days",
                    "description": "forecast lead time in days since initialization",
                },
            ),
        },
        attrs={
            "title": "CFSv2 daily 00Z regional forecast statistics matched by valid date",
            "source_dataset": "NOAA CFSv2 operational 9-month forecast, 6-hourly flux",
            "source_layout": "daily initialization NetCDF files with regional statistics by lead_hour",
            "year": year,
            "is_leap_year": int(is_leap),
            "time_dimension_policy": "All yearly outputs use 366 time slots. Non-leap years leave slot 366 missing.",
            "missing_policy": "Missing source files, missing leads, and missing source values are stored as NaN.",
        },
    )


def write_year_dataset(ds: xr.Dataset, path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        print(f"Skip existing output: {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    encoding, engine = netcdf_write_options(ds)
    ds.to_netcdf(tmp_path, encoding=encoding, engine=engine)
    tmp_path.replace(path)
    print(f"Wrote {path}")


def main() -> None:
    args = parse_args()
    if args.start_year > args.end_year:
        raise ValueError("--start-year must be <= --end-year")
    if args.lead_days <= 0:
        raise ValueError("--lead-days must be positive")
    if not args.input_root.exists():
        raise FileNotFoundError(f"Input root does not exist: {args.input_root}")

    leads = lead_hours(args.lead_days, args.lead_schedule)
    print(f"Input root: {args.input_root}")
    print(f"Output root: {args.output_root}")
    print(f"Years: {args.start_year}-{args.end_year}")
    print(f"Lead hours: {', '.join(str(lead) for lead in leads)}")
    print("Output shape per year: time=366, lead_time={}".format(len(leads)))

    output_paths = [output_path(args.output_root, year) for year in range(args.start_year, args.end_year + 1)]
    if args.dry_run:
        print("Planned output files:")
        for path in output_paths:
            print(f"  {path}")
        return

    storages = build_year_storages(args.start_year, args.end_year, leads)
    counts = populate_storages(
        storages,
        args.input_root,
        args.start_year,
        args.end_year,
        args.init_hour,
        leads,
        args.quiet,
    )
    print(
        "Source scan complete: "
        f"existing_source_files={counts['existing_source_files']}; "
        f"expected_source_files={counts['expected_source_files']}; "
        f"filled_values={counts['filled_values']}"
    )

    for year in range(args.start_year, args.end_year + 1):
        ds = make_year_dataset(year, storages[year], leads)
        write_year_dataset(ds, output_path(args.output_root, year), args.overwrite)
        ds.close()


if __name__ == "__main__":
    main()
