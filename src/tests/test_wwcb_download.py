import pandas as pd

from text.wwcb_download import filter_releases, parse_last_page, parse_release_links


def test_parse_release_links_dedupes_latest_release():
    html = """
    <a href="/sites/default/release-files/795911/wwcb2026.pdf">May 19 2026 - pdf</a>
    <a href="/publication/weekly-weather-and-crop-bulletin/2026-05-19">View</a>
    <a href="/sites/default/release-files/795911/wwcb2026.pdf">Weekly Weather and Crop Bulletin - May 19 2026 - pdf</a>
    <a href="?page=1">Next</a>
    <a href="?page=289">Last</a>
    """

    releases = parse_release_links(html)

    assert len(releases) == 1
    assert releases[0].release_date == "2026-05-19"
    assert releases[0].pdf_filename == "wwcb2026.pdf"
    assert releases[0].pdf_url == "https://esmis.nal.usda.gov/sites/default/release-files/795911/wwcb2026.pdf"


def test_parse_release_links_accepts_older_weather_weekly_filenames():
    html = """
    <a href="/sites/default/release-files/cj82k728n/123/weather_weekly-05-31-2007.pdf">May 31 2007 - pdf</a>
    <a href="/publication/weekly-weather-and-crop-bulletin/2007-05-31">View</a>
    """

    releases = parse_release_links(html)

    assert len(releases) == 1
    assert releases[0].release_date == "2007-05-31"
    assert releases[0].pdf_filename == "weather_weekly-05-31-2007.pdf"


def test_parse_last_page_reads_pagination_links():
    html = '<a href="?page=1">2</a><a href="?page=289">Last</a>'

    assert parse_last_page(html) == 289


def test_filter_releases_uses_inclusive_date_range():
    html = """
    <a href="/sites/default/release-files/a/wwcb1826.pdf">May 05 2026 - pdf</a>
    <a href="/sites/default/release-files/b/wwcb1926.pdf">May 12 2026 - pdf</a>
    <a href="/sites/default/release-files/c/wwcb2026.pdf">May 19 2026 - pdf</a>
    """

    releases = filter_releases(parse_release_links(html), start="2026-05-06", end="2026-05-18")

    assert [pd.Timestamp(item.release_date) for item in releases] == [pd.Timestamp("2026-05-12")]
