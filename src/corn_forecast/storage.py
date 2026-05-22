from pathlib import Path
from typing import Iterable

import pandas as pd


DATE_COLUMNS = ("date", "week", "release_date")


def _csv_fallback(path: Path) -> Path:
    return path.with_suffix(".csv") if path.suffix == ".parquet" else path


def coerce_date_columns(df: pd.DataFrame, columns: Iterable[str] = DATE_COLUMNS) -> pd.DataFrame:
    result = df.copy()
    for column in columns:
        if column in result.columns:
            result[column] = pd.to_datetime(result[column])
    return result


def read_table(path: Path) -> pd.DataFrame:
    """Read a parquet table, falling back to a same-stem CSV when needed."""
    actual_path = path
    if not actual_path.exists() and path.suffix == ".parquet":
        actual_path = _csv_fallback(path)
    if not actual_path.exists():
        raise FileNotFoundError(f"Missing table: {path}")

    if actual_path.suffix == ".parquet":
        return coerce_date_columns(pd.read_parquet(actual_path))
    return coerce_date_columns(pd.read_csv(actual_path))


def table_exists(path: Path) -> bool:
    if path.exists():
        return True
    return path.suffix == ".parquet" and _csv_fallback(path).exists()


def write_table(df: pd.DataFrame, path: Path, index: bool = False) -> Path:
    """Write parquet when possible and transparently fall back to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".parquet":
        try:
            df.to_parquet(path, index=index)
            return path
        except (ImportError, ValueError, OSError):
            fallback = _csv_fallback(path)
            df.to_csv(fallback, index=index)
            return fallback

    df.to_csv(path, index=index)
    return path
