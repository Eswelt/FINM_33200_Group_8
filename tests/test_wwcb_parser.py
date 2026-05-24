from pathlib import Path

import pandas as pd

from corn_forecast.text.wwcb import (
    align_report_week,
    build_report_text,
    extract_corn_section_from_text,
    extract_report_date,
    extract_week_ending,
    find_pdf_paths,
)


def test_wwcb_dates_prefer_crop_progress_week_ending():
    text = """
Volume 113, No. 20                                           May 19, 2026
HIGHLIGHTS
May 10 - 16, 2026

Weather Data for the Week Ending May 16, 2026

Crop Progress and Condition
Week Ending May 17, 2026
"""

    report_date = extract_report_date(text)
    week_ending = extract_week_ending(text, report_date)

    assert report_date == pd.Timestamp("2026-05-19")
    assert week_ending == pd.Timestamp("2026-05-17")


def test_report_week_aligns_to_report_release_week():
    report_date = pd.Timestamp("2026-05-19")
    week_ending = pd.Timestamp("2026-05-17")

    assert align_report_week(report_date, week_ending) == pd.Timestamp("2026-05-22")


def test_extract_corn_section_uses_left_column_only():
    text = """
National Agricultural Summary
Weekly National Agricultural Summary provided by USDA/NASS
HIGHLIGHTS

Corn: By May 17, producers had planted 76 percent of the           the nation's rice acreage was rated in good to excellent
nation's corn crop, equal to last year but 6 percentage points     condition, 1 percentage point above last week
ahead of the 5-year average. Thirty-nine percent of the corn
acreage had emerged by May 17, eight percentage points
behind last year but 2 points ahead of the 5-year average.         Small Grains: Producers had seeded oats
Soybeans: Sixty-seven percent of the soybean crop had been planted.
"""

    corn_section = extract_corn_section_from_text(text)

    assert corn_section.startswith("Corn: By May 17")
    assert "rice acreage" not in corn_section
    assert "Small Grains" not in corn_section
    assert "Soybeans" not in corn_section


def test_report_text_excludes_full_national_ag_summary():
    report_text = build_report_text(
        weather_highlights="Dryness expanded across the Corn Belt.",
        national_ag_summary="Soybeans: this full paragraph should remain out of the LLM input.",
        corn_section="Corn: Planting was ahead of average.",
        corn_table_text="Corn Percent Planted table.",
    )

    assert "[WEATHER HIGHLIGHTS]" in report_text
    assert "[CORN SECTION]" in report_text
    assert "[CORN PROGRESS TABLE]" in report_text
    assert "[NATIONAL AGRICULTURAL SUMMARY]" not in report_text
    assert "Soybeans:" not in report_text


def test_find_pdf_paths_accepts_file_and_folder(tmp_path: Path):
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    other = tmp_path / "notes.txt"
    first.touch()
    second.touch()
    other.touch()

    assert find_pdf_paths(first) == [first]
    assert find_pdf_paths(tmp_path) == [first, second]
