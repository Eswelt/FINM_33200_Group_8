from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from gdelt_utils import AI_SCORE_COLUMNS, save_csv


DEFAULT_INPUT = Path("data/interim/gdelt_corn_headlines/scored_compact_all.parquet")
DEFAULT_OUTPUT = Path("data/interim/news_weekly.parquet")


def read_scored(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def choose_date_column(frame: pd.DataFrame) -> str:
    for column in ["gkg_date", "seendate", "week"]:
        if column in frame.columns:
            return column
    raise ValueError("Input must contain one of: gkg_date, seendate, week")


def relevance_weighted_mean(group: pd.DataFrame, score_columns: list[str], weight_column: str) -> pd.Series:
    output: dict[str, float] = {}
    weights = pd.to_numeric(group[weight_column], errors="coerce").fillna(0).clip(lower=0)
    weight_sum = float(weights.sum())

    for column in score_columns:
        values = pd.to_numeric(group[column], errors="coerce")
        if column == weight_column:
            output[column] = float(values.mean()) if values.notna().any() else 0.0
        elif weight_sum > 0:
            output[column] = float((values.fillna(0) * weights).sum() / weight_sum)
        else:
            output[column] = 0.0
    return pd.Series(output)


def aggregate_weekly(
    frame: pd.DataFrame,
    date_column: str | None = None,
    score_columns: list[str] | None = None,
    weight_column: str = "relevance_score",
    min_relevance: float = 0.0,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["week", *(score_columns or AI_SCORE_COLUMNS)])

    date_column = date_column or choose_date_column(frame)
    score_columns = score_columns or [column for column in AI_SCORE_COLUMNS if column in frame.columns]
    missing = [column for column in score_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing score columns: {missing}")
    if weight_column not in frame.columns:
        raise ValueError(f"Missing weight column: {weight_column}")

    result = frame.copy()
    timestamps = pd.to_datetime(result[date_column], errors="coerce", utc=True).dt.tz_convert(None)
    result = result[timestamps.notna()].copy()
    timestamps = timestamps[timestamps.notna()]
    result["week"] = timestamps.dt.to_period("W-SUN").dt.start_time.dt.strftime("%Y-%m-%d")
    for column in score_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result[weight_column] = pd.to_numeric(result[weight_column], errors="coerce").fillna(0)
    if min_relevance > 0:
        result = result[result[weight_column] >= min_relevance].copy()

    weekly = (
        result.groupby("week", sort=True)
        .apply(
            relevance_weighted_mean,
            score_columns=score_columns,
            weight_column=weight_column,
            include_groups=False,
        )
        .reset_index()
    )
    return weekly[["week", *score_columns]]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate article-level GDELT OpenAI scores to Monday-week features."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--csv", type=Path, default=Path("data/interim/news_weekly.csv"))
    parser.add_argument("--date-column", default=None, help="Default auto-picks gkg_date, seendate, then week.")
    parser.add_argument("--weight-column", default="relevance_score")
    parser.add_argument(
        "--min-relevance",
        type=float,
        default=0.0,
        help="Optional row filter before aggregation. Default keeps all rows and uses relevance as weights.",
    )
    args = parser.parse_args()

    scored = read_scored(args.input)
    weekly = aggregate_weekly(
        scored,
        date_column=args.date_column,
        weight_column=args.weight_column,
        min_relevance=args.min_relevance,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.suffix == ".parquet":
        weekly.to_parquet(args.out, index=False)
    else:
        save_csv(weekly, args.out)
    print(f"Wrote {len(weekly)} weekly rows: {args.out}")

    if args.csv is not None:
        save_csv(weekly, args.csv)
        print(f"Wrote CSV: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
