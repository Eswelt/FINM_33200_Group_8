"""Download USDA Weekly Weather and Crop Bulletin PDFs from ESMIS."""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://esmis.nal.usda.gov"
PUBLICATION_URL = f"{BASE_URL}/publication/weekly-weather-and-crop-bulletin"
DATE_PATTERN = re.compile(r"\b([A-Z][a-z]{2} [0-9]{2} [0-9]{4}|[A-Z][a-z]+ [0-9]{1,2} [0-9]{4})\b")


@dataclass(frozen=True)
class WWCBRelease:
    release_date: str
    pdf_url: str
    pdf_filename: str
    title: str


def parse_release_date(text: str) -> Optional[pd.Timestamp]:
    match = DATE_PATTERN.search(" ".join(text.split()))
    if not match:
        return None
    return pd.to_datetime(match.group(1), errors="coerce")


def parse_last_page(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    page_numbers = []
    for link in soup.find_all("a", href=True):
        match = re.search(r"[?&]page=(\d+)", link["href"])
        if match:
            page_numbers.append(int(match.group(1)))
    return max(page_numbers) if page_numbers else 0


def parse_release_links(html: str, base_url: str = BASE_URL) -> List[WWCBRelease]:
    soup = BeautifulSoup(html, "html.parser")
    releases: List[WWCBRelease] = []
    seen_urls = set()
    for link in soup.find_all("a", href=True):
        label = " ".join(link.get_text(" ", strip=True).split())
        href = link["href"]
        if ".pdf" not in href.lower() or "wwcb" not in href.lower():
            continue
        release_date = parse_release_date(label)
        if release_date is None or pd.isna(release_date):
            continue
        pdf_url = urljoin(base_url, href)
        if pdf_url in seen_urls:
            continue
        seen_urls.add(pdf_url)
        releases.append(
            WWCBRelease(
                release_date=release_date.strftime("%Y-%m-%d"),
                pdf_url=pdf_url,
                pdf_filename=Path(href).name,
                title=label,
            )
        )
    return releases


def filter_releases(
    releases: Iterable[WWCBRelease],
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> List[WWCBRelease]:
    start_ts = pd.to_datetime(start) if start else None
    end_ts = pd.to_datetime(end) if end else None
    result = []
    for release in releases:
        release_ts = pd.to_datetime(release.release_date)
        if start_ts is not None and release_ts < start_ts:
            continue
        if end_ts is not None and release_ts > end_ts:
            continue
        result.append(release)
    return result


def discover_releases(
    start: Optional[str] = None,
    end: Optional[str] = None,
    max_pages: Optional[int] = None,
    timeout: int = 30,
) -> List[WWCBRelease]:
    session = requests.Session()
    first = session.get(PUBLICATION_URL, timeout=timeout)
    first.raise_for_status()
    last_page = parse_last_page(first.text)
    if max_pages is not None:
        last_page = min(last_page, max_pages - 1)

    all_releases = parse_release_links(first.text)
    for page in range(1, last_page + 1):
        response = session.get(PUBLICATION_URL, params={"page": page}, timeout=timeout)
        response.raise_for_status()
        page_releases = parse_release_links(response.text)
        all_releases.extend(page_releases)

        filtered_so_far = filter_releases(all_releases, start=start, end=end)
        if start and page_releases:
            oldest_on_page = min(pd.to_datetime(item.release_date) for item in page_releases)
            if oldest_on_page < pd.to_datetime(start) and filtered_so_far:
                break

    deduped = {release.pdf_url: release for release in all_releases}
    return sorted(filter_releases(deduped.values(), start=start, end=end), key=lambda item: item.release_date)


def download_releases(
    releases: Iterable[WWCBRelease],
    output_dir: Path,
    overwrite: bool = False,
    dry_run: bool = False,
    sleep_seconds: float = 0.25,
    timeout: int = 60,
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    records = []
    for release in releases:
        path = output_dir / release.pdf_filename
        status = "exists"
        if dry_run:
            status = "dry_run"
        elif overwrite or not path.exists():
            response = session.get(release.pdf_url, timeout=timeout)
            response.raise_for_status()
            path.write_bytes(response.content)
            status = "downloaded"
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        record = asdict(release)
        record["path"] = str(path)
        record["status"] = status
        records.append(record)
    return pd.DataFrame.from_records(records)
