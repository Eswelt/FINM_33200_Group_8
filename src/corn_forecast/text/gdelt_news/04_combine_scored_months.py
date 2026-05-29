from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from gdelt_utils import save_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Combine monthly scored GDELT files into one dataset.")
    parser.add_argument("--root", type=Path, default=Path("data/interim/gdelt_corn_headlines"))
    parser.add_argument("--input-name", default="scored_compact.parquet")
    parser.add_argument("--out", type=Path, default=Path("data/interim/gdelt_corn_headlines/scored_compact_all.parquet"))
    parser.add_argument("--csv", type=Path, default=None, help="Optional CSV output path.")
    args = parser.parse_args()

    files = sorted(args.root.glob(f"year=*/month=*/{args.input_name}"))
    if not files and args.input_name.endswith(".parquet"):
        files = sorted(args.root.glob("year=*/month=*/scored_compact.csv"))
    if not files:
        raise FileNotFoundError(f"No scored files found under {args.root}/year=*/month=*/{args.input_name}")

    frames = []
    for path in files:
        if path.suffix == ".parquet":
            frame = pd.read_parquet(path)
        else:
            frame = pd.read_csv(path)
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    if "gkg_date" in combined.columns:
        combined = combined.sort_values(["gkg_date", "article_id"]).reset_index(drop=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.suffix == ".parquet":
        combined.to_parquet(args.out, index=False)
    else:
        save_csv(combined, args.out)
    print(f"Combined {len(files)} files, {len(combined)} rows: {args.out}")
    if args.csv is not None:
        save_csv(combined, args.csv)
        print(f"Wrote CSV: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
