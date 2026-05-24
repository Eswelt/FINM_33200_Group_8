"""Download USDA Weekly Weather and Crop Bulletin PDFs and write a manifest."""

import argparse
from pathlib import Path

from corn_forecast.storage import write_table
from corn_forecast.text.wwcb_download import discover_releases, download_releases


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch download USDA WWCB PDFs from ESMIS.")
    parser.add_argument("--start", default=None, help="Earliest release date to download, e.g. 2011-01-01.")
    parser.add_argument("--end", default=None, help="Latest release date to download, e.g. 2026-05-15.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/external/wwcb_pdfs"),
        help="Folder for raw WWCB PDF files.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/interim/wwcb_manifest.csv"),
        help="CSV/parquet manifest with release date, source URL, local path, and download status.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional cap for testing small downloads.")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional cap on archive pages to scan.")
    parser.add_argument("--dry-run", action="store_true", help="List matching PDFs without downloading them.")
    parser.add_argument("--overwrite", action="store_true", help="Re-download files that already exist.")
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds to wait between PDF downloads.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    releases = discover_releases(start=args.start, end=args.end, max_pages=args.max_pages)
    if args.limit is not None:
        releases = releases[: args.limit]
    manifest = download_releases(
        releases,
        output_dir=args.output_dir,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        sleep_seconds=args.sleep,
    )
    output = write_table(manifest, args.manifest)
    print(f"Matched WWCB PDFs: {len(manifest)}")
    print(f"Wrote WWCB manifest: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
