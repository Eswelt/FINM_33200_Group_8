"""Expected-return trading strategy experiments for CORN ETF."""

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from features import pipeline_feature_columns
from modeling import REGRESSION_ESTIMATORS, build_regressor
from strategy import summarize_backtest
from validation import walk_forward_splits


FEATURE_SETS = ("price_only", "price_calendar")
ESTIMATORS = REGRESSION_ESTIMATORS


def _attach_strategy_returns(
    predictions: pd.DataFrame,
    trade_threshold: float,
    allow_short: bool,
    transaction_cost_bps: float,
) -> pd.DataFrame:
    frames = []
    cost_per_turnover = transaction_cost_bps / 10_000.0
    for model, group in predictions.sort_values(["model", "week"]).groupby("model", sort=False):
        frame = group.copy()
        frame["trade_threshold"] = trade_threshold
        frame["position"] = 0.0
        frame.loc[frame["predicted_return"] > trade_threshold, "position"] = 1.0
        if allow_short:
            frame.loc[frame["predicted_return"] < -trade_threshold, "position"] = -1.0
        frame["turnover"] = frame["position"].diff().abs().fillna(frame["position"].abs())
        frame["transaction_cost"] = frame["turnover"] * cost_per_turnover
        frame["strategy_log_return"] = frame["position"] * frame["target_log_return_next"] - frame["transaction_cost"]
        frame["benchmark_log_return"] = frame["target_log_return_next"]
        frame["cum_strategy_return"] = np.exp(frame["strategy_log_return"].cumsum()) - 1.0
        frame["cum_benchmark_return"] = np.exp(frame["benchmark_log_return"].cumsum()) - 1.0
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _regression_metrics(group: pd.DataFrame) -> Dict[str, float]:
    y_true = group["target_log_return_next"]
    y_pred = group["predicted_return"]
    traded = group[group["position"] != 0]
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "direction_accuracy": float(((y_true > 0) == (y_pred > 0)).mean()),
        "trade_count": int(len(traded)),
        "trade_frequency": float(len(traded) / len(group)),
        "hit_rate_traded_weeks": float((traded["target_log_return_next"] > 0).mean()) if len(traded) else np.nan,
        "average_return_traded_weeks": float(traded["target_log_return_next"].mean()) if len(traded) else np.nan,
        "average_predicted_return_traded_weeks": float(traded["predicted_return"].mean()) if len(traded) else np.nan,
    }


def evaluate_expected_return_strategy(
    panel: pd.DataFrame,
    feature_sets: Iterable[str] = FEATURE_SETS,
    estimators: Iterable[str] = ESTIMATORS,
    split_date: str = "2022-12-31",
    test_window_weeks: int = 13,
    retrain_step_weeks: int = 13,
    transaction_cost_bps: float = 5.0,
    buffer_bps: float = 25.0,
    allow_short: bool = False,
    validation_scheme: str = "expanding",
    train_window_weeks: int = 260,
) -> Tuple[Dict[str, Dict[str, float]], pd.DataFrame]:
    """Forecast next-week returns and trade only when predicted edge clears cost plus buffer."""
    data = panel.copy()
    data["week"] = pd.to_datetime(data["week"])
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna(subset=["target_log_return_next"]).copy()
    if "report_text" in data.columns:
        data["report_text"] = data["report_text"].fillna("")
    splits = list(
        walk_forward_splits(
            data,
            split_date=split_date,
            test_window_weeks=test_window_weeks,
            retrain_step_weeks=retrain_step_weeks,
            validation_scheme=validation_scheme,
            train_window_weeks=train_window_weeks,
        )
    )
    if not splits:
        raise ValueError("Walk-forward split produced no out-of-sample folds.")

    prediction_frames = []
    for feature_set in feature_sets:
        numeric_columns, text_column = pipeline_feature_columns(data, feature_set)
        columns = numeric_columns + ([text_column] if text_column else [])
        if not columns:
            raise ValueError(f"No usable columns found for {feature_set}.")
        for estimator in estimators:
            for fold, train, test in splits:
                model = build_regressor(estimator, numeric_columns=numeric_columns, text_column=text_column)
                model.fit(train[columns], train["target_log_return_next"])
                predicted_return = model.predict(test[columns])
                prediction_frames.append(
                    pd.DataFrame(
                        {
                            "week": test["week"].to_numpy(),
                            "fold": fold,
                            "feature_set": feature_set,
                            "estimator": estimator,
                            "model": f"{feature_set}_{estimator}",
                            "target_log_return_next": test["target_log_return_next"].to_numpy(),
                            "predicted_return": predicted_return,
                            "train_start": train["week"].min(),
                            "train_end": train["week"].max(),
                            "n_train": len(train),
                        }
                    )
                )

    predictions = pd.concat(prediction_frames, ignore_index=True)
    trade_threshold = (transaction_cost_bps + buffer_bps) / 10_000.0
    predictions = _attach_strategy_returns(
        predictions,
        trade_threshold=trade_threshold,
        allow_short=allow_short,
        transaction_cost_bps=transaction_cost_bps,
    )
    strategy_metrics = summarize_backtest(predictions)

    metrics: Dict[str, Dict[str, float]] = {}
    for model, group in predictions.groupby("model"):
        values = {
            "target": "next_week_log_return",
            "feature_set": group["feature_set"].iloc[0],
            "estimator": group["estimator"].iloc[0],
            "validation_scheme": validation_scheme,
            "train_window_weeks": int(train_window_weeks) if validation_scheme == "rolling" else None,
            "transaction_cost_bps": float(transaction_cost_bps),
            "buffer_bps": float(buffer_bps),
            "trade_threshold": float(trade_threshold),
            "allow_short": bool(allow_short),
            "n_test": int(len(group)),
            "n_folds": int(group["fold"].nunique()),
            **_regression_metrics(group),
            **strategy_metrics[model],
        }
        metrics[model] = values

    return metrics, predictions.sort_values(["model", "week"]).reset_index(drop=True)
