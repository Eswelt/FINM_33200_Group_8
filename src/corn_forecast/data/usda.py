"""Optional USDA text adapter.

The main forecasting pipelines do not require this module. Teammates can
instead provide weekly text/AI feature tables under `data/interim/` following
`pipeline_contract.md`.
"""

import re
from typing import Iterable, List, Optional
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup


CROP_PROGRESS_URL = "https://esmis.nal.usda.gov/publication/crop-progress"
WEEKLY_BULLETIN_URL = "https://esmis.nal.usda.gov/publication/weekly-weather-and-crop-bulletin"

DATE_PATTERN = re.compile(r"([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})")
TEXT_KEYWORDS = ("drought", "rain", "heat", "planting", "harvest", "yield", "export", "ethanol")


def parse_usda_listing(html: str, base_url: str, publication: str) -> pd.DataFrame:
    """Parse USDA ESMIS listing pages and return downloadable txt releases."""
    soup = BeautifulSoup(html, "html.parser")
    records: List[dict] = []
    for anchor in soup.find_all("a", href=True):
        label = " ".join(anchor.get_text(" ", strip=True).split())
        href = anchor["href"]
        if "txt" not in label.lower() and not href.lower().endswith(".txt"):
            continue

        match = DATE_PATTERN.search(label)
        if not match:
            match = DATE_PATTERN.search(href.replace("-", " "))
        if not match:
            continue

        release_date = pd.to_datetime(match.group(1), errors="coerce")
        if pd.isna(release_date):
            continue

        records.append(
            {
                "release_date": release_date.normalize(),
                "publication": publication,
                "title": label,
                "url": urljoin(base_url, href),
            }
        )

    return pd.DataFrame.from_records(records).drop_duplicates(subset=["url"]).sort_values("release_date")


def download_report_text(url: str, timeout: int = 30) -> str:
    import requests

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_usda_releases(limit_per_source: int = 80) -> pd.DataFrame:
    import requests

    records = []
    for publication, url in (
        ("crop_progress", CROP_PROGRESS_URL),
        ("weekly_weather_crop_bulletin", WEEKLY_BULLETIN_URL),
    ):
        page = requests.get(url, timeout=30)
        page.raise_for_status()
        listing = parse_usda_listing(page.text, url, publication).tail(limit_per_source)
        for row in listing.itertuples(index=False):
            records.append(
                {
                    "release_date": row.release_date,
                    "publication": row.publication,
                    "title": row.title,
                    "url": row.url,
                    "text": download_report_text(row.url),
                }
            )
    return pd.DataFrame.from_records(records).sort_values(["release_date", "publication"])


def generate_demo_usda_releases(start: str = "2011-01-01", end: Optional[str] = None) -> pd.DataFrame:
    if end is None:
        end = pd.Timestamp.today().normalize().strftime("%Y-%m-%d")
    dates = pd.date_range(start=start, end=end, freq="W-TUE")
    templates = [
        "Crop progress notes corn planting pace, yield condition, and harvest delays.",
        "Weekly weather bulletin highlights rain, drought, heat, and soil moisture across the Corn Belt.",
        "Markets discuss export demand, ethanol use, and crop ratings for corn.",
    ]
    records = []
    for idx, release_date in enumerate(dates):
        month = release_date.month
        seasonal_phrase = "planting" if month in (4, 5) else "harvest" if month in (9, 10, 11) else "yield"
        stress_phrase = "drought heat" if month in (7, 8) else "rain soil moisture"
        for publication in ("crop_progress", "weekly_weather_crop_bulletin"):
            records.append(
                {
                    "release_date": release_date,
                    "publication": publication,
                    "title": f"Demo USDA {publication} {release_date:%Y-%m-%d}",
                    "url": "demo://usda",
                    "text": f"{templates[idx % len(templates)]} Corn Belt {seasonal_phrase} {stress_phrase}.",
                }
            )
    return pd.DataFrame.from_records(records)


def release_week(release_dates: Iterable[pd.Timestamp]) -> pd.Series:
    dates = pd.to_datetime(pd.Series(release_dates))
    return dates.dt.to_period("W-FRI").dt.end_time.dt.normalize()


def build_weekly_text_features(releases: pd.DataFrame) -> pd.DataFrame:
    if releases.empty:
        return pd.DataFrame(columns=["week", "report_text"] + [f"text_kw_{kw}" for kw in TEXT_KEYWORDS])

    frame = releases.copy()
    frame["release_date"] = pd.to_datetime(frame["release_date"])
    frame["week"] = release_week(frame["release_date"])
    frame["text"] = frame["text"].fillna("")
    grouped = (
        frame.groupby("week", as_index=False)
        .agg(report_text=("text", " ".join), report_count=("text", "size"))
        .sort_values("week")
    )
    lower_text = grouped["report_text"].str.lower()
    for keyword in TEXT_KEYWORDS:
        grouped[f"text_kw_{keyword}"] = lower_text.str.count(rf"\b{re.escape(keyword)}\b")
    return grouped


def load_usda_releases(start: str, end: Optional[str] = None, demo: bool = False) -> pd.DataFrame:
    if demo:
        return generate_demo_usda_releases(start=start, end=end)
    return fetch_usda_releases()
