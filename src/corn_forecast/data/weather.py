from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from corn_forecast.storage import read_table, write_table


ERA5_DATASET = "derived-era5-single-levels-daily-statistics"
CFSV2_BASE_URL = "https://www.ncei.noaa.gov/data/climate-forecast-system/access/operational-9-month-forecast"
GEFSV12_BASE_URL = "https://noaa-gefs-retrospective.s3.amazonaws.com/GEFSv12/reforecast"


def build_era5_daily_request(
    year: int,
    month: int,
    variables: Optional[Sequence[str]] = None,
    bbox: Tuple[float, float, float, float] = (49.0, -104.0, 37.0, -80.0),
) -> dict:
    """Return the CDS request body for Corn Belt ERA5 daily statistics."""
    if variables is None:
        variables = ("2m_temperature", "total_precipitation")
    days = pd.Period(f"{year}-{month:02d}").days_in_month
    return {
        "dataset": ERA5_DATASET,
        "request": {
            "product_type": "reanalysis",
            "variable": list(variables),
            "year": f"{year}",
            "month": f"{month:02d}",
            "day": [f"{day:02d}" for day in range(1, days + 1)],
            "daily_statistic": "daily_mean",
            "time_zone": "utc+00:00",
            "frequency": "1_hourly",
            "area": list(bbox),
        },
    }


def build_cfsv2_url(
    init_time: datetime,
    forecast_hour: int = 168,
    member: str = "01",
    product: str = "6-hourly-by-pressure",
) -> str:
    """Build a CFSv2 operational forecast GRIB2 URL for a chosen lead time."""
    init_stamp = init_time.strftime("%Y%m%d%H")
    valid_stamp = (init_time + timedelta(hours=forecast_hour)).strftime("%Y%m%d%H")
    return (
        f"{CFSV2_BASE_URL}/{product}/"
        f"{init_time:%Y}/{init_time:%Y%m}/{init_time:%Y%m%d}/{init_stamp}/"
        f"pgbf{valid_stamp}.{member}.{init_stamp}.grb2"
    )


def build_gefs_v12_url(
    init_time: datetime,
    variable_level: str = "tmp_2m",
    member: str = "c00",
    day_bucket: str = "Days:1-10",
) -> str:
    """Build a GEFSv12 retrospective S3 URL for a variable/member/init."""
    init_stamp = init_time.strftime("%Y%m%d%H")
    return (
        f"{GEFSV12_BASE_URL}/{init_time:%Y}/{init_stamp}/{member}/{day_bucket}/"
        f"{variable_level}_{init_stamp}_{member}.grib2"
    )


def generate_demo_weather(start: str = "2011-01-01", end: Optional[str] = None) -> pd.DataFrame:
    """Generate deterministic Corn Belt weekly weather features."""
    if end is None:
        end = pd.Timestamp.today().normalize().strftime("%Y-%m-%d")
    weeks = pd.date_range(start=start, end=end, freq="W-FRI")
    rng = np.random.default_rng(8080)
    day_of_year = weeks.dayofyear.to_numpy()
    years = weeks.year.to_numpy()

    temp_f = 54 + 24 * np.sin(2 * np.pi * (day_of_year - 105) / 365.25) + rng.normal(0, 3.0, len(weeks))
    precip_mm = (18 + 10 * np.sin(2 * np.pi * (day_of_year - 70) / 365.25) + rng.normal(0, 5.0, len(weeks))).clip(min=0)
    gdd = np.clip((temp_f - 50) * 7, 0, None)

    climatology = pd.DataFrame({"week": weeks, "temp": temp_f, "precip": precip_mm})
    climatology["week_of_year"] = climatology["week"].dt.isocalendar().week.astype(int)
    weekly_climo = climatology.groupby("week_of_year").agg(temp=("temp", "mean"), precip=("precip", "mean"))
    temp_anomaly = [
        temp - weekly_climo.loc[int(week), "temp"]
        for temp, week in zip(temp_f, climatology["week_of_year"])
    ]
    precip_anomaly = [
        precip - weekly_climo.loc[int(week), "precip"]
        for precip, week in zip(precip_mm, climatology["week_of_year"])
    ]

    return pd.DataFrame(
        {
            "week": weeks,
            "weather_temp_mean_f": temp_f,
            "weather_precip_mm": precip_mm,
            "weather_gdd": gdd,
            "weather_temp_anomaly_f": temp_anomaly,
            "weather_precip_anomaly_mm": precip_anomaly,
            "weather_forecast_temp_week1_f": temp_f + rng.normal(0, 2.5, len(weeks)),
            "weather_forecast_precip_week1_mm": (precip_mm + rng.normal(0, 4.0, len(weeks))).clip(min=0),
            "weather_forecast_temp_week2_f": temp_f + rng.normal(0, 3.5, len(weeks)),
            "weather_forecast_precip_week2_mm": (precip_mm + rng.normal(0, 5.0, len(weeks))).clip(min=0),
            "weather_year": years,
        }
    )


def write_weather_request_catalog(path: Path, bbox: Tuple[float, float, float, float]) -> pd.DataFrame:
    """Write example adapter requests for full ERA5/CFSv2/GEFS data builds."""
    init_time = datetime(2025, 1, 1, 0)
    catalog = pd.DataFrame(
        [
            {
                "source": "era5",
                "description": "CDS request body for daily Corn Belt historical weather.",
                "dataset": ERA5_DATASET,
                "example": str(build_era5_daily_request(2025, 1, bbox=bbox)),
            },
            {
                "source": "cfsv2",
                "description": "NOAA CFSv2 operational 9-month forecast, week-1 lead example.",
                "dataset": "operational-9-month-forecast",
                "example": build_cfsv2_url(init_time, forecast_hour=168),
            },
            {
                "source": "gefsv12",
                "description": "NOAA GEFSv12 retrospective S3, day-1-to-10 temperature example.",
                "dataset": "GEFSv12/reforecast",
                "example": build_gefs_v12_url(init_time),
            },
        ]
    )
    write_table(catalog, path)
    return catalog


def load_weather_features(
    start: str,
    end: Optional[str],
    cache_path: Path,
    demo: bool,
    bbox: Tuple[float, float, float, float],
    catalog_path: Optional[Path] = None,
) -> pd.DataFrame:
    if demo:
        return generate_demo_weather(start=start, end=end)
    if cache_path.exists() or cache_path.with_suffix(".csv").exists():
        return read_table(cache_path)
    if catalog_path is not None:
        write_weather_request_catalog(catalog_path, bbox=bbox)
    raise RuntimeError(
        "No weather cache found. Run with --demo for an offline MVP, or populate "
        f"{cache_path} from ERA5/CFSv2/GEFS adapters."
    )
