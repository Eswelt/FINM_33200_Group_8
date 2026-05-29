from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from gdelt_utils import openai_api_key_from_env, openai_model_from_env, save_csv, score_titles_with_openai


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compact OpenAI scoring: structured corn-market headline features only."
    )
    parser.add_argument("--input", type=Path, default=Path("data/interim/gdelt_corn_headlines/year=2025/month=01/data.csv"))
    parser.add_argument("--out", type=Path, default=Path("data/interim/gdelt_corn_headlines/year=2025/month=01/scored_compact.csv"))
    parser.add_argument("--model", default=None)
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument("--quiet", action="store_true", help="Disable batch progress output.")
    args = parser.parse_args()

    api_key = openai_api_key_from_env()
    model = args.model or openai_model_from_env()
    titles = pd.read_csv(args.input)
    scored = score_titles_with_openai(
        titles,
        api_key=api_key,
        model=model,
        batch_size=args.batch_size,
        show_progress=not args.quiet,
        include_metadata=False,
        compact_output=True,
    )
    save_csv(scored, args.out)
    print(f"Wrote {len(scored)} compact scored titles: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
