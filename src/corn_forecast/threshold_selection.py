"""Threshold selection utilities for volatility-adjusted CORN trading targets."""

from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from corn_forecast.features import calendar_feature_columns, price_feature_columns
from corn_forecast.strategy import summarize_backtest


VOL_TARGET_LABELS = (-1, 0, 1)


def add_volatility_adjusted_target(
    panel: pd.DataFrame,
    k: float,
    volatility_column: str = "price_rolling_vol_12w",
) -> pd.DataFrame:
    """Add a -1/0/1 target using k times trailing weekly volatility as the no-trade band."""
    frame = panel.copy()
    returns = frame["target_log_return_next"]
    threshold = k * frame[volatility_column]
    frame["target_vol_adj_3class"] = np.select(
        [returns < -threshold, returns > threshold],
        [-1, 1],
        default=0,
    )
    frame.loc[returns.isna() | threshold.isna(), "target_vol_adj_3class"] = np.nan
    frame["target_vol_threshold"] = threshold
    return frame


def _walk_forward_splits(
    data: pd.DataFrame,
    split_date: str,
    test_window_weeks: int,
    retrain_step_weeks: int,
) -> Iterable[Tuple[int, pd.DataFrame, pd.DataFrame]]:
    split = pd.Timestamp(split_date)
    test_start = data.loc[data["week"] > split, "week"].min()
    if pd.isna(test_start):
        return

    fold = 0
    max_week = data["week"].max()
    while test_start <= max_week:
        test_end = test_start + pd.Timedelta(weeks=test_window_weeks - 1)
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
    raise ValueError(f"Unknown feature set: {feature_set}")


def _classifier(y_train: pd.Series) -> Pipeline:
    if y_train.nunique() < 2:
        model = DummyClassifier(strategy="most_frequent")
    else:
        model = LogisticRegression(max_iter=1000, class_weight="balanced", solver="lbfgs")
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", model),
        ]
    )


def _positive_class_probability(model: Pipeline, x_frame: pd.DataFrame, label: int) -> np.ndarray:
    classes = list(model.named_steps["model"].classes_)
    probabilities = model.predict_proba(x_frame)
    if label not in classes:
        return np.zeros(len(x_frame))
    return probabilities[:, classes.index(label)]


def _attach_strategy_returns(
    predictions: pd.DataFrame,
    long_probability_threshold: float,
    short_probability_threshold: float,
    allow_short: bool,
    transaction_cost_bps: float,
) -> pd.DataFrame:
    frames = []
    cost_per_turnover = transaction_cost_bps / 10_000.0
    for group_key, group in predictions.sort_values(["k", "feature_set", "week"]).groupby(["k", "feature_set"], sort=False):
        frame = group.copy()
        frame["position"] = 0.0
        frame.loc[frame["prob_up"] >= long_probability_threshold, "position"] = 1.0
        if allow_short:
            frame.loc[frame["prob_down"] >= short_probability_threshold, "position"] = -1.0
        frame["turnover"] = frame["position"].diff().abs().fillna(frame["position"].abs())
        frame["transaction_cost"] = frame["turnover"] * cost_per_turnover
        frame["strategy_log_return"] = frame["position"] * frame["target_log_return_next"] - frame["transaction_cost"]
        frame["benchmark_log_return"] = frame["target_log_return_next"]
        frame["cum_strategy_return"] = np.exp(frame["strategy_log_return"].cumsum()) - 1.0
        frame["cum_benchmark_return"] = np.exp(frame["benchmark_log_return"].cumsum()) - 1.0
        frame["model"] = f"vol_adj_k_{group_key[0]}_{group_key[1]}"
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _classification_metrics(predictions: pd.DataFrame) -> Dict[str, float]:
    y_true = predictions["y_true"].astype(int)
    y_pred = predictions["y_pred"].astype(int)
    matrix = confusion_matrix(y_true, y_pred, labels=list(VOL_TARGET_LABELS))
    counts = y_true.value_counts().reindex(VOL_TARGET_LABELS, fill_value=0)
    support = matrix.sum(axis=1)
    recall_by_class = np.divide(
        matrix.diagonal(),
        support,
        out=np.full(len(VOL_TARGET_LABELS), np.nan, dtype=float),
        where=support > 0,
    )
    present_class_recall = recall_by_class[~np.isnan(recall_by_class)]
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy_present_classes": float(present_class_recall.mean()) if len(present_class_recall) else np.nan,
        "macro_f1": float(f1_score(y_true, y_pred, labels=list(VOL_TARGET_LABELS), average="macro", zero_division=0)),
        "n_down": int(counts.loc[-1]),
        "n_flat": int(counts.loc[0]),
        "n_up": int(counts.loc[1]),
        "tradeable_event_rate": float((counts.loc[-1] + counts.loc[1]) / len(y_true)),
        "confusion_matrix_labels": list(VOL_TARGET_LABELS),
        "confusion_matrix": matrix.astype(int).tolist(),
    }


def evaluate_volatility_thresholds(
    panel: pd.DataFrame,
    k_values: Iterable[float] = (0.25, 0.5, 0.75, 1.0),
    feature_sets: Iterable[str] = ("price_only", "price_calendar"),
    split_date: str = "2022-12-31",
    test_window_weeks: int = 13,
    retrain_step_weeks: int = 13,
    long_probability_threshold: float = 0.45,
    short_probability_threshold: float = 0.45,
    allow_short: bool = False,
    transaction_cost_bps: float = 5.0,
) -> Tuple[Dict[str, Dict[str, float]], pd.DataFrame]:
    """Evaluate candidate volatility thresholds under the same walk-forward protocol."""
    prediction_frames = []
    metrics: Dict[str, Dict[str, float]] = {}

    for k in k_values:
        data = add_volatility_adjusted_target(panel, k=k)
        data["week"] = pd.to_datetime(data["week"])
        data = data.replace([np.inf, -np.inf], np.nan)
        data = data.dropna(subset=["target_log_return_next", "target_vol_adj_3class"]).copy()
        data["target_vol_adj_3class"] = data["target_vol_adj_3class"].astype(int)
        splits = list(_walk_forward_splits(data, split_date, test_window_weeks, retrain_step_weeks))
        if not splits:
            raise ValueError("Walk-forward split produced no out-of-sample folds.")

        for feature_set in feature_sets:
            columns = _feature_columns(data, feature_set)
            for fold, train, test in splits:
                model = _classifier(train["target_vol_adj_3class"])
                model.fit(train[columns], train["target_vol_adj_3class"])
                y_pred = model.predict(test[columns])
                prediction_frames.append(
                    pd.DataFrame(
                        {
                            "week": test["week"].to_numpy(),
                            "fold": fold,
                            "k": float(k),
                            "feature_set": feature_set,
                            "y_true": test["target_vol_adj_3class"].to_numpy(),
                            "y_pred": y_pred,
                            "prob_down": _positive_class_probability(model, test[columns], -1),
                            "prob_flat": _positive_class_probability(model, test[columns], 0),
                            "prob_up": _positive_class_probability(model, test[columns], 1),
                            "target_log_return_next": test["target_log_return_next"].to_numpy(),
                            "target_vol_threshold": test["target_vol_threshold"].to_numpy(),
                            "train_start": train["week"].min(),
                            "train_end": train["week"].max(),
                            "n_train": len(train),
                        }
                    )
                )

    predictions = pd.concat(prediction_frames, ignore_index=True)
    predictions = _attach_strategy_returns(
        predictions,
        long_probability_threshold=long_probability_threshold,
        short_probability_threshold=short_probability_threshold,
        allow_short=allow_short,
        transaction_cost_bps=transaction_cost_bps,
    )
    strategy_metrics = summarize_backtest(predictions)

    for (k, feature_set), group in predictions.groupby(["k", "feature_set"]):
        key = f"k_{k:g}_{feature_set}"
        metrics[key] = {
            "target": "next_week_volatility_adjusted_3class",
            "k": float(k),
            "feature_set": feature_set,
            "n_test": int(len(group)),
            "n_folds": int(group["fold"].nunique()),
            "long_probability_threshold": float(long_probability_threshold),
            "short_probability_threshold": float(short_probability_threshold),
            "allow_short": bool(allow_short),
            **_classification_metrics(group),
            **strategy_metrics[group["model"].iloc[0]],
        }

    return metrics, predictions.sort_values(["k", "feature_set", "week"]).reset_index(drop=True)
