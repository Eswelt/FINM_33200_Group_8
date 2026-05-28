import numpy as np
import pandas as pd

from corn_forecast.features import build_feature_panel, calendar_feature_columns, feature_set_columns, pipeline_feature_columns


def test_feature_panel_joins_weather_and_text_on_week_end():
    weeks = pd.date_range("2024-01-05", periods=16, freq="W-FRI")
    prices = pd.DataFrame(
        {
            "date": weeks,
            "close": np.linspace(20, 25, len(weeks)),
            "volume": 100_000,
        }
    )
    weather = pd.DataFrame(
        {
            "week": weeks,
            "weather_temp_mean_f": np.arange(len(weeks)),
            "weather_precip_mm": 1.0,
        }
    )
    usda = pd.DataFrame(
        {
            "release_date": [pd.Timestamp("2024-01-08")],
            "publication": ["crop_progress"],
            "title": ["Demo"],
            "url": ["demo://report"],
            "text": ["rain heat yield"],
        }
    )

    panel = build_feature_panel(prices=prices, weather=weather, usda_releases=usda)
    matched = panel.loc[panel["week"] == pd.Timestamp("2024-01-12")].iloc[0]

    assert matched["calendar_month"] == 1
    assert matched["calendar_is_winter_storage_season"] == 1
    assert matched["weather_temp_mean_f"] == 1
    assert matched["text_kw_rain"] == 1
    numeric_columns, text_column = feature_set_columns(panel, "C_price_weather_text")
    assert "weather_temp_mean_f" in numeric_columns
    assert "text_kw_yield" in numeric_columns
    assert text_column == "report_text"
    price_calendar_columns, _ = feature_set_columns(panel, "A_price_calendar")
    assert "calendar_week_sin" in price_calendar_columns
    assert "calendar_is_harvest_season" in calendar_feature_columns(panel)


def test_pipeline_feature_sets_pick_up_weather_text_and_ai_columns():
    panel = pd.DataFrame(
        {
            "price_lag_return_1w": [0.01],
            "calendar_week_sin": [0.1],
            "weather_temp_anomaly_f": [2.0],
            "text_drought_score": [1.0],
            "report_text": ["dry weather"],
            "ai_bullish_score": [0.4],
            "gdelt_yield_supply_risk": [0.7],
        }
    )

    numeric, text_column = pipeline_feature_columns(panel, "price_calendar_weather_text_ai")

    assert "price_lag_return_1w" in numeric
    assert "calendar_week_sin" in numeric
    assert "weather_temp_anomaly_f" in numeric
    assert "text_drought_score" in numeric
    assert "ai_bullish_score" in numeric
    assert text_column == "report_text"

    numeric, text_column = pipeline_feature_columns(panel, "price_ai")
    assert "price_lag_return_1w" in numeric
    assert "ai_bullish_score" in numeric
    assert "calendar_week_sin" not in numeric
    assert text_column is None

    numeric, text_column = pipeline_feature_columns(panel, "price_calendar_ai_gdelt")
    assert "price_lag_return_1w" in numeric
    assert "calendar_week_sin" in numeric
    assert "ai_bullish_score" in numeric
    assert "gdelt_yield_supply_risk" in numeric
    assert text_column is None
