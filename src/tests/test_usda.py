import pandas as pd

from data.usda import build_weekly_text_features, parse_usda_listing


def test_parse_usda_listing_extracts_txt_release_links():
    html = """
    <html><body>
      <a href="/publication/crop-progress/2024/05/crop-progress-may-20-2024.txt">May 20 2024 - txt</a>
      <a href="/publication/crop-progress/2024/05/crop-progress-may-20-2024.pdf">May 20 2024 - pdf</a>
    </body></html>
    """

    releases = parse_usda_listing(html, "https://esmis.nal.usda.gov/publication/crop-progress", "crop_progress")

    assert len(releases) == 1
    assert releases.loc[0, "publication"] == "crop_progress"
    assert releases.loc[0, "release_date"] == pd.Timestamp("2024-05-20")
    assert releases.loc[0, "url"].endswith("crop-progress-may-20-2024.txt")


def test_weekly_text_features_align_to_friday_week():
    releases = pd.DataFrame(
        {
            "release_date": [pd.Timestamp("2024-05-20")],
            "publication": ["crop_progress"],
            "title": ["Demo"],
            "url": ["demo://report"],
            "text": ["Corn planting rain drought yield yield"],
        }
    )

    weekly = build_weekly_text_features(releases)

    assert weekly.loc[0, "week"] == pd.Timestamp("2024-05-24")
    assert weekly.loc[0, "text_kw_yield"] == 2
    assert weekly.loc[0, "text_kw_rain"] == 1
