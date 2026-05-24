"""Extract weekly AI features from parsed USDA WWCB text with GLM."""

import argparse
from pathlib import Path

import pandas as pd

from corn_forecast.storage import read_table, write_table
from corn_forecast.text.ai_features import (
    AI_FEATURE_COLUMNS,
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
    parser.add_argument("--sleep", type=float, default=1.0, help="Seconds to wait between GLM API calls.")
    parser.add_argument("--max-retries", type=int, default=6, help="Retries for 429 or transient GLM server errors.")
    parser.add_argument("--retry-sleep", type=float, default=10.0, help="Base seconds for exponential retry backoff.")
    return parser


def _row_key(row) -> tuple:
    return (pd.to_datetime(row["week"]).normalize(), str(row.get("source_file", "")))


def _load_existing_raw(path: Path) -> pd.DataFrame:
    try:
        return read_table(path)
    except FileNotFoundError:
        return pd.DataFrame()


def _extract_with_checkpoints(core_text, client, args) -> pd.DataFrame:
    frame = core_text.copy()
    frame["week"] = pd.to_datetime(frame["week"]).dt.normalize()
    if args.limit is not None:
        frame = frame.head(args.limit)

    existing = _load_existing_raw(args.raw_output)
    records = [] if existing.empty else existing.to_dict("records")
    done_keys = set()
    if not existing.empty:
        for _, row in existing.iterrows():
            done_keys.add(_row_key(row))

    for _, row in frame.iterrows():
        if _row_key(row) in done_keys:
            continue
        new_row = extract_ai_feature_rows(
            pd.DataFrame([row]),
            client=client,
            mock=args.mock,
            sleep_seconds=args.sleep,
        )
        records.extend(new_row.to_dict("records"))
        raw_rows = pd.DataFrame.from_records(records)
        weekly = aggregate_weekly_ai_features(raw_rows)
        write_table(raw_rows, args.raw_output)
        write_table(weekly, args.output)
        print(f"Checkpointed AI WWCB rows: {len(raw_rows)} / {len(frame)}", flush=True)

    return pd.DataFrame.from_records(records)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    core_text = read_table(args.input)

    client = None
    if not args.mock:
        import os

        api_key = os.getenv(args.api_key_env) if args.api_key_env else api_key_from_env()
        if not api_key:
            raise RuntimeError("Missing GLM API key. Set BIGMODEL_API_KEY, ZHIPUAI_API_KEY, or GLM_API_KEY.")
        client = GLMClient(
            api_key=api_key,
            model=args.model,
            base_url=args.base_url,
            max_retries=args.max_retries,
            retry_sleep_seconds=args.retry_sleep,
        )

    raw_rows = _extract_with_checkpoints(core_text, client, args)
    weekly = aggregate_weekly_ai_features(raw_rows)
    if raw_rows.empty:
        raw_rows = pd.DataFrame(columns=["week", "report_date", "source_file"] + AI_FEATURE_COLUMNS)
    raw_path = write_table(raw_rows, args.raw_output)
    output_path = write_table(weekly, args.output)
    print(f"Wrote raw AI WWCB rows: {raw_path}")
    print(f"Wrote weekly AI features: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
