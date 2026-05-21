from datetime import datetime

from corn_forecast.data.weather import build_cfsv2_url, build_era5_daily_request, build_gefs_v12_url


def test_cfsv2_url_matches_noaa_directory_shape():
    url = build_cfsv2_url(datetime(2025, 1, 1, 0), forecast_hour=168)

    assert "/2025/202501/20250101/2025010100/" in url
    assert url.endswith("pgbf2025010800.01.2025010100.grb2")


def test_gefs_v12_url_matches_s3_reforecast_shape():
    url = build_gefs_v12_url(datetime(2025, 1, 1, 0))

    assert "/GEFSv12/reforecast/2025/2025010100/c00/Days:1-10/" in url
    assert url.endswith("tmp_2m_2025010100_c00.grib2")


def test_era5_request_uses_corn_belt_bbox():
    request = build_era5_daily_request(2025, 1, bbox=(49.0, -104.0, 37.0, -80.0))

    assert request["dataset"] == "derived-era5-single-levels-daily-statistics"
    assert request["request"]["area"] == [49.0, -104.0, 37.0, -80.0]
    assert "2m_temperature" in request["request"]["variable"]
