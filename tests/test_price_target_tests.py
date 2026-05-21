import numpy as np
import pandas as pd

from corn_forecast.features import build_feature_panel
from corn_forecast.price_target_tests import add_three_class_return_target, run_price_only_target_tests


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


def test_three_class_target_uses_symmetric_threshold():
    panel = pd.DataFrame(
        {
            "target_log_return_next": [-0.08, -0.01, 0.0, 0.02, 0.07, np.nan],
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

    assert set(metrics) == {"return_regression", "three_class_5pct"}
    assert metrics["return_regression"]["n_folds"] > 1
    assert metrics["three_class_5pct"]["n_up"] > 0
    assert metrics["three_class_5pct"]["n_down"] > 0
    assert {"return_regression", "three_class_5pct"} == set(predictions["experiment"])
