"""Reusable sklearn pipelines for the CORN forecasting experiments."""

from typing import List

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REGRESSION_ESTIMATORS = ("ridge", "hgb")


def _numeric_pipeline(scale: bool) -> Pipeline:
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    return Pipeline(steps)


def build_preprocessor(
    numeric_columns: List[str],
    text_column: str = None,
    scale_numeric: bool = True,
    max_text_features: int = 50,
) -> ColumnTransformer:
    transformers = []
    if numeric_columns:
        transformers.append(("numeric", _numeric_pipeline(scale=scale_numeric), numeric_columns))
    if text_column:
        transformers.append(
            (
                "text",
                TfidfVectorizer(max_features=max_text_features, ngram_range=(1, 2), stop_words="english"),
                text_column,
            )
        )
    if not transformers:
        raise ValueError("At least one numeric or text feature column is required.")
    return ColumnTransformer(transformers=transformers, remainder="drop", sparse_threshold=0.0)


def build_regressor(estimator: str, numeric_columns: List[str], text_column: str = None) -> Pipeline:
    """Build the shared return/volatility regression pipeline."""
    if estimator == "ridge":
        model = Ridge(alpha=1.0)
        scale_numeric = True
    elif estimator == "hgb":
        model = HistGradientBoostingRegressor(
            learning_rate=0.04,
            max_iter=150,
            max_leaf_nodes=15,
            l2_regularization=0.05,
            random_state=33200,
        )
        scale_numeric = False
    else:
        raise ValueError(f"Unknown estimator: {estimator}")

    preprocessor = build_preprocessor(
        numeric_columns=numeric_columns,
        text_column=text_column,
        scale_numeric=scale_numeric,
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def build_three_class_classifier(
    y_train: pd.Series,
    numeric_columns: List[str],
    text_column: str = None,
    max_text_features: int = 50,
) -> Pipeline:
    """Build a class-balanced 3-class classifier with a dummy fallback for one-class folds."""
    preprocessor = build_preprocessor(
        numeric_columns=numeric_columns,
        text_column=text_column,
        scale_numeric=True,
        max_text_features=max_text_features,
    )
    if y_train.nunique() < 2:
        model = DummyClassifier(strategy="most_frequent")
    else:
        model = LogisticRegression(max_iter=1000, class_weight="balanced", solver="lbfgs")
    return Pipeline([("preprocess", preprocessor), ("model", model)])
