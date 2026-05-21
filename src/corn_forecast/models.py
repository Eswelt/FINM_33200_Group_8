from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
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


FEATURE_SETS = ("A_price", "B_price_weather", "C_price_weather_text")


def _safe_float(value: float) -> float:
    if value is None or pd.isna(value):
        return float("nan")
    return float(value)


def _build_pipeline(numeric_columns: List[str], text_column: str = None) -> Pipeline:
    transformers = []
    if numeric_columns:
        numeric_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("numeric", numeric_pipeline, numeric_columns))
    if text_column:
        transformers.append(
            (
                "text",
                TfidfVectorizer(max_features=30, ngram_range=(1, 2), stop_words="english"),
                text_column,
            )
        )

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
    return Pipeline(
        [
            ("preprocess", preprocessor),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear")),
        ]
    )


def _predict_positive_probability(pipeline: Pipeline, x_frame: pd.DataFrame) -> np.ndarray:
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


def train_evaluate(
    panel: pd.DataFrame,
    split_date: str = "2022-12-31",
) -> Tuple[Dict[str, Dict[str, float]], pd.DataFrame]:
    data = panel.copy()
    data = data.replace([np.inf, -np.inf], np.nan)
    data["week"] = pd.to_datetime(data["week"])
    data = data.dropna(subset=["target_up_next"]).copy()
    data["target_up_next"] = data["target_up_next"].astype(int)
    if "report_text" in data.columns:
        data["report_text"] = data["report_text"].fillna("")

    split = pd.Timestamp(split_date)
    train = data[data["week"] <= split].copy()
    test = data[data["week"] > split].copy()
    if train.empty or test.empty:
        raise ValueError("Chronological split produced an empty train or test set.")
    if train["target_up_next"].nunique() < 2:
        raise ValueError("Training set needs both up and down weeks for logistic regression.")

    metrics: Dict[str, Dict[str, float]] = {}
    prediction_frames = []

    for feature_set in FEATURE_SETS:
        numeric_columns, text_column = feature_set_columns(data, feature_set)
        if not numeric_columns and text_column is None:
            raise ValueError(f"No usable columns found for {feature_set}.")

        pipeline = _build_pipeline(numeric_columns=numeric_columns, text_column=text_column)
        fit_columns = numeric_columns + ([text_column] if text_column else [])
        pipeline.fit(train[fit_columns], train["target_up_next"])

        y_prob = _predict_positive_probability(pipeline, test[fit_columns])
        y_pred = (y_prob >= 0.5).astype(int)
        feature_metrics = _metric_dict(test["target_up_next"], y_pred, y_prob)
        feature_metrics["n_train"] = int(len(train))
        metrics[feature_set] = feature_metrics

        prediction_frames.append(
            pd.DataFrame(
                {
                    "week": test["week"].to_numpy(),
                    "model": feature_set,
                    "y_true": test["target_up_next"].to_numpy(),
                    "y_prob": y_prob,
                    "y_pred": y_pred,
                    "target_log_return_next": test["target_log_return_next"].to_numpy(),
                }
            )
        )

    return metrics, pd.concat(prediction_frames, ignore_index=True)
