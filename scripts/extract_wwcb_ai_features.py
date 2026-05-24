"""Extract weekly AI features from parsed USDA WWCB text with GLM."""

import argparse
from pathlib import Path

from corn_forecast.storage import read_table, write_table
from corn_forecast.text.ai_features import (
    DEFAULT_GLM_BASE_URL,
    DEFAULT_GLM_MODEL,
    GLMClient,
    aggregate_weekly_ai_features,
    api_key_from_env,
    extract_ai_feature_rows,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Use GLM to convert WWCB text into fixed AI feature columns.")
    parser.add_argument("--input", type=Path, default=Path("data/interim/wwcb_core_text.parquet"))
    parser.add_argument("--output", type=Path, default=Path("data/interim/ai_weekly.parquet"))
    parser.add_argument("--raw-output", type=Path, default=Path("data/interim/ai_wwcb_raw.parquet"))
    parser.add_argument("--model", default=DEFAULT_GLM_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_GLM_BASE_URL)
    parser.add_argument("--api-key-env", default=None, help="Optional env var name for the GLM API key.")
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit for small test runs.")
    parser.add_argument("--mock", action="store_true", help="Run deterministic local extraction without calling GLM.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Seconds to wait between GLM API calls.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    core_text = read_table(args.input)

    client = None
    if not args.mock:
        import os

        api_key = os.getenv(args.api_key_env) if args.api_key_env else api_key_from_env()
        if not api_key:
            raise RuntimeError("Missing GLM API key. Set BIGMODEL_API_KEY, ZHIPUAI_API_KEY, or GLM_API_KEY.")
        client = GLMClient(api_key=api_key, model=args.model, base_url=args.base_url)

    raw_rows = extract_ai_feature_rows(
        core_text,
        client=client,
        mock=args.mock,
        limit=args.limit,
        sleep_seconds=args.sleep,
    )
    weekly = aggregate_weekly_ai_features(raw_rows)
    raw_path = write_table(raw_rows, args.raw_output)
    output_path = write_table(weekly, args.output)
    print(f"Wrote raw AI WWCB rows: {raw_path}")
    print(f"Wrote weekly AI features: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
