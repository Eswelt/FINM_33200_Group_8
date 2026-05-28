import numpy as np
import pandas as pd

from features import build_feature_panel
from threshold_selection import add_volatility_adjusted_target, evaluate_volatility_thresholds


def _sample_panel(periods: int = 180) -> pd.DataFrame:
    weeks = pd.date_range("2020-01-03", periods=periods, freq="W-FRI")
    returns = 0.02 * np.sin(np.arange(periods) / 3)
    returns[8::17] += 0.08
    returns[13::19] -= 0.08
    prices = pd.DataFrame(
        {
            "date": weeks,
            "close": 25 * np.exp(np.cumsum(returns)),
            "volume": 100_000 + np.arange(periods) * 500,
        }
    )
    return build_feature_panel(prices=prices)


def test_volatility_adjusted_target_uses_trailing_volatility_band():
    panel = pd.DataFrame(
        {
            "target_log_return_next": [-0.04, -0.01, 0.01, 0.04, np.nan],
            "price_rolling_vol_12w": [0.04, 0.04, 0.04, 0.04, 0.04],
        }
    )

    result = add_volatility_adjusted_target(panel, k=0.5)

    assert result["target_vol_adj_3class"].tolist()[:4] == [-1, 0, 0, 1]
    assert np.isnan(result["target_vol_adj_3class"].iloc[4])


def test_evaluate_volatility_thresholds_compares_k_and_feature_sets():
    panel = _sample_panel()

    metrics, predictions = evaluate_volatility_thresholds(
        panel,
        k_values=(0.25, 0.5),
        feature_sets=("price_only", "price_calendar"),
        split_date="2022-01-01",
        test_window_weeks=8,
        retrain_step_weeks=8,
        long_probability_threshold=0.45,
    )

    assert set(metrics) == {
        "k_0.25_price_only",
        "k_0.25_price_calendar",
        "k_0.5_price_only",
        "k_0.5_price_calendar",
    }
    assert set(predictions["k"]) == {0.25, 0.5}
    assert set(predictions["feature_set"]) == {"price_only", "price_calendar"}
    assert {"prob_down", "prob_flat", "prob_up", "strategy_log_return"}.issubset(predictions.columns)


def test_rolling_validation_uses_fixed_length_training_window():
    panel = _sample_panel(periods=240)

    metrics, predictions = evaluate_volatility_thresholds(
        panel,
        k_values=(1.0,),
        feature_sets=("price_only",),
        split_date="2022-01-01",
        test_window_weeks=8,
        retrain_step_weeks=8,
        validation_scheme="rolling",
        train_window_weeks=104,
    )

    assert metrics["k_1_price_only"]["validation_scheme"] == "rolling"
    assert metrics["k_1_price_only"]["train_window_weeks"] == 104
    assert predictions["n_train"].max() <= 104
