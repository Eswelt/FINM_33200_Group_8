"""Time-series validation helpers shared by all modeling tasks."""

from typing import Iterable, Tuple

import pandas as pd


def walk_forward_splits(
    data: pd.DataFrame,
    split_date: str,
    test_window_weeks: int,
    retrain_step_weeks: int,
    validation_scheme: str = "expanding",
    train_window_weeks: int = 260,
    date_column: str = "week",
) -> Iterable[Tuple[int, pd.DataFrame, pd.DataFrame]]:
    """Yield forward-only train/test windows for weekly model validation."""
    if validation_scheme not in {"expanding", "rolling"}:
        raise ValueError(f"Unknown validation scheme: {validation_scheme}")
    if test_window_weeks < 1:
        raise ValueError("test_window_weeks must be positive.")
    if retrain_step_weeks < 1:
        raise ValueError("retrain_step_weeks must be positive.")
    if validation_scheme == "rolling" and train_window_weeks < 1:
        raise ValueError("train_window_weeks must be positive for rolling validation.")
    if date_column not in data.columns:
        raise ValueError(f"Missing validation date column: {date_column}")

    weeks = pd.to_datetime(data[date_column])
    split = pd.Timestamp(split_date)
    test_start = weeks.loc[weeks > split].min()
    if pd.isna(test_start):
        return

    fold = 0
    max_week = weeks.max()
    while test_start <= max_week:
        test_end = test_start + pd.Timedelta(weeks=test_window_weeks - 1)
        if validation_scheme == "rolling":
            train_start = test_start - pd.Timedelta(weeks=train_window_weeks)
            train_mask = (weeks >= train_start) & (weeks < test_start)
        else:
            train_mask = weeks < test_start
        test_mask = (weeks >= test_start) & (weeks <= test_end)

        train = data.loc[train_mask].copy()
        test = data.loc[test_mask].copy()
        if not train.empty and not test.empty:
            yield fold, train, test

        fold += 1
        test_start = test_start + pd.Timedelta(weeks=retrain_step_weeks)
