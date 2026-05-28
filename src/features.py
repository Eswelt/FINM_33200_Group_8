from typing import Optional

import numpy as np
import pandas as pd

from data.usda import build_weekly_text_features


FEATURE_SET_PARTS = {
    "price_only": ("price",),
    "price_calendar": ("price", "calendar"),
    "price_weather": ("price", "weather"),
    "price_gdelt": ("price", "gdelt"),
    "price_ai": ("price", "ai"),
    "price_weather_text": ("price", "weather", "text"),
    "price_ai_gdelt": ("price", "ai", "gdelt"),
    "price_calendar_weather": ("price", "calendar", "weather"),
    "price_calendar_text": ("price", "calendar", "text"),
    "price_calendar_gdelt": ("price", "calendar", "gdelt"),
    "price_calendar_ai": ("price", "calendar", "ai"),
    "price_calendar_weather_text": ("price", "calendar", "weather", "text"),
    "price_calendar_ai_gdelt": ("price", "calendar", "ai", "gdelt"),
    "price_calendar_weather_ai": ("price", "calendar", "weather", "ai"),
    "price_calendar_weather_text_ai": ("price", "calendar", "weather", "text", "ai"),
}

LEGACY_FEATURE_SET_ALIASES = {
    "A_price": "price_only",
    "A_price_calendar": "price_calendar",
    "B_price_weather": "price_weather",
    "C_price_weather_text": "price_weather_text",
}


def build_weekly_price_features(prices: pd.DataFrame) -> pd.DataFrame:
    """Create point-in-time weekly price features and the next-week label."""
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values("date").set_index("date")

    weekly = (
        frame.resample("W-FRI")
        .agg(close=("close", "last"), volume=("volume", "sum"))
        .dropna(subset=["close"])
    )
    weekly["week"] = weekly.index.normalize()
    weekly["price_log_close"] = np.log(weekly["close"])
    weekly["price_log_return"] = weekly["price_log_close"].diff()
    for lag in (1, 2, 4, 12):
        weekly[f"price_lag_return_{lag}w"] = weekly["price_log_return"].shift(lag)

    weekly["price_rolling_vol_4w"] = weekly["price_log_return"].rolling(4).std()
    weekly["price_rolling_vol_12w"] = weekly["price_log_return"].rolling(12).std()
    weekly["price_momentum_4w"] = weekly["price_log_close"] - weekly["price_log_close"].shift(4)
    weekly["price_momentum_12w"] = weekly["price_log_close"] - weekly["price_log_close"].shift(12)
    weekly["price_volume_change_4w"] = np.log(weekly["volume"] / weekly["volume"].shift(4))
    # The next-week return is a label only. It is never included in feature sets.
    weekly["target_log_return_next"] = weekly["price_log_return"].shift(-1)
    weekly["target_up_next"] = np.where(
        weekly["target_log_return_next"].isna(),
        np.nan,
        (weekly["target_log_return_next"] > 0).astype(int),
    )

    return weekly.reset_index(drop=True)


def add_calendar_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Add deterministic Corn Belt seasonality features from the weekly date."""
    frame = panel.copy()
    week = pd.to_datetime(frame["week"])
    week_of_year = week.dt.isocalendar().week.astype(int)
    month = week.dt.month

    frame["calendar_month"] = month
    frame["calendar_quarter"] = week.dt.quarter
    frame["calendar_week_of_year"] = week_of_year
    frame["calendar_week_sin"] = np.sin(2 * np.pi * week_of_year / 52.0)
    frame["calendar_week_cos"] = np.cos(2 * np.pi * week_of_year / 52.0)
    frame["calendar_is_planting_season"] = month.isin([4, 5]).astype(int)
    frame["calendar_is_pollination_weather_season"] = month.isin([6, 7, 8]).astype(int)
    frame["calendar_is_harvest_season"] = month.isin([9, 10, 11]).astype(int)
    frame["calendar_is_winter_storage_season"] = month.isin([12, 1, 2]).astype(int)
    return frame


def build_feature_panel(
    prices: pd.DataFrame,
    weather: Optional[pd.DataFrame] = None,
    usda_releases: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    panel = build_weekly_price_features(prices)
    panel = add_calendar_features(panel)

    if weather is not None and not weather.empty:
        weather_frame = weather.copy()
        weather_frame["week"] = pd.to_datetime(weather_frame["week"]).dt.normalize()
        panel = panel.merge(weather_frame, on="week", how="left")

    if usda_releases is not None and not usda_releases.empty:
        text_features = build_weekly_text_features(usda_releases)
        text_features["week"] = pd.to_datetime(text_features["week"]).dt.normalize()
        panel = panel.merge(text_features, on="week", how="left")

    if "report_text" not in panel.columns:
        panel["report_text"] = ""
    panel["report_text"] = panel["report_text"].fillna("")

    text_numeric_columns = [column for column in panel.columns if column.startswith("text_kw_")]
    for column in text_numeric_columns:
        panel[column] = panel[column].fillna(0)
    if "report_count" in panel.columns:
        panel["report_count"] = panel["report_count"].fillna(0)

    panel = panel.replace([np.inf, -np.inf], np.nan)
    return panel.sort_values("week").reset_index(drop=True)


def price_feature_columns(panel: pd.DataFrame) -> list:
    return [
        column
        for column in panel.columns
        if column.startswith("price_") and column not in {"price_log_close"}
    ]


def weather_feature_columns(panel: pd.DataFrame) -> list:
    return [column for column in panel.columns if column.startswith("weather_")]


def calendar_feature_columns(panel: pd.DataFrame) -> list:
    return [column for column in panel.columns if column.startswith("calendar_")]


def text_numeric_feature_columns(panel: pd.DataFrame) -> list:
    columns = [
        column
        for column in panel.columns
        if column.startswith("text_") and column != "report_text"
    ]
    if "report_count" in panel.columns:
        columns.append("report_count")
    return sorted(set(columns))


def ai_feature_columns(panel: pd.DataFrame) -> list:
    return [column for column in panel.columns if column.startswith("ai_")]


def gdelt_feature_columns(panel: pd.DataFrame) -> list:
    return [column for column in panel.columns if column.startswith("gdelt_")]


def _columns_for_parts(panel: pd.DataFrame, parts: tuple) -> list:
    family_columns = {
        "price": price_feature_columns(panel),
        "calendar": calendar_feature_columns(panel),
        "weather": weather_feature_columns(panel),
        "text": text_numeric_feature_columns(panel),
        "ai": ai_feature_columns(panel),
        "gdelt": gdelt_feature_columns(panel),
    }
    columns = []
    for part in parts:
        columns.extend(family_columns[part])
    return columns


def pipeline_feature_columns(panel: pd.DataFrame, feature_set: str) -> tuple:
    """Return numeric and optional free-text columns for modular prediction pipelines."""
    canonical = LEGACY_FEATURE_SET_ALIASES.get(feature_set, feature_set)
    if canonical not in FEATURE_SET_PARTS:
        raise ValueError(f"Unknown pipeline feature set: {feature_set}")
    parts = FEATURE_SET_PARTS[canonical]
    return _columns_for_parts(panel, parts), "report_text" if "text" in parts else None


def feature_set_columns(panel: pd.DataFrame, feature_set: str) -> tuple:
    return pipeline_feature_columns(panel, feature_set)
