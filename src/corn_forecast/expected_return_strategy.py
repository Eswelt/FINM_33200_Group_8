"""Expected-return trading strategy experiments for CORN ETF."""

from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from corn_forecast.features import calendar_feature_columns, price_feature_columns
from corn_forecast.strategy import summarize_backtest


FEATURE_SETS = ("price_only", "price_calendar")
ESTIMATORS = ("ridge", "hgb")


def _walk_forward_splits(
    data: pd.DataFrame,
    split_date: str,
    test_window_weeks: int,
    retrain_step_weeks: int,
    validation_scheme: str = "expanding",
    train_window_weeks: int = 260,
) -> Iterable[Tuple[int, pd.DataFrame, pd.DataFrame]]:
    if validation_scheme not in {"expanding", "rolling"}:
        raise ValueError(f"Unknown validation scheme: {validation_scheme}")

    split = pd.Timestamp(split_date)
    test_start = data.loc[data["week"] > split, "week"].min()
    if pd.isna(test_start):
        return

    fold = 0
    max_week = data["week"].max()
    while test_start <= max_week:
        test_end = test_start + pd.Timedelta(weeks=test_window_weeks - 1)
        if validation_scheme == "rolling":
            train_start = test_start - pd.Timedelta(weeks=train_window_weeks)
            train = data[(data["week"] >= train_start) & (data["week"] < test_start)].copy()
        else:
            train = data[data["week"] < test_start].copy()
        test = data[(data["week"] >= test_start) & (data["week"] <= test_end)].copy()
        if not train.empty and not test.empty:
            yield fold, train, test
        fold += 1
        test_start = test_start + pd.Timedelta(weeks=retrain_step_weeks)


def _feature_columns(data: pd.DataFrame, feature_set: str) -> List[str]:
    price_columns = price_feature_columns(data)
    if feature_set == "price_only":
        return price_columns
    if feature_set == "price_calendar":
        return price_columns + calendar_feature_columns(data)
    raise ValueError(f"Unknown expected-return feature set: {feature_set}")


def _regressor(estimator: str) -> Pipeline:
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if estimator == "ridge":
        steps.extend([("scaler", StandardScaler()), ("model", Ridge(alpha=1.0))])
    elif estimator == "hgb":
        steps.append(
            (
                "model",
                HistGradientBoostingRegressor(
                    learning_rate=0.04,
                    max_iter=150,
                    max_leaf_nodes=15,
                    l2_regularization=0.05,
                    random_state=33200,
                ),
            )
        )
    else:
        raise ValueError(f"Unknown estimator: {estimator}")
    return Pipeline(steps)


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
    splits = list(
        _walk_forward_splits(
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
        columns = _feature_columns(data, feature_set)
        for estimator in estimators:
            for fold, train, test in splits:
                model = _regressor(estimator)
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
