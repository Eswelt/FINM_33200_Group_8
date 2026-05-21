from typing import Optional

import numpy as np
import pandas as pd

from corn_forecast.data.usda import build_weekly_text_features


def build_weekly_price_features(prices: pd.DataFrame) -> pd.DataFrame:
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
    weekly["target_log_return_next"] = weekly["price_log_return"].shift(-1)
    weekly["target_up_next"] = np.where(
        weekly["target_log_return_next"].isna(),
        np.nan,
        (weekly["target_log_return_next"] > 0).astype(int),
    )

    return weekly.reset_index(drop=True)


def build_feature_panel(
    prices: pd.DataFrame,
    weather: Optional[pd.DataFrame] = None,
    usda_releases: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    panel = build_weekly_price_features(prices)

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


def text_numeric_feature_columns(panel: pd.DataFrame) -> list:
    columns = [column for column in panel.columns if column.startswith("text_kw_")]
    if "report_count" in panel.columns:
        columns.append("report_count")
    return columns


def feature_set_columns(panel: pd.DataFrame, feature_set: str) -> tuple:
    price_columns = price_feature_columns(panel)
    if feature_set == "A_price":
        return price_columns, None
    if feature_set == "B_price_weather":
        return price_columns + weather_feature_columns(panel), None
    if feature_set == "C_price_weather_text":
        return price_columns + weather_feature_columns(panel) + text_numeric_feature_columns(panel), "report_text"
    raise ValueError(f"Unknown feature set: {feature_set}")
