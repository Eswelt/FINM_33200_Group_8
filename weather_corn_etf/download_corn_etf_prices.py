#!/usr/bin/env python3
"""
Download CORN ETF prices into the CSV format expected by the weather model.

The output CSV is compatible with
test_corn_etf_cfsv2_daily_decision_leadbylead_expanding_yearly.py because it
contains at least these two columns:

    date,close

Run on GLADE/Derecho after installing yfinance in the active environment:

    python download_corn_etf_prices.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SCRIPT_DIR / "weather_data" / "corn_etf_prices.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download CORN ETF prices as a date,close CSV for the weather return script."
    )
    parser.add_argument("--symbol", default="CORN", help="Yahoo Finance ticker. Default: CORN.")
    parser.add_argument("--start", default="2011-01-01", help="Inclusive Yahoo Finance start date.")
    parser.add_argument("--end", default="2026-02-01", help="Exclusive Yahoo Finance end date.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output CSV path.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output CSV if it already exists.",
    )
    return parser.parse_args()


def download_prices(symbol: str, start: str, end: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError(
            "yfinance is required. Install it in the active environment, or run: pip install yfinance"
        ) from exc

    data = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError(f"Yahoo Finance returned no rows for {symbol} from {start} to {end}")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [column[0] for column in data.columns]

    close_col = "Close" if "Close" in data.columns else "Adj Close"
    if close_col not in data.columns:
        raise KeyError(f"Could not find Close or Adj Close in Yahoo Finance columns: {list(data.columns)}")

    reset = data.reset_index()
    date_col = next(
        (column for column in ("Date", "Datetime", "date", "datetime", "index") if column in reset.columns),
        None,
    )
    if date_col is None:
        date_col = reset.columns[0]

    out = reset[[date_col, close_col]].copy()
    out.columns = ["date", "close"]
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna(subset=["date", "close"]).sort_values("date")
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out[["date", "close"]]


def main() -> None:
    args = parse_args()
    output = args.output.expanduser()
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"{output} already exists; pass --overwrite to replace it")

    output.parent.mkdir(parents=True, exist_ok=True)
    prices = download_prices(args.symbol, args.start, args.end)
    prices.to_csv(output, index=False)

    print(f"Wrote {len(prices)} rows to {output}", flush=True)
    print(f"Date range: {prices['date'].iloc[0]} to {prices['date'].iloc[-1]}", flush=True)


if __name__ == "__main__":
    main()
