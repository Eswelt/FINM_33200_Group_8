from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from gdelt_utils import openai_api_key_from_env, openai_model_from_env, save_csv, score_titles_with_openai


def month_label(path: Path, root: Path) -> str:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    year = next((part.split("=", 1)[1] for part in parts if part.startswith("year=")), "????")
    month = next((part.split("=", 1)[1] for part in parts if part.startswith("month=")), "??")
    return f"{year}-{month}"


def score_month_file(
    input_path: Path,
    output_path: Path,
    api_key: str,
    model: str,
    batch_size: int,
    quiet: bool,
) -> int:
    titles = pd.read_csv(input_path)
    scored = score_titles_with_openai(
        titles,
        api_key=api_key,
        model=model,
        batch_size=batch_size,
        show_progress=not quiet,
        include_metadata=False,
        compact_output=True,
    )
    save_csv(scored, output_path)
    parquet_path = output_path.with_suffix(".parquet")
    scored.to_parquet(parquet_path, index=False)
    print(f"Wrote {len(scored)} rows: {output_path}")
    print(f"Wrote parquet: {parquet_path}")
    return len(scored)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score all monthly BigQuery GDELT title files with OpenAI.")
    parser.add_argument("--root", type=Path, default=Path("data/interim/gdelt_corn_headlines"))
    parser.add_argument("--input-name", default="data.csv")
    parser.add_argument("--out-name", default="scored_compact.csv")
    parser.add_argument("--model", default=None)
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument("--overwrite", action="store_true", help="Re-score months with existing output.")
    parser.add_argument("--quiet", action="store_true", help="Disable per-batch OpenAI progress.")
    parser.add_argument("--max-months", type=int, default=None, help="Optional safety limit for testing.")
    args = parser.parse_args()

    api_key = openai_api_key_from_env()
    model = args.model or openai_model_from_env()
    input_files = sorted(args.root.glob(f"year=*/month=*/{args.input_name}"))
    if args.max_months is not None:
        input_files = input_files[: args.max_months]
    if not input_files:
        raise FileNotFoundError(f"No monthly files found under {args.root}/year=*/month=*/{args.input_name}")

    print(f"Found {len(input_files)} monthly files under {args.root}")
    total_rows = 0
    started_at = time.time()
    for index, input_path in enumerate(input_files, 1):
        label = month_label(input_path, args.root)
        output_path = input_path.with_name(args.out_name)
        if output_path.exists() and not args.overwrite:
            print(f"[{index}/{len(input_files)}] {label}: {output_path.name} exists, skipping")
            continue
        print(f"[{index}/{len(input_files)}] {label}: scoring {input_path}")
        total_rows += score_month_file(
            input_path=input_path,
            output_path=output_path,
            api_key=api_key,
            model=model,
            batch_size=args.batch_size,
            quiet=args.quiet,
        )
    elapsed = time.time() - started_at
    print(f"Done. Newly scored rows: {total_rows}. Elapsed: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
