import numpy as np
import pandas as pd

from features import build_feature_panel
from price_target_tests import (
    add_three_class_return_target,
    arithmetic_threshold_to_log_bounds,
    run_price_only_target_tests,
)


def _sample_price_panel(periods: int = 180) -> pd.DataFrame:
    weeks = pd.date_range("2020-01-03", periods=periods, freq="W-FRI")
    returns = np.zeros(periods)
    returns[1::9] = 0.065
    returns[5::11] = -0.06
    returns += 0.008 * np.sin(np.arange(periods) / 4)
    close = 25 * np.exp(np.cumsum(returns))
    prices = pd.DataFrame(
        {
            "date": weeks,
            "close": close,
            "volume": 100_000 + 1_000 * np.arange(periods),
        }
    )
    return build_feature_panel(prices=prices)


def test_three_class_target_converts_arithmetic_band_to_log_bounds():
    down_log, up_log = arithmetic_threshold_to_log_bounds(0.05)
    panel = pd.DataFrame(
        {
            "target_log_return_next": [down_log - 0.001, down_log + 0.001, 0.0, up_log - 0.001, up_log, np.nan],
        }
    )

    result = add_three_class_return_target(panel, threshold=0.05)

    assert result["target_return_3class"].tolist()[:5] == [-1, 0, 0, 0, 1]
    assert np.isnan(result["target_return_3class"].iloc[5])


def test_price_only_target_tests_return_both_experiments():
    panel = _sample_price_panel()

    metrics, predictions = run_price_only_target_tests(
        panel,
        split_date="2022-01-01",
        test_window_weeks=8,
        retrain_step_weeks=8,
        three_class_threshold=0.05,
    )

    assert set(metrics) == {
        "price_only_return_regression",
        "price_only_three_class_fixed",
        "price_calendar_return_regression",
        "price_calendar_three_class_fixed",
    }
    assert metrics["price_only_return_regression"]["n_folds"] > 1
    assert metrics["price_calendar_return_regression"]["feature_set"] == "price_calendar"
    assert metrics["price_only_three_class_fixed"]["n_up"] > 0
    assert metrics["price_only_three_class_fixed"]["n_down"] > 0
    assert {"return_regression", "three_class_fixed"} == set(predictions["experiment"])
    assert {"price_only", "price_calendar"} == set(predictions["feature_set"])
