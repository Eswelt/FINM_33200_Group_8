import numpy as np
import pandas as pd

from corn_forecast.features import build_feature_panel, feature_set_columns


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

    assert matched["weather_temp_mean_f"] == 1
    assert matched["text_kw_rain"] == 1
    numeric_columns, text_column = feature_set_columns(panel, "C_price_weather_text")
    assert "weather_temp_mean_f" in numeric_columns
    assert "text_kw_yield" in numeric_columns
    assert text_column == "report_text"
