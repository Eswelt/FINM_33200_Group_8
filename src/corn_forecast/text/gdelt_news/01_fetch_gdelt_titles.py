from __future__ import annotations

import argparse
import html
import os
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.parse import unquote, urlparse

import pandas as pd

from gdelt_utils import article_id, friday_week, load_env_file, save_csv

if TYPE_CHECKING:
    from google.cloud import bigquery


GDELT_BQ_TABLE = "gdelt-bq.gdeltv2.gkg_partitioned"
DEFAULT_START_DATE = "2015-02-01"
DEFAULT_OUTPUT_DIR = Path("data/interim/gdelt_corn_headlines")
DEFAULT_SAMPLE_MONTH = "2025-01"
DEFAULT_KEYWORDS = [
    "corn",
    "maize",
    "usda",
    "ethanol",
    "biofuel",
    "drought",
    "harvest",
    "planting",
    "yield",
    "crop",
    "grain",
    "farm",
    "soybean",
]
DEFAULT_REQUIRED_KEYWORDS = [
    "corn",
    "maize",
    "ethanol",
]
DEFAULT_WEATHER_KEYWORDS = [
    "drought",
    "heat",
    "heat wave",
    "flood",
    "flooding",
    "rain",
    "rainfall",
    "dry weather",
    "dryness",
    "soil moisture",
    "planting",
    "harvest",
    "yield",
    "crop condition",
    "crop conditions",
]
DEFAULT_AG_CONTEXT_KEYWORDS = [
    "crop",
    "crops",
    "farm",
    "farmer",
    "farmers",
    "agriculture",
    "agricultural",
    "grain",
    "grains",
    "corn belt",
    "iowa",
    "illinois",
    "nebraska",
    "minnesota",
    "indiana",
    "ohio",
    "kansas",
    "missouri",
    "wisconsin",
]
DEFAULT_EXCLUDE_TERMS = [
    "cornwall",
    "cornell",
    "unicorn",
    "acorn",
    "cornhuskers",
    "cornhole",
    "cornucopia",
    "popcorn",
]
DEFAULT_US_LOCATIONS = [
    "united states",
    "iowa",
    "illinois",
    "nebraska",
    "minnesota",
    "indiana",
    "ohio",
    "south dakota",
    "north dakota",
    "missouri",
    "kansas",
    "wisconsin",
    "michigan",
]


def bigquery_module():
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "Install BigQuery dependencies first: pip install -r requirements.txt"
        ) from exc
    return bigquery


def extract_page_title(extras: Optional[str]) -> Optional[str]:
    if extras is None:
        return None
    match = re.search(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", extras, flags=re.DOTALL)
    if not match:
        return None
    return html.unescape(match.group(1)).strip()


def title_from_url_slug(url: Optional[str]) -> Optional[str]:
    if not url or pd.isna(url):
        return None
    path = urlparse(str(url)).path.rstrip("/")
    if not path:
        return None
    slug = Path(path).name
    slug = re.sub(r"\.(html?|php|aspx?)$", "", slug, flags=re.IGNORECASE)
    slug = unquote(slug)
    slug = re.sub(r"[_\-]+", " ", slug)
    slug = re.sub(r"\s+", " ", slug).strip()
    if len(slug) < 8 or not re.search(r"[A-Za-z]", slug):
        return None
    return slug


def clean_headline_tail(title: Optional[str]) -> Optional[str]:
    """Remove feed/article ids that often appear at the end of URL-derived titles."""
    if title is None or pd.isna(title):
        return None
    cleaned = html.unescape(str(title))
    cleaned = cleaned.replace("%20", " ")
    cleaned = unquote(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Reuters/wire suffixes: idUSKBN1FL5ZJ, idUKL4N1PV1C8, idINL4N1PR1GN.
    cleaned = re.sub(r"\s+id[A-Z]{2,}[A-Z0-9]+$", "", cleaned, flags=re.IGNORECASE)

    # Feed timestamp/id suffixes: 20180205 00011, 2018 02 05, etc.
    cleaned = re.sub(r"\s+20\d{6}\s+\d{3,}$", "", cleaned)
    cleaned = re.sub(r"\s+20\d{2}\s+\d{2}\s+\d{2}$", "", cleaned)

    # Long trailing article ids from publisher URLs.
    cleaned = re.sub(r"\s+\d{6,}$", "", cleaned)

    return re.sub(r"\s+", " ", cleaned).strip()


def month_start_end(month: str) -> tuple[str, str]:
    dt = datetime.strptime(month, "%Y-%m").date()
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)
    return dt.strftime("%Y-%m-%d"), next_month.strftime("%Y-%m-%d")


def generate_month_ranges(start_date: str, end_date: str):
    current = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    while current < end:
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1, day=1)
        else:
            next_month = current.replace(month=current.month + 1, day=1)
        month_end = min(next_month, end)
        yield current.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")
        current = next_month


def hive_partition_path(output_dir: Path, month_start: str) -> Path:
    return output_dir / f"year={month_start[:4]}" / f"month={month_start[5:7]}" / "data.parquet"


def sql_string_list(values: list[str]) -> str:
    return ", ".join("'" + value.replace("'", "\\'").lower() + "'" for value in values)


def regex_alternation(values: list[str]) -> str:
    escaped = [re.escape(value.lower()).replace(r"\ ", " ") for value in values if value]
    return "|".join(escaped)


def build_corn_bigquery_sql(
    month_start: str,
    month_end: str,
    keywords: list[str],
    us_locations: list[str],
    required_keywords: list[str],
    weather_keywords: list[str],
    ag_context_keywords: list[str],
    exclude_terms: list[str],
    mode: str = "expanded",
    allow_url_slug_fallback: bool = False,
    limit: Optional[int] = None,
) -> str:
    if mode not in {"direct", "expanded"}:
        raise ValueError(f"Unknown mode: {mode}")
    limit_clause = "" if limit is None else f"\nLIMIT {int(limit)}"
    keyword_regex = regex_alternation(keywords)
    required_regex = regex_alternation(required_keywords)
    weather_regex = regex_alternation(weather_keywords)
    ag_context_regex = regex_alternation(ag_context_keywords)
    exclude_regex = regex_alternation(exclude_terms)
    if mode == "direct":
        match_condition = f"REGEXP_CONTAINS(headline_text, r'\\b({required_regex})\\b')"
    else:
        match_condition = f"""
        (
            REGEXP_CONTAINS(headline_text, r'\\b({required_regex})\\b')
            OR (
                REGEXP_CONTAINS(headline_text, r'\\b({weather_regex})\\b')
                AND REGEXP_CONTAINS(search_text, r'\\b({ag_context_regex})\\b')
            )
        )
        """
    headline_expression = (
        "COALESCE(REGEXP_EXTRACT(Extras, r'<PAGE_TITLE>(.*?)</PAGE_TITLE>'), "
        "REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_EXTRACT(DocumentIdentifier, r'/([^/?#]+)(?:[?#].*)?$'), "
        "r'\\.(html?|php|aspx?)$', ''), r'[-_]+', ' '), r'\\s+', ' '))"
        if allow_url_slug_fallback
        else "REGEXP_EXTRACT(Extras, r'<PAGE_TITLE>(.*?)</PAGE_TITLE>')"
    )
    page_title_filter = "" if allow_url_slug_fallback else "AND Extras LIKE '%<PAGE_TITLE>%'"
    return f"""
    WITH base AS (
        SELECT
            PARSE_TIMESTAMP('%E4Y%m%d%H%M%S', CAST(DATE AS STRING)) AS gkg_date,
            DocumentIdentifier AS source_url,
            SourceCommonName AS source_name,
            {headline_expression} AS headline_raw,
            Extras,
            V2Tone,
            V2Themes,
            V2Locations
        FROM `{GDELT_BQ_TABLE}`
        WHERE _PARTITIONTIME >= TIMESTAMP('{month_start}')
          AND _PARTITIONTIME < TIMESTAMP('{month_end}')
          {page_title_filter}
          AND TranslationInfo IS NULL
    ),
    titled AS (
        SELECT *,
            LOWER(CONCAT(IFNULL(headline_raw, ''), ' ', IFNULL(V2Themes, ''), ' ', IFNULL(source_url, ''))) AS search_text,
            LOWER(IFNULL(headline_raw, '')) AS headline_text,
            LOWER(IFNULL(V2Locations, '')) AS location_text
        FROM base
        WHERE headline_raw IS NOT NULL
          AND TRIM(headline_raw) != ''
    ),
    filtered AS (
        SELECT *,
            CASE
                WHEN REGEXP_CONTAINS(headline_text, r'\\b({required_regex})\\b') THEN 'direct_corn'
                WHEN REGEXP_CONTAINS(headline_text, r'\\b({weather_regex})\\b')
                  AND REGEXP_CONTAINS(search_text, r'\\b({ag_context_regex})\\b') THEN 'weather_ag'
                ELSE 'other'
            END AS match_type
        FROM titled
        WHERE {match_condition}
          AND REGEXP_CONTAINS(search_text, r'\\b({keyword_regex})\\b')
          AND NOT REGEXP_CONTAINS(headline_text, r'\\b({exclude_regex})\\b')
          AND EXISTS (
                SELECT 1
                FROM UNNEST([{sql_string_list(us_locations)}]) AS loc
                WHERE location_text LIKE CONCAT('%', loc, '%')
            )
    )
    SELECT DISTINCT
        gkg_date,
        source_url,
        source_name,
        match_type,
        headline_raw,
        Extras,
        V2Tone AS v2tone,
        V2Themes AS v2themes,
        V2Locations AS v2locations
    FROM filtered
    ORDER BY gkg_date
    {limit_clause}
    """


def clean_bigquery_headlines(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "article_id",
                "gkg_date",
                "seendate",
                "week",
                "headline",
                "title",
                "source_url",
                "url",
                "source_name",
                "domain",
                "v2tone",
                "v2themes",
                "v2locations",
                "match_type",
            ]
        )
    result = frame.copy()
    if "headline_raw" in result.columns:
        result["headline"] = result["headline_raw"].map(clean_headline_tail)
        result = result.drop(columns=["headline_raw"])
    else:
        result["headline"] = result["Extras"].map(extract_page_title).map(clean_headline_tail)
    result = result.drop(columns=["Extras"])
    result = result.dropna(subset=["headline", "gkg_date"])
    result["headline"] = result["headline"].astype(str).str.strip()
    result = result[result["headline"] != ""].copy()
    result = result.sort_values("gkg_date").drop_duplicates(subset=["headline"], keep="first")
    result["title"] = result["headline"]
    result["url"] = result["source_url"]
    result["domain"] = result["source_name"]
    result["seendate"] = pd.to_datetime(result["gkg_date"], errors="coerce")
    result["week"] = result["seendate"].map(friday_week)
    result["article_id"] = [
        article_id(str(url), str(title))
        for url, title in zip(result["source_url"], result["headline"])
    ]
    ordered = [
        "article_id",
        "gkg_date",
        "seendate",
        "week",
        "headline",
        "title",
        "source_url",
        "url",
        "source_name",
        "domain",
        "match_type",
        "v2tone",
        "v2themes",
        "v2locations",
    ]
    return result[ordered].reset_index(drop=True)


def query_bigquery_month(
    client: "bigquery.Client",
    month_start: str,
    month_end: str,
    keywords: list[str],
    us_locations: list[str],
    required_keywords: list[str],
    weather_keywords: list[str],
    ag_context_keywords: list[str],
    exclude_terms: list[str],
    mode: str = "expanded",
    allow_url_slug_fallback: bool = False,
    limit: Optional[int] = None,
    dry_run: bool = False,
) -> tuple[pd.DataFrame, int]:
    bigquery = bigquery_module()
    sql = build_corn_bigquery_sql(
        month_start=month_start,
        month_end=month_end,
        keywords=keywords,
        us_locations=us_locations,
        limit=limit,
        required_keywords=required_keywords,
        weather_keywords=weather_keywords,
        ag_context_keywords=ag_context_keywords,
        exclude_terms=exclude_terms,
        mode=mode,
        allow_url_slug_fallback=allow_url_slug_fallback,
    )
    job_config = None
    if dry_run:
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    job = client.query(sql, job_config=job_config)
    if dry_run:
        return pd.DataFrame(), int(job.total_bytes_processed or 0)
    rows = job.result()
    frame = rows.to_dataframe()
    return clean_bigquery_headlines(frame), int(job.total_bytes_processed or 0)


def pull_month(
    month: str,
    project: str,
    output_dir: Path,
    keywords: list[str],
    us_locations: list[str],
    required_keywords: list[str],
    weather_keywords: list[str],
    ag_context_keywords: list[str],
    exclude_terms: list[str],
    mode: str = "expanded",
    allow_url_slug_fallback: bool = False,
    limit: Optional[int] = None,
    overwrite: bool = False,
) -> int:
    month_start, month_end = month_start_end(month)
    out_path = hive_partition_path(output_dir, month_start)
    if out_path.exists() and not overwrite:
        print(f"{out_path} already exists. Use --overwrite to re-pull.")
        return 0

    bigquery = bigquery_module()
    client = bigquery.Client(project=project)
    print(f"Querying GDELT BigQuery for {month} ({month_start} to {month_end})...")
    frame, bytes_processed = query_bigquery_month(
        client=client,
        month_start=month_start,
        month_end=month_end,
        keywords=keywords,
        us_locations=us_locations,
        required_keywords=required_keywords,
        weather_keywords=weather_keywords,
        ag_context_keywords=ag_context_keywords,
        exclude_terms=exclude_terms,
        mode=mode,
        allow_url_slug_fallback=allow_url_slug_fallback,
        limit=limit,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out_path, index=False)
    csv_path = out_path.with_suffix(".csv")
    save_csv(frame, csv_path)
    print(f"Rows after title extraction/cleaning: {len(frame):,}")
    print(f"BigQuery bytes processed: {bytes_processed / 1e9:.2f} GB")
    print(f"Saved parquet: {out_path}")
    print(f"Saved csv: {csv_path}")
    return len(frame)


def pull_range(
    start_date: str,
    end_date: str,
    project: str,
    output_dir: Path,
    keywords: list[str],
    us_locations: list[str],
    required_keywords: list[str],
    weather_keywords: list[str],
    ag_context_keywords: list[str],
    exclude_terms: list[str],
    mode: str = "expanded",
    allow_url_slug_fallback: bool = False,
    limit: Optional[int] = None,
    overwrite: bool = False,
) -> None:
    ranges = list(generate_month_ranges(start_date, end_date))
    print(f"Pulling {len(ranges)} months from {start_date} to {end_date}.")
    for idx, (month_start, month_end) in enumerate(ranges, 1):
        month = month_start[:7]
        out_path = hive_partition_path(output_dir, month_start)
        if out_path.exists() and not overwrite:
            print(f"[{idx}/{len(ranges)}] {month}: already exists, skipping")
            continue
        print(f"[{idx}/{len(ranges)}] {month}")
        t0 = time.time()
        pull_month(
            month=month,
            project=project,
            output_dir=output_dir,
            keywords=keywords,
            us_locations=us_locations,
            required_keywords=required_keywords,
            weather_keywords=weather_keywords,
            ag_context_keywords=ag_context_keywords,
            exclude_terms=exclude_terms,
            mode=mode,
            allow_url_slug_fallback=allow_url_slug_fallback,
            limit=limit,
            overwrite=overwrite,
        )
        print(f"Elapsed: {time.time() - t0:.1f}s\n")


def estimate_range(
    start_date: str,
    end_date: str,
    project: str,
    keywords: list[str],
    us_locations: list[str],
    required_keywords: list[str],
    weather_keywords: list[str],
    ag_context_keywords: list[str],
    exclude_terms: list[str],
    mode: str,
    allow_url_slug_fallback: bool,
) -> None:
    ranges = list(generate_month_ranges(start_date, end_date))
    if not ranges:
        print("No months to estimate.")
        return
    sample_ranges = [ranges[0], ranges[len(ranges) // 2], ranges[-1]]
    seen = set()
    sample_ranges = [item for item in sample_ranges if not (item in seen or seen.add(item))]
    bigquery = bigquery_module()
    client = bigquery.Client(project=project)
    total_bytes = 0
    print(f"Estimating {len(ranges)} months using {len(sample_ranges)} dry-run query samples...")
    for month_start, month_end in sample_ranges:
        _, bytes_processed = query_bigquery_month(
            client=client,
            month_start=month_start,
            month_end=month_end,
            keywords=keywords,
            us_locations=us_locations,
            required_keywords=required_keywords,
            weather_keywords=weather_keywords,
            ag_context_keywords=ag_context_keywords,
            exclude_terms=exclude_terms,
            mode=mode,
            allow_url_slug_fallback=allow_url_slug_fallback,
            dry_run=True,
        )
        total_bytes += bytes_processed
        print(f"  {month_start[:7]}: {bytes_processed / 1e9:.2f} GB")
    avg_bytes = total_bytes / len(sample_ranges)
    est_tb = avg_bytes * len(ranges) / 1e12
    print(f"Estimated scan: {est_tb:.2f} TB for {len(ranges)} months.")


def parse_csv_list(value: Optional[str], default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def project_from_env_or_arg(project: Optional[str]) -> str:
    load_env_file()
    resolved = project or os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    resolved = "" if resolved is None else resolved.strip()
    if not resolved:
        raise RuntimeError(
            "Set --project, GCP_PROJECT, or GOOGLE_CLOUD_PROJECT before running BigQuery. "
            "For example, add GCP_PROJECT=your-google-cloud-project-id to the .env file."
        )
    if resolved in {"your-google-cloud-project", "your-google-cloud-project-id"}:
        raise RuntimeError("Replace the placeholder GCP_PROJECT value with your real Google Cloud project id.")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch historical corn-related GDELT GKG titles from BigQuery.")
    parser.add_argument("--project", default=None, help="Google Cloud project id.")
    parser.add_argument("--month", default=DEFAULT_SAMPLE_MONTH, help="Single YYYY-MM month to pull.")
    parser.add_argument("--start", default=DEFAULT_START_DATE, help="Start date for --full.")
    parser.add_argument("--end", default=None, help="End date for --full; default is today.")
    parser.add_argument("--full", action="store_true", help="Pull all months from --start to --end.")
    parser.add_argument("--estimate", action="store_true", help="Dry-run estimate for --start to --end.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--keywords", default=None, help="Comma-separated keyword override.")
    parser.add_argument("--required-keywords", default=None, help="Comma-separated required corn-market keyword override.")
    parser.add_argument("--weather-keywords", default=None, help="Comma-separated weather/ag risk keyword override.")
    parser.add_argument("--ag-context-keywords", default=None, help="Comma-separated agriculture context keyword override.")
    parser.add_argument("--exclude-terms", default=None, help="Comma-separated noise terms to exclude.")
    parser.add_argument("--locations", default=None, help="Comma-separated US location override.")
    parser.add_argument("--mode", choices=("direct", "expanded"), default="direct", help="direct only or expanded direct+weather/ag mode.")
    parser.add_argument("--limit", type=int, default=None, help="Optional BigQuery LIMIT per month.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--show-config", action="store_true", help="Print resolved non-secret config and exit.")
    parser.add_argument(
        "--allow-url-slug-fallback",
        action="store_true",
        help="Use cleaned URL slug as headline when PAGE_TITLE is missing. Useful for pre-2019 tests, lower quality.",
    )
    args = parser.parse_args()

    project = project_from_env_or_arg(args.project)
    keywords = parse_csv_list(args.keywords, DEFAULT_KEYWORDS)
    required_keywords = parse_csv_list(args.required_keywords, DEFAULT_REQUIRED_KEYWORDS)
    weather_keywords = parse_csv_list(args.weather_keywords, DEFAULT_WEATHER_KEYWORDS)
    ag_context_keywords = parse_csv_list(args.ag_context_keywords, DEFAULT_AG_CONTEXT_KEYWORDS)
    exclude_terms = parse_csv_list(args.exclude_terms, DEFAULT_EXCLUDE_TERMS)
    locations = parse_csv_list(args.locations, DEFAULT_US_LOCATIONS)
    end_date = args.end or date.today().strftime("%Y-%m-%d")

    if args.show_config:
        print(f"GCP_PROJECT={project}")
        print(f"keywords={','.join(keywords)}")
        print(f"required_keywords={','.join(required_keywords)}")
        print(f"weather_keywords={','.join(weather_keywords)}")
        print(f"ag_context_keywords={','.join(ag_context_keywords)}")
        print(f"exclude_terms={','.join(exclude_terms)}")
        print(f"locations={','.join(locations)}")
        print(f"mode={args.mode}")
        print(f"allow_url_slug_fallback={args.allow_url_slug_fallback}")
        print(f"out_dir={args.out_dir}")
        return 0

    if args.estimate:
        estimate_range(
            args.start,
            end_date,
            project,
            keywords,
            locations,
            required_keywords,
            weather_keywords,
            ag_context_keywords,
            exclude_terms,
            args.mode,
            args.allow_url_slug_fallback,
        )
    elif args.full:
        pull_range(
            args.start,
            end_date,
            project,
            args.out_dir,
            keywords,
            locations,
            required_keywords,
            weather_keywords,
            ag_context_keywords,
            exclude_terms,
            args.mode,
            args.allow_url_slug_fallback,
            args.limit,
            args.overwrite,
        )
    else:
        pull_month(
            args.month,
            project,
            args.out_dir,
            keywords,
            locations,
            required_keywords,
            weather_keywords,
            ag_context_keywords,
            exclude_terms,
            args.mode,
            args.allow_url_slug_fallback,
            args.limit,
            args.overwrite,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
