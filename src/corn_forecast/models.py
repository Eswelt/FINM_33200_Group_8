"""Walk-forward model training for the CORN ETF forecasting project."""

import os
from typing import Dict, Iterable, List, Tuple

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer

from corn_forecast.features import feature_set_columns
from corn_forecast.strategy import backtest_predictions, summarize_backtest


FEATURE_SETS = ("A_price", "B_price_weather", "C_price_weather_text")
ESTIMATORS = ("logit", "hgb")


def _safe_float(value: float) -> float:
    if value is None or pd.isna(value):
        return float("nan")
    return float(value)


def _numeric_pipeline(estimator: str) -> Pipeline:
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if estimator == "logit":
        steps.append(("scaler", StandardScaler()))
    return Pipeline(steps)


def _build_pipeline(estimator: str, numeric_columns: List[str], text_column: str = None) -> Pipeline:
    transformers = []
    if numeric_columns:
        transformers.append(("numeric", _numeric_pipeline(estimator), numeric_columns))
    if text_column:
        transformers.append(
            (
                "text",
                TfidfVectorizer(max_features=30, ngram_range=(1, 2), stop_words="english"),
                text_column,
            )
        )

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop", sparse_threshold=0.0)
    if estimator == "logit":
        model = LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear")
    elif estimator == "hgb":
        model = HistGradientBoostingClassifier(
            learning_rate=0.04,
            max_iter=150,
            max_leaf_nodes=15,
            l2_regularization=0.05,
            random_state=33200,
        )
    else:
        raise ValueError(f"Unknown estimator: {estimator}")

    return Pipeline([("preprocess", preprocessor), ("model", model)])


def _predict_logit_probability(pipeline: Pipeline, x_frame: pd.DataFrame) -> np.ndarray:
    transformed = pipeline.named_steps["preprocess"].transform(x_frame)
    x_matrix = transformed.toarray() if hasattr(transformed, "toarray") else np.asarray(transformed)
    model = pipeline.named_steps["model"]
    coef = np.asarray(model.coef_).ravel()
    intercept = float(model.intercept_[0])

    if not np.isfinite(x_matrix).all():
        raise ValueError("Preprocessed feature matrix contains non-finite values.")
    if not np.isfinite(coef).all() or not np.isfinite(intercept):
        raise ValueError("Fitted logistic regression parameters contain non-finite values.")

    scores = np.clip(x_matrix.dot(coef) + intercept, -35, 35)
    return 1.0 / (1.0 + np.exp(-scores))


def _predict_positive_probability(estimator: str, pipeline: Pipeline, x_frame: pd.DataFrame) -> np.ndarray:
    if estimator == "logit":
        return _predict_logit_probability(pipeline, x_frame)
    probabilities = pipeline.predict_proba(x_frame)[:, 1]
    return np.clip(probabilities, 1e-6, 1 - 1e-6)


def _metric_dict(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    labels_present = set(pd.Series(y_true).dropna().astype(int).unique())
    roc_auc = roc_auc_score(y_true, y_prob) if len(labels_present) == 2 else np.nan
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": _safe_float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": _safe_float(balanced_accuracy_score(y_true, y_pred)),
        "f1": _safe_float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": _safe_float(roc_auc),
        "log_loss": _safe_float(log_loss(y_true, y_prob, labels=[0, 1])),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "n_train": 0,
        "n_test": int(len(y_true)),
    }


def _walk_forward_splits(
    data: pd.DataFrame,
    split_date: str,
    test_window_weeks: int,
    retrain_step_weeks: int,
) -> Iterable[Tuple[int, pd.DataFrame, pd.DataFrame]]:
    """Yield expanding train sets and forward-only test windows."""
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


def train_evaluate(
    panel: pd.DataFrame,
    split_date: str = "2022-12-31",
    test_window_weeks: int = 13,
    retrain_step_weeks: int = 13,
    long_threshold: float = 0.55,
    short_threshold: float = 0.45,
    allow_short: bool = False,
    transaction_cost_bps: float = 5.0,
) -> Tuple[Dict[str, Dict[str, float]], pd.DataFrame]:
    """Train baseline and gradient-boosted classifiers with walk-forward validation."""
    data = panel.copy()
    data = data.replace([np.inf, -np.inf], np.nan)
    data["week"] = pd.to_datetime(data["week"])
    data = data.dropna(subset=["target_up_next"]).copy()
    data["target_up_next"] = data["target_up_next"].astype(int)
    if "report_text" in data.columns:
        data["report_text"] = data["report_text"].fillna("")

    prediction_frames = []
    splits = list(_walk_forward_splits(data, split_date, test_window_weeks, retrain_step_weeks))
    if not splits:
        raise ValueError("Walk-forward split produced no out-of-sample folds.")

    for fold, train, test in splits:
        if train["target_up_next"].nunique() < 2:
            continue
        for feature_set in FEATURE_SETS:
            numeric_columns, text_column = feature_set_columns(data, feature_set)
            if not numeric_columns and text_column is None:
                raise ValueError(f"No usable columns found for {feature_set}.")

            fit_columns = numeric_columns + ([text_column] if text_column else [])
            for estimator in ESTIMATORS:
                model_name = f"{feature_set}_{estimator}"
                pipeline = _build_pipeline(estimator, numeric_columns=numeric_columns, text_column=text_column)
                pipeline.fit(train[fit_columns], train["target_up_next"])

                y_prob = _predict_positive_probability(estimator, pipeline, test[fit_columns])
                y_pred = (y_prob >= 0.5).astype(int)

                prediction_frames.append(
                    pd.DataFrame(
                        {
                            "week": test["week"].to_numpy(),
                            "fold": fold,
                            "feature_set": feature_set,
                            "estimator": estimator,
                            "model": model_name,
                            "y_true": test["target_up_next"].to_numpy(),
                            "y_prob": y_prob,
                            "y_pred": y_pred,
                            "target_log_return_next": test["target_log_return_next"].to_numpy(),
                            "train_start": train["week"].min(),
                            "train_end": train["week"].max(),
                            "n_train": len(train),
                        }
                    )
                )

    if not prediction_frames:
        raise ValueError("No model folds were trained; check split dates and class balance.")

    predictions = pd.concat(prediction_frames, ignore_index=True)
    predictions = backtest_predictions(
        predictions,
        long_threshold=long_threshold,
        short_threshold=short_threshold,
        allow_short=allow_short,
        transaction_cost_bps=transaction_cost_bps,
    )

    strategy_metrics = summarize_backtest(predictions)
    metrics: Dict[str, Dict[str, float]] = {}
    for model, group in predictions.groupby("model"):
        model_metrics = _metric_dict(group["y_true"], group["y_pred"], group["y_prob"])
        model_metrics["n_train_min"] = int(group["n_train"].min())
        model_metrics["n_train_max"] = int(group["n_train"].max())
        model_metrics["n_folds"] = int(group["fold"].nunique())
        model_metrics.update(strategy_metrics[model])
        metrics[model] = model_metrics

    return metrics, predictions.sort_values(["model", "week"]).reset_index(drop=True)
