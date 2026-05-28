"""Weekly volatility forecasting experiments for CORN ETF."""

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, mean_absolute_error, mean_squared_error, r2_score

from corn_forecast.expected_return_strategy import ESTIMATORS, FEATURE_SETS, _regressor, _walk_forward_splits
from corn_forecast.features import pipeline_feature_columns


HIGH_VOL_QUANTILE = 0.70


def add_next_week_volatility_target(panel: pd.DataFrame) -> pd.DataFrame:
    """Use next-week absolute log return as a weekly realized-volatility proxy."""
    frame = panel.copy()
    frame["target_abs_return_next"] = frame["target_log_return_next"].abs()
    return frame


def add_horizon_targets(panel: pd.DataFrame, horizon_weeks: int) -> pd.DataFrame:
    """Add cumulative-return and realized-volatility targets for a forward horizon."""
    if horizon_weeks < 1:
        raise ValueError("horizon_weeks must be positive.")

    frame = panel.copy()
    future_returns = pd.concat(
        [
            frame["price_log_return"].shift(-offset).rename(f"future_return_{offset}w")
            for offset in range(1, horizon_weeks + 1)
        ],
        axis=1,
    )
    frame["target_log_return_next"] = future_returns.sum(axis=1, min_count=horizon_weeks)
    if horizon_weeks == 1:
        frame["target_realized_vol_next"] = frame["target_log_return_next"].abs()
    else:
        frame["target_realized_vol_next"] = np.sqrt((future_returns.pow(2)).sum(axis=1, min_count=horizon_weeks))
    return frame


def _volatility_metrics(group: pd.DataFrame) -> Dict[str, float]:
    y_true = group["target_abs_return_next"]
    y_pred = group["predicted_abs_return_next"]
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "spearman_corr": float(y_true.corr(y_pred, method="spearman")),
        "mean_actual_volatility": float(y_true.mean()),
        "mean_predicted_volatility": float(y_pred.mean()),
        "high_vol_accuracy": float(accuracy_score(group["y_true_high_vol"], group["y_pred_high_vol"])),
        "high_vol_balanced_accuracy": float(
            balanced_accuracy_score(group["y_true_high_vol"], group["y_pred_high_vol"])
        ),
        "high_vol_rate_actual": float(group["y_true_high_vol"].mean()),
        "high_vol_rate_predicted": float(group["y_pred_high_vol"].mean()),
    }


def evaluate_volatility_forecast(
    panel: pd.DataFrame,
    feature_sets: Iterable[str] = FEATURE_SETS,
    estimators: Iterable[str] = ESTIMATORS,
    split_date: str = "2022-12-31",
    test_window_weeks: int = 13,
    retrain_step_weeks: int = 13,
    validation_scheme: str = "expanding",
    train_window_weeks: int = 260,
    high_vol_quantile: float = HIGH_VOL_QUANTILE,
    target_column: str = "target_abs_return_next",
    target_name: str = "next_week_abs_log_return",
) -> Tuple[Dict[str, Dict[str, float]], pd.DataFrame]:
    """Forecast next-week absolute return and classify high-volatility weeks."""
    if not 0 < high_vol_quantile < 1:
        raise ValueError("high_vol_quantile must be between 0 and 1.")

    data = panel.copy()
    if target_column == "target_abs_return_next" and target_column not in data.columns:
        data = add_next_week_volatility_target(data)
    data["week"] = pd.to_datetime(data["week"])
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna(subset=["target_log_return_next", target_column]).copy()
    if "report_text" in data.columns:
        data["report_text"] = data["report_text"].fillna("")

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
        numeric_columns, text_column = pipeline_feature_columns(data, feature_set)
        columns = numeric_columns + ([text_column] if text_column else [])
        if not columns:
            raise ValueError(f"No usable columns found for {feature_set}.")
        for estimator in estimators:
            for fold, train, test in splits:
                model = _regressor(estimator, numeric_columns=numeric_columns, text_column=text_column)
                model.fit(train[columns], train[target_column])
                predicted = np.maximum(model.predict(test[columns]), 0.0)
                threshold = float(train[target_column].quantile(high_vol_quantile))
                prediction_frames.append(
                    pd.DataFrame(
                        {
                            "week": test["week"].to_numpy(),
                            "fold": fold,
                            "feature_set": feature_set,
                            "estimator": estimator,
                            "model": f"{feature_set}_{estimator}",
                            "target_log_return_next": test["target_log_return_next"].to_numpy(),
                            "target_abs_return_next": test[target_column].to_numpy(),
                            "predicted_abs_return_next": predicted,
                            "high_vol_threshold": threshold,
                            "y_true_high_vol": (test[target_column].to_numpy() >= threshold).astype(int),
                            "y_pred_high_vol": (predicted >= threshold).astype(int),
                            "train_start": train["week"].min(),
                            "train_end": train["week"].max(),
                            "n_train": len(train),
                        }
                    )
                )

    predictions = pd.concat(prediction_frames, ignore_index=True)
    metrics: Dict[str, Dict[str, float]] = {}
    for model, group in predictions.groupby("model"):
        values = {
            "target": target_name,
            "feature_set": group["feature_set"].iloc[0],
            "estimator": group["estimator"].iloc[0],
            "validation_scheme": validation_scheme,
            "train_window_weeks": int(train_window_weeks) if validation_scheme == "rolling" else None,
            "high_vol_quantile": float(high_vol_quantile),
            "n_test": int(len(group)),
            "n_folds": int(group["fold"].nunique()),
            **_volatility_metrics(group),
        }
        metrics[model] = values

    return metrics, predictions.sort_values(["model", "week"]).reset_index(drop=True)
