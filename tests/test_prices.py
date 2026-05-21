import numpy as np
import pandas as pd

from corn_forecast.features import build_weekly_price_features


def test_next_week_target_uses_future_return_only_as_label():
    closes = np.array([10.0, 11.0, 10.5, 12.0, 12.5, 12.0, 13.0, 13.2, 12.8, 14.0, 13.7, 14.5, 15.0, 14.8])
    prices = pd.DataFrame(
        {
            "date": pd.date_range("2021-01-01", periods=len(closes), freq="W-FRI"),
            "close": closes,
            "volume": 100_000,
        }
    )

    panel = build_weekly_price_features(prices)

    expected_next_return = np.log(closes[1] / closes[0])
    assert np.isclose(panel.loc[0, "target_log_return_next"], expected_next_return)
    assert panel.loc[0, "target_up_next"] == 1
    assert np.isclose(panel.loc[2, "price_lag_return_1w"], np.log(closes[1] / closes[0]))
    assert np.isnan(panel.loc[len(panel) - 1, "target_log_return_next"])
