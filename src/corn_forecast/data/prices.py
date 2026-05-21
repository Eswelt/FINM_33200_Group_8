from typing import Optional

import numpy as np
import pandas as pd


PRICE_COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]


def generate_demo_prices(start: str = "2011-01-01", end: Optional[str] = None) -> pd.DataFrame:
    """Create deterministic business-day CORN-like prices for offline smoke tests."""
    if end is None:
        end = pd.Timestamp.today().normalize().strftime("%Y-%m-%d")
    dates = pd.bdate_range(start=start, end=end)
    rng = np.random.default_rng(33200)
    t = np.arange(len(dates))

    seasonal = 0.00045 * np.sin(2 * np.pi * t / 252)
    weather_cycle = 0.00025 * np.sin(2 * np.pi * (t + 30) / 63)
    shocks = rng.normal(0.0, 0.0075, len(dates))
    log_close = np.log(22.0) + np.cumsum(0.00005 + seasonal + weather_cycle + shocks)
    close = np.exp(log_close)

    open_ = close * (1 + rng.normal(0.0, 0.002, len(dates)))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0.002, 0.001, len(dates))))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0.002, 0.001, len(dates))))
    volume = (
        175_000
        + 40_000 * (1 + np.sin(2 * np.pi * t / 252))
        + rng.normal(0, 12_000, len(dates))
    ).clip(min=10_000)

    return pd.DataFrame(
        {
            "date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "adj_close": close,
            "volume": volume.astype(int),
        }
    )


def _flatten_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [column[0] for column in df.columns]
    return df


def normalize_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = _flatten_yfinance_columns(df.copy())
    if "Date" in frame.columns:
        frame = frame.rename(columns={"Date": "date"})
    if "date" not in frame.columns:
        frame = frame.reset_index().rename(columns={"Date": "date", "index": "date"})

    rename_map = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Adj_Close": "adj_close",
        "Volume": "volume",
    }
    frame = frame.rename(columns=rename_map)
    if "adj_close" not in frame.columns and "close" in frame.columns:
        frame["adj_close"] = frame["close"]

    missing = [column for column in PRICE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Price data is missing required columns: {missing}")

    frame = frame[PRICE_COLUMNS].copy()
    frame["date"] = pd.to_datetime(frame["date"]).dt.tz_localize(None)
    return frame.sort_values("date").dropna(subset=["close"])


def fetch_yahoo_prices(symbol: str, start: str, end: Optional[str] = None) -> pd.DataFrame:
    """Fetch daily prices from Yahoo Finance through yfinance."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("Install yfinance or run with --demo to use synthetic prices.") from exc

    raw = yf.download(symbol, start=start, end=end, auto_adjust=False, progress=False)
    if raw.empty:
        raise RuntimeError(f"Yahoo Finance returned no rows for {symbol}.")
    return normalize_price_frame(raw)


def load_prices(symbol: str, start: str, end: Optional[str] = None, demo: bool = False) -> pd.DataFrame:
    if demo:
        return generate_demo_prices(start=start, end=end)
    return fetch_yahoo_prices(symbol=symbol, start=start, end=end)
