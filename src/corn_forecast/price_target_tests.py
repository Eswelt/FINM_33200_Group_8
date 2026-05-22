"""Price-only target tests for choosing the CORN forecasting objective."""

from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from corn_forecast.features import calendar_feature_columns, price_feature_columns


THREE_CLASS_LABELS = (-1, 0, 1)
PRICE_TARGET_FEATURE_SETS = ("price_only", "price_calendar")


def add_three_class_return_target(panel: pd.DataFrame, threshold: float = 0.02) -> pd.DataFrame:
    """Add -1/0/1 classes for next-week returns below/inside/above a threshold."""
    frame = panel.copy()
    returns = frame["target_log_return_next"]
    frame["target_return_3class"] = np.select(
        [returns <= -threshold, returns >= threshold],
        [-1, 1],
        default=0,
    )
    frame.loc[returns.isna(), "target_return_3class"] = np.nan
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


def _price_regression_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ]
    )


def _price_three_class_pipeline(y_train: pd.Series) -> Pipeline:
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


def _feature_columns(data: pd.DataFrame, feature_set: str) -> List[str]:
    price_columns = price_feature_columns(data)
    if feature_set == "price_only":
        return price_columns
    if feature_set == "price_calendar":
        return price_columns + calendar_feature_columns(data)
    raise ValueError(f"Unknown price target feature set: {feature_set}")


def _regression_metrics(predictions: pd.DataFrame, feature_set: str) -> Dict[str, float]:
    y_true = predictions["y_true_return"]
    y_pred = predictions["y_pred_return"]
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    direction_true = (y_true > 0).astype(int)
    direction_pred = (y_pred > 0).astype(int)
    return {
        "target": "next_week_log_return",
        "model": "price_only_ridge",
        "feature_set": feature_set,
        "n_test": int(len(predictions)),
        "n_folds": int(predictions["fold"].nunique()),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": rmse,
        "r2": float(r2_score(y_true, y_pred)),
        "direction_accuracy": float(accuracy_score(direction_true, direction_pred)),
        "mean_actual_return": float(y_true.mean()),
        "mean_predicted_return": float(y_pred.mean()),
    }


def _three_class_metrics(predictions: pd.DataFrame, threshold: float, feature_set: str) -> Dict[str, float]:
    y_true = predictions["y_true_3class"].astype(int)
    y_pred = predictions["y_pred_3class"].astype(int)
    matrix = confusion_matrix(y_true, y_pred, labels=list(THREE_CLASS_LABELS))
    counts = y_true.value_counts().reindex(THREE_CLASS_LABELS, fill_value=0)
    support = matrix.sum(axis=1)
    recall_by_class = np.divide(
        matrix.diagonal(),
        support,
        out=np.full(len(THREE_CLASS_LABELS), np.nan, dtype=float),
        where=support > 0,
    )
    present_class_recall = recall_by_class[~np.isnan(recall_by_class)]
    return {
        "target": f"next_week_log_return_3class_{threshold:.1%}_bands",
        "model": "price_only_logit",
        "feature_set": feature_set,
        "threshold": float(threshold),
        "n_test": int(len(predictions)),
        "n_folds": int(predictions["fold"].nunique()),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy_present_classes": float(present_class_recall.mean()) if len(present_class_recall) else np.nan,
        "macro_f1": float(f1_score(y_true, y_pred, labels=list(THREE_CLASS_LABELS), average="macro", zero_division=0)),
        "n_down": int(counts.loc[-1]),
        "n_flat": int(counts.loc[0]),
        "n_up": int(counts.loc[1]),
        "extreme_event_rate": float((counts.loc[-1] + counts.loc[1]) / len(y_true)),
        "has_both_extreme_classes": bool(counts.loc[-1] > 0 and counts.loc[1] > 0),
        "confusion_matrix_labels": list(THREE_CLASS_LABELS),
        "confusion_matrix": matrix.astype(int).tolist(),
    }


def run_price_only_target_tests(
    panel: pd.DataFrame,
    split_date: str = "2022-12-31",
    test_window_weeks: int = 13,
    retrain_step_weeks: int = 13,
    three_class_threshold: float = 0.02,
) -> Tuple[Dict[str, Dict[str, float]], pd.DataFrame]:
    """Run return regression and fixed-threshold three-class tests with price and price+calendar features."""
    data = add_three_class_return_target(panel, threshold=three_class_threshold)
    data["week"] = pd.to_datetime(data["week"])
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna(subset=["target_log_return_next", "target_return_3class"]).copy()
    data["target_return_3class"] = data["target_return_3class"].astype(int)

    if not price_feature_columns(data):
        raise ValueError("No price feature columns found for price-only target tests.")

    regression_frames = []
    class_frames = []
    splits = list(_walk_forward_splits(data, split_date, test_window_weeks, retrain_step_weeks))
    if not splits:
        raise ValueError("Walk-forward split produced no out-of-sample folds.")

    for feature_set in PRICE_TARGET_FEATURE_SETS:
        numeric_columns = _feature_columns(data, feature_set)
        for fold, train, test in splits:
            reg_model = _price_regression_pipeline()
            reg_model.fit(train[numeric_columns], train["target_log_return_next"])
            y_pred_return = reg_model.predict(test[numeric_columns])
            regression_frames.append(
                pd.DataFrame(
                    {
                        "week": test["week"].to_numpy(),
                        "fold": fold,
                        "experiment": "return_regression",
                        "feature_set": feature_set,
                        "model": "price_only_ridge",
                        "y_true_return": test["target_log_return_next"].to_numpy(),
                        "y_pred_return": y_pred_return,
                        "train_start": train["week"].min(),
                        "train_end": train["week"].max(),
                        "n_train": len(train),
                    }
                )
            )

            class_model = _price_three_class_pipeline(train["target_return_3class"])
            class_model.fit(train[numeric_columns], train["target_return_3class"])
            y_pred_class = class_model.predict(test[numeric_columns])
            class_frames.append(
                pd.DataFrame(
                    {
                        "week": test["week"].to_numpy(),
                        "fold": fold,
                        "experiment": "three_class_fixed",
                        "feature_set": feature_set,
                        "model": "price_only_logit",
                        "y_true_3class": test["target_return_3class"].to_numpy(),
                        "y_pred_3class": y_pred_class,
                        "target_log_return_next": test["target_log_return_next"].to_numpy(),
                        "train_start": train["week"].min(),
                        "train_end": train["week"].max(),
                        "n_train": len(train),
                    }
                )
            )

    regression_predictions = pd.concat(regression_frames, ignore_index=True)
    class_predictions = pd.concat(class_frames, ignore_index=True)
    metrics = {}
    for feature_set in PRICE_TARGET_FEATURE_SETS:
        reg_group = regression_predictions[regression_predictions["feature_set"] == feature_set]
        class_group = class_predictions[class_predictions["feature_set"] == feature_set]
        metrics[f"{feature_set}_return_regression"] = _regression_metrics(reg_group, feature_set=feature_set)
        metrics[f"{feature_set}_three_class_fixed"] = _three_class_metrics(
            class_group,
            threshold=three_class_threshold,
            feature_set=feature_set,
        )

    predictions = pd.concat([regression_predictions, class_predictions], ignore_index=True, sort=False)
    return metrics, predictions.sort_values(["feature_set", "experiment", "week"]).reset_index(drop=True)
