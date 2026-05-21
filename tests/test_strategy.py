import numpy as np
import pandas as pd

from corn_forecast.strategy import assign_positions, backtest_predictions, summarize_backtest


def test_assign_positions_defaults_to_long_flat():
    probabilities = pd.Series([0.40, 0.54, 0.55, 0.80])

    positions = assign_positions(probabilities, long_threshold=0.55, allow_short=False)

    assert positions.tolist() == [0.0, 0.0, 1.0, 1.0]


def test_backtest_charges_turnover_costs():
    predictions = pd.DataFrame(
        {
            "week": pd.date_range("2024-01-05", periods=3, freq="W-FRI"),
            "model": ["demo"] * 3,
            "y_prob": [0.60, 0.40, 0.70],
            "target_log_return_next": [0.01, -0.02, 0.03],
        }
    )

    result = backtest_predictions(predictions, long_threshold=0.55, transaction_cost_bps=10)
    summary = summarize_backtest(result)

    assert result["position"].tolist() == [1.0, 0.0, 1.0]
    assert np.isclose(result.loc[0, "transaction_cost"], 0.001)
    assert "strategy_sharpe" in summary["demo"]
