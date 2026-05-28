import numpy as np
import pandas as pd

from expected_return_strategy import evaluate_expected_return_strategy
from features import build_feature_panel


def _sample_panel(periods: int = 220) -> pd.DataFrame:
    weeks = pd.date_range("2020-01-03", periods=periods, freq="W-FRI")
    returns = 0.006 * np.sin(np.arange(periods) / 4)
    returns += np.where(np.arange(periods) % 13 == 0, 0.018, 0)
    returns += np.where(np.arange(periods) % 17 == 0, -0.016, 0)
    prices = pd.DataFrame(
        {
            "date": weeks,
            "close": 25 * np.exp(np.cumsum(returns)),
            "volume": 100_000 + 500 * np.arange(periods),
        }
    )
    return build_feature_panel(prices=prices)


def test_expected_return_strategy_outputs_models_and_trade_threshold():
    panel = _sample_panel()

    metrics, predictions = evaluate_expected_return_strategy(
        panel,
        feature_sets=("price_only", "price_calendar"),
        estimators=("ridge", "hgb"),
        split_date="2022-01-01",
        test_window_weeks=8,
        retrain_step_weeks=8,
        transaction_cost_bps=5.0,
        buffer_bps=25.0,
    )

    assert set(metrics) == {
        "price_only_ridge",
        "price_only_hgb",
        "price_calendar_ridge",
        "price_calendar_hgb",
    }
    assert metrics["price_only_ridge"]["trade_threshold"] == 0.003
    assert {"predicted_return", "position", "strategy_log_return"}.issubset(predictions.columns)


def test_expected_return_strategy_supports_rolling_window():
    panel = _sample_panel(periods=260)

    metrics, predictions = evaluate_expected_return_strategy(
        panel,
        feature_sets=("price_only",),
        estimators=("ridge",),
        split_date="2022-01-01",
        test_window_weeks=8,
        retrain_step_weeks=8,
        validation_scheme="rolling",
        train_window_weeks=104,
    )

    assert metrics["price_only_ridge"]["validation_scheme"] == "rolling"
    assert metrics["price_only_ridge"]["train_window_weeks"] == 104
    assert predictions["n_train"].max() <= 104
