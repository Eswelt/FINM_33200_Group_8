import numpy as np
import pandas as pd

from corn_forecast.features import build_feature_panel
from corn_forecast.volatility import evaluate_volatility_forecast


def _sample_panel(periods: int = 220) -> pd.DataFrame:
    weeks = pd.date_range("2020-01-03", periods=periods, freq="W-FRI")
    returns = 0.006 * np.sin(np.arange(periods) / 4)
    returns += np.where(np.arange(periods) % 11 == 0, 0.025, 0)
    returns += np.where(np.arange(periods) % 17 == 0, -0.021, 0)
    prices = pd.DataFrame(
        {
            "date": weeks,
            "close": 25 * np.exp(np.cumsum(returns)),
            "volume": 100_000 + 500 * np.arange(periods),
        }
    )
    return build_feature_panel(prices=prices)


def test_volatility_forecast_outputs_models_and_high_vol_labels():
    panel = _sample_panel()

    metrics, predictions = evaluate_volatility_forecast(
        panel,
        feature_sets=("price_only", "price_calendar"),
        estimators=("ridge", "hgb"),
        split_date="2022-01-01",
        test_window_weeks=8,
        retrain_step_weeks=8,
    )

    assert set(metrics) == {
        "price_only_ridge",
        "price_only_hgb",
        "price_calendar_ridge",
        "price_calendar_hgb",
    }
    assert metrics["price_only_ridge"]["target"] == "next_week_abs_log_return"
    assert {"predicted_abs_return_next", "high_vol_threshold", "y_true_high_vol", "y_pred_high_vol"}.issubset(
        predictions.columns
    )
    assert predictions["predicted_abs_return_next"].min() >= 0


def test_volatility_forecast_supports_rolling_window():
    panel = _sample_panel(periods=260)

    metrics, predictions = evaluate_volatility_forecast(
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
