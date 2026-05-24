"""Parser for USDA Weekly Weather and Crop Bulletin PDFs."""

import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd


REPORT_DATE_PATTERN = re.compile(r"\b([A-Z][a-z]+ \d{1,2}, \d{4})\b")
HIGHLIGHTS_RANGE_PATTERN = re.compile(r"\b([A-Z][a-z]+ \d{1,2})\s*[–-]\s*(\d{1,2}),\s*(\d{4})\b")
PAGE_BREAK = "\f"


@dataclass
class WWCBCoreText:
    source_file: str
    report_date: Optional[str]
    week_ending: Optional[str]
    week: Optional[str]
    weather_highlights: str
    national_ag_summary: str
    corn_section: str
    corn_table_text: str
    report_text: str


def pdf_to_text(path: Path) -> str:
    """Extract layout-preserving text from a PDF with poppler's pdftotext."""
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph boundaries enough for LLM input."""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def _remove_page_headers(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^\d+\s+Weekly Weather and Crop Bulletin\s+[A-Z][a-z]+ \d{1,2}, \d{4}$", stripped):
            continue
        if re.match(r"^[A-Z][a-z]+ \d{1,2}, \d{4}\s+Weekly Weather and Crop Bulletin\s+\d+$", stripped):
            continue
        lines.append(line)
    return "\n".join(lines)


def extract_report_date(text: str) -> Optional[pd.Timestamp]:
    first_page = text.split(PAGE_BREAK)[0]
    matches = REPORT_DATE_PATTERN.findall(first_page)
    if not matches:
        return None
    return pd.to_datetime(matches[0], errors="coerce")


def extract_week_ending(text: str, report_date: Optional[pd.Timestamp]) -> Optional[pd.Timestamp]:
    crop_week = re.search(
        r"Crop Progress and Condition\s+Week Ending\s+([A-Z][a-z]+ \d{1,2}, \d{4})",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if crop_week:
        return pd.to_datetime(crop_week.group(1), errors="coerce")
    match = HIGHLIGHTS_RANGE_PATTERN.search(text[:2000])
    if match:
        month_day_start, end_day, year = match.groups()
        month = month_day_start.split()[0]
        return pd.to_datetime(f"{month} {end_day}, {year}", errors="coerce")
    if report_date is not None and not pd.isna(report_date):
        return report_date - pd.Timedelta(days=2)
    return None


def _slice_between(text: str, start_pattern: str, end_patterns: Iterable[str]) -> str:
    start = re.search(start_pattern, text, flags=re.IGNORECASE)
    if not start:
        return ""
    start_idx = start.end()
    end_idx = len(text)
    for pattern in end_patterns:
        end = re.search(pattern, text[start_idx:], flags=re.IGNORECASE)
        if end:
            end_idx = min(end_idx, start_idx + end.start())
    return clean_text(text[start_idx:end_idx])


def extract_weather_highlights(text: str) -> str:
    """Extract the front-page highlights and page-3 continuation."""
    pages = text.split(PAGE_BREAK)
    parts = []
    if pages:
        first_page = _remove_page_headers(pages[0])
        start = re.search(r"\bA\s*\n", first_page)
        end = re.search(r"\(Continued on page 3\)", first_page)
        if start and end:
            front = first_page[start.end(): end.start()]
            cleaned_lines = []
            for line in front.splitlines():
                # Drop the right-hand table-of-contents column when it is present.
                cleaned_lines.append(re.split(r"\s{4,}", line)[0])
            parts.append("\n".join(cleaned_lines))
    if len(pages) >= 3:
        page3 = _remove_page_headers(pages[2])
        start = re.search(r"\(Continued from front cover\)", page3, flags=re.IGNORECASE)
        end = re.search(r"\bAs the week began\b", page3)
        if start and end:
            parts.append(page3[start.end(): end.start()])
    return clean_text("\n\n".join(parts))


def extract_national_ag_summary(text: str) -> str:
    for page in text.split(PAGE_BREAK):
        if "Weekly National Agricultural Summary provided" not in page:
            continue
        page = _remove_page_headers(page)
        start = re.search(r"\bHIGHLIGHTS\b", page)
        if not start:
            continue
        body = page[start.end():]
        return clean_text(body)
    return ""


def extract_corn_section(national_ag_summary: str) -> str:
    match = re.search(r"\bCorn:\s*(.*?5-year average\.)", national_ag_summary, flags=re.DOTALL)
    if match:
        return clean_text(match.group(0))
    match = re.search(
        r"\bCorn:\s*(.*?)(?=\n[A-Z][A-Za-z ]+:\s|\n\s*[A-Z][a-z]+ Grains:|\n\s*Other Crops:|\Z)",
        national_ag_summary,
        flags=re.DOTALL,
    )
    return clean_text(match.group(0)) if match else ""


def extract_corn_section_from_text(text: str) -> str:
    """Extract the left-column Corn paragraph from the National Agricultural Summary page."""
    for page in text.split(PAGE_BREAK):
        if "Weekly National Agricultural Summary provided" not in page:
            continue
        lines = page.splitlines()
        captured = []
        in_corn = False
        for line in lines:
            left_column = re.split(r"\s{2,}", line.strip())[0].strip()
            if not left_column:
                continue
            if left_column.startswith("Corn:"):
                in_corn = True
            elif in_corn and re.match(r"^[A-Z][A-Za-z ]+:", left_column):
                break
            if in_corn:
                captured.append(left_column)
                if "emerged" in " ".join(captured).lower() and "5-year average." in left_column:
                    break
        if captured:
            return clean_text("\n".join(captured))
    return ""


def extract_corn_table_text(text: str) -> str:
    start = re.search(r"Corn Percent Planted", text, flags=re.IGNORECASE)
    if not start:
        return ""
    after = text[start.start():]
    end = re.search(r"Soybeans Percent Planted", after, flags=re.IGNORECASE)
    if end:
        after = after[: end.start()]
    return clean_text(after)


def build_report_text(
    weather_highlights: str,
    national_ag_summary: str,
    corn_section: str,
    corn_table_text: str,
) -> str:
    return clean_text(
        "\n\n".join(
            [
                "[WEATHER HIGHLIGHTS]\n" + weather_highlights,
                "[NATIONAL AGRICULTURAL SUMMARY]\n" + national_ag_summary,
                "[CORN SECTION]\n" + corn_section,
                "[CORN PROGRESS TABLE]\n" + corn_table_text,
            ]
        )
    )


def parse_wwcb_pdf(path: Path) -> WWCBCoreText:
    raw_text = pdf_to_text(path)
    report_date = extract_report_date(raw_text)
    week_ending = extract_week_ending(raw_text, report_date)
    weather_highlights = extract_weather_highlights(raw_text)
    national_ag_summary = extract_national_ag_summary(raw_text)
    corn_section = extract_corn_section_from_text(raw_text) or extract_corn_section(national_ag_summary)
    corn_table_text = extract_corn_table_text(raw_text)
    report_text = build_report_text(weather_highlights, national_ag_summary, corn_section, corn_table_text)
    return WWCBCoreText(
        source_file=str(path),
        report_date=None if report_date is None or pd.isna(report_date) else report_date.strftime("%Y-%m-%d"),
        week_ending=None if week_ending is None or pd.isna(week_ending) else week_ending.strftime("%Y-%m-%d"),
        week=None if week_ending is None or pd.isna(week_ending) else week_ending.to_period("W-FRI").end_time.normalize().strftime("%Y-%m-%d"),
        weather_highlights=weather_highlights,
        national_ag_summary=national_ag_summary,
        corn_section=corn_section,
        corn_table_text=corn_table_text,
        report_text=report_text,
    )


def parse_wwcb_paths(paths: Iterable[Path]) -> pd.DataFrame:
    records: List[dict] = []
    for path in paths:
        records.append(asdict(parse_wwcb_pdf(path)))
    return pd.DataFrame.from_records(records)


def find_pdf_paths(input_path: Path) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.glob("*.pdf"))
