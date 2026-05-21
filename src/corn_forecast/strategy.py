"""Trading-signal evaluation for out-of-sample model predictions."""

from typing import Dict

import numpy as np
import pandas as pd


WEEKS_PER_YEAR = 52


def assign_positions(
    probabilities: pd.Series,
    long_threshold: float = 0.55,
    short_threshold: float = 0.45,
    allow_short: bool = False,
) -> pd.Series:
    """Convert calibrated direction probabilities into long/flat or long/short positions."""
    positions = pd.Series(0.0, index=probabilities.index)
    positions.loc[probabilities >= long_threshold] = 1.0
    if allow_short:
        positions.loc[probabilities <= short_threshold] = -1.0
    return positions


def backtest_predictions(
    predictions: pd.DataFrame,
    long_threshold: float = 0.55,
    short_threshold: float = 0.45,
    allow_short: bool = False,
    transaction_cost_bps: float = 5.0,
) -> pd.DataFrame:
    """Attach a simple next-week PnL path to each model's walk-forward predictions.

    The row dated week t contains the prediction made at week t for the return
    from t to t+1. Transaction cost is charged when the target position changes.
    """
    frames = []
    cost_per_turnover = transaction_cost_bps / 10_000.0

    for model, group in predictions.sort_values(["model", "week"]).groupby("model", sort=False):
        frame = group.copy()
        frame["position"] = assign_positions(
            frame["y_prob"],
            long_threshold=long_threshold,
            short_threshold=short_threshold,
            allow_short=allow_short,
        )
        frame["turnover"] = frame["position"].diff().abs().fillna(frame["position"].abs())
        frame["transaction_cost"] = frame["turnover"] * cost_per_turnover
        frame["strategy_log_return"] = frame["position"] * frame["target_log_return_next"] - frame["transaction_cost"]
        frame["benchmark_log_return"] = frame["target_log_return_next"]
        frame["cum_strategy_return"] = np.exp(frame["strategy_log_return"].cumsum()) - 1.0
        frame["cum_benchmark_return"] = np.exp(frame["benchmark_log_return"].cumsum()) - 1.0
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def _max_drawdown(cumulative_returns: pd.Series) -> float:
    wealth = 1.0 + cumulative_returns
    running_peak = wealth.cummax()
    drawdown = wealth / running_peak - 1.0
    return float(drawdown.min())


def summarize_backtest(predictions: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Summarize strategy quality by model."""
    summaries: Dict[str, Dict[str, float]] = {}
    for model, group in predictions.groupby("model"):
        returns = group["strategy_log_return"].fillna(0.0)
        benchmark = group["benchmark_log_return"].fillna(0.0)
        weekly_vol = returns.std(ddof=0)
        benchmark_vol = benchmark.std(ddof=0)
        summaries[model] = {
            "strategy_total_return": float(np.exp(returns.sum()) - 1.0),
            "benchmark_total_return": float(np.exp(benchmark.sum()) - 1.0),
            "strategy_annual_return": float(np.exp(returns.mean() * WEEKS_PER_YEAR) - 1.0),
            "strategy_annual_vol": float(weekly_vol * np.sqrt(WEEKS_PER_YEAR)),
            "strategy_sharpe": float((returns.mean() / weekly_vol) * np.sqrt(WEEKS_PER_YEAR)) if weekly_vol > 0 else np.nan,
            "benchmark_sharpe": float((benchmark.mean() / benchmark_vol) * np.sqrt(WEEKS_PER_YEAR)) if benchmark_vol > 0 else np.nan,
            "max_drawdown": _max_drawdown(group["cum_strategy_return"]),
            "mean_position": float(group["position"].mean()),
            "turnover": float(group["turnover"].mean()),
        }
    return summaries
