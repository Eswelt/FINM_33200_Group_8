"""Parse USDA Weekly Weather and Crop Bulletin PDFs into core text rows."""

import argparse
from pathlib import Path

from corn_forecast.storage import write_table
from corn_forecast.text.wwcb import find_pdf_paths, parse_wwcb_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract core CORN-relevant text from USDA WWCB PDFs.")
    parser.add_argument("input", type=Path, help="A WWCB PDF file or a folder containing PDFs.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/interim/wwcb_core_text.parquet"),
        help="Output parquet/csv path.",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    pdf_paths = find_pdf_paths(args.input)
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found: {args.input}")
    frame = parse_wwcb_paths(pdf_paths)
    output = write_table(frame, args.output)
    print(f"Wrote WWCB core text: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
