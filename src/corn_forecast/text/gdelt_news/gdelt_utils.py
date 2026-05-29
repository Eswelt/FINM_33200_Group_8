from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlencode

import pandas as pd
import requests


GDELT_DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_QUERY = (
    '(corn OR maize) '
    '(crop OR harvest OR planting OR yield OR drought OR ethanol OR export OR futures OR USDA) '
    'sourcecountry:US'
)
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
DEFAULT_ENV_PATH = Path(__file__).resolve().parent / ".env"
AI_SCORE_COLUMNS = [
    "relevance_score",
    "yield_supply_risk",
    "inventory_supply_tightness",
    "demand_strength",
    "ethanol_export_signal",
    "trade_policy_risk",
]


def parse_args_date(value: str) -> pd.Timestamp:
    return pd.Timestamp(value).tz_localize(None)


def gdelt_datetime(value: pd.Timestamp) -> str:
    return pd.Timestamp(value).strftime("%Y%m%d%H%M%S")


def friday_week(value: Any) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return ""
    return timestamp.to_period("W-FRI").end_time.normalize().strftime("%Y-%m-%d")


def safe_date_string(value: Any) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return "" if value is None else str(value)
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def article_id(url: str, title: str) -> str:
    key = (url or "") + "\n" + (title or "")
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def build_gdelt_artlist_url(
    query: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    max_records: int = 250,
    sort: str = "hybridrel",
) -> str:
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "startdatetime": gdelt_datetime(start),
        "enddatetime": gdelt_datetime(end),
        "maxrecords": str(max_records),
        "sort": sort,
    }
    return f"{GDELT_DOC_API_URL}?{urlencode(params)}"


def _article_records(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = payload.get("articles") or payload.get("results") or payload.get("data") or []
    return records if isinstance(records, list) else []


def normalize_gdelt_articles(payload: Dict[str, Any], query: str) -> pd.DataFrame:
    rows = []
    for raw in _article_records(payload):
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "").strip()
        url = str(raw.get("url") or "").strip()
        if not title or not url:
            continue
        seendate = raw.get("seendate") or raw.get("date") or raw.get("datetime")
        rows.append(
            {
                "article_id": article_id(url, title),
                "seendate": pd.to_datetime(seendate, errors="coerce"),
                "title": title,
                "url": url,
                "domain": raw.get("domain"),
                "language": raw.get("language"),
                "sourcecountry": raw.get("sourcecountry"),
                "query": query,
            }
        )
    frame = pd.DataFrame.from_records(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "article_id",
                "seendate",
                "week",
                "title",
                "url",
                "domain",
                "language",
                "sourcecountry",
                "query",
            ]
        )
    frame = frame.dropna(subset=["seendate"])
    frame["week"] = frame["seendate"].map(friday_week)
    frame = frame.drop_duplicates(subset=["article_id"]).sort_values(["seendate", "title"])
    return frame.reset_index(drop=True)


def normalize_title_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Make downstream OpenAI scoring accept either title or headline inputs."""
    result = frame.copy()
    if "title" not in result.columns and "headline" in result.columns:
        result["title"] = result["headline"]
    if "url" not in result.columns and "source_url" in result.columns:
        result["url"] = result["source_url"]
    if "domain" not in result.columns and "source_name" in result.columns:
        result["domain"] = result["source_name"]
    if "seendate" not in result.columns and "gkg_date" in result.columns:
        result["seendate"] = result["gkg_date"]
    if "article_id" not in result.columns:
        result["article_id"] = [
            article_id(str(url), str(title))
            for url, title in zip(result.get("url", ""), result.get("title", ""))
        ]
    if "week" not in result.columns and "seendate" in result.columns:
        result["week"] = result["seendate"].map(friday_week)
    return result


def fetch_gdelt_titles(
    start: pd.Timestamp,
    end: pd.Timestamp,
    query: str = DEFAULT_QUERY,
    max_records: int = 100,
    timeout: int = 30,
    max_retries: int = 5,
    retry_sleep_seconds: float = 8.0,
) -> pd.DataFrame:
    url = build_gdelt_artlist_url(query=query, start=start, end=end, max_records=max_records)
    response = None
    for attempt in range(max_retries + 1):
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "corn-weather-analysis-gdelt-demo/0.1"},
        )
        if response.status_code not in {429, 500, 502, 503, 504}:
            response.raise_for_status()
            break
        if attempt >= max_retries:
            response.raise_for_status()
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            delay = float(retry_after)
        else:
            delay = retry_sleep_seconds * (2**attempt) + random.uniform(0, 1.5)
        print(
            f"GDELT returned HTTP {response.status_code}; retrying in {delay:.1f}s "
            f"({attempt + 1}/{max_retries})..."
        )
        time.sleep(delay)
    return normalize_gdelt_articles(response.json(), query=query)


def save_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def load_env_file(path: Path = DEFAULT_ENV_PATH) -> Dict[str, str]:
    """Load simple KEY=VALUE lines from a local .env file without extra dependencies."""
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'").strip()
        if key:
            values[key] = value
            os.environ.setdefault(key, value)
    return values


def openai_api_key_from_env(path: Path = DEFAULT_ENV_PATH) -> str:
    load_env_file(path)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"Set OPENAI_API_KEY in your shell or in {path}. "
            "Example: OPENAI_API_KEY=sk-..."
        )
    if api_key in {"your_key_here", "sk-your-api-key-here"}:
        raise RuntimeError(f"Replace the placeholder OPENAI_API_KEY in {path} with a real API key.")
    return api_key


def openai_model_from_env(default: str = "gpt-4.1-mini", path: Path = DEFAULT_ENV_PATH) -> str:
    load_env_file(path)
    return os.getenv("OPENAI_MODEL", default)


def chunked(records: List[Dict[str, Any]], batch_size: int) -> Iterable[List[Dict[str, Any]]]:
    for start in range(0, len(records), batch_size):
        yield records[start : start + batch_size]


def title_feature_schema() -> Dict[str, Any]:
    return title_feature_schema_with_metadata(include_metadata=True)


def title_feature_schema_with_metadata(include_metadata: bool = True) -> Dict[str, Any]:
    score_properties = {
        column: {
            "type": "integer",
            "minimum": 0,
            "maximum": 3,
            "description": "0=no evidence, 1=weak, 2=moderate, 3=strong.",
        }
        for column in AI_SCORE_COLUMNS
    }
    item_properties = {
        "article_id": {"type": "string"},
        **score_properties,
    }
    item_required = ["article_id", *AI_SCORE_COLUMNS]
    if include_metadata:
        item_properties.update(
            {
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "rationale": {"type": "string"},
            }
        )
        item_required.extend(["confidence", "rationale"])
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": item_properties,
                    "required": item_required,
                },
            }
        },
        "required": ["items"],
    }


def extract_response_text(payload: Any) -> str:
    if hasattr(payload, "output_text") and isinstance(payload.output_text, str):
        return payload.output_text
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    parts = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and "text" in content:
                parts.append(content["text"])
    if parts:
        return "\n".join(parts)
    raise RuntimeError(f"Could not find output text in OpenAI response: {payload.keys()}")


def score_title_batch(
    records: List[Dict[str, Any]],
    api_key: str,
    model: str = DEFAULT_MODEL,
    timeout: int = 60,
    include_metadata: bool = True,
) -> List[Dict[str, Any]]:
    from openai import OpenAI

    instructions = (
        "Score corn-related news titles for US corn futures and CORN ETF research using only title/domain/time; no outside or future information. "
        "For each feature use 0 none, 1 weak, 2 moderate, 3 strong. "
        "relevance_score: 0 unrelated, 3 directly relevant to the US corn market. "
        "Features: relevance_score, yield_supply_risk, inventory_supply_tightness, demand_strength, "
        "ethanol_export_signal, trade_policy_risk. "
        "Extract features only; do not predict returns. "
        "Return JSON only."
    )
    if include_metadata:
        instructions += " Include confidence and a short rationale."
    input_text = json.dumps(
        {
            "task": (
                "Score each title into compact corn-market features for downstream forecasting."
            ),
            "items": [
                {
                    "article_id": row["article_id"],
                    "title": row["title"],
                    "domain": row.get("domain", ""),
                    "seendate": safe_date_string(row.get("seendate", "")),
                }
                for row in records
            ],
        },
        ensure_ascii=False,
    )
    payload = {
        "type": "json_schema",
        "name": "corn_title_features",
        "strict": True,
        "schema": title_feature_schema_with_metadata(include_metadata=include_metadata),
    }
    client = OpenAI(api_key=api_key, timeout=timeout)
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=input_text,
        text={"format": payload},
    )
    result = json.loads(extract_response_text(response))
    return result["items"]


def score_titles_with_openai(
    titles: pd.DataFrame,
    api_key: str,
    model: str = DEFAULT_MODEL,
    batch_size: int = 20,
    sleep_seconds: float = 0.2,
    show_progress: bool = True,
    include_metadata: bool = True,
    compact_output: bool = False,
) -> pd.DataFrame:
    base_columns = ["article_id", "seendate", "week", "title", "url", "domain", "language", "sourcecountry"]
    frame = normalize_title_columns(titles)
    for column in base_columns:
        if column not in frame.columns:
            frame[column] = ""
    records = frame[base_columns].fillna("").to_dict(orient="records")
    scored_rows = []
    batches = list(chunked(records, batch_size=batch_size))
    total_batches = len(batches)
    total_records = len(records)
    started_at = time.time()
    if show_progress:
        print(
            f"Scoring {total_records} titles with model={model}, "
            f"batch_size={batch_size}, batches={total_batches}"
        )
    for batch_index, batch in enumerate(batches, 1):
        batch_started_at = time.time()
        if show_progress:
            completed = len(scored_rows)
            print(
                f"[{batch_index}/{total_batches}] sending batch of {len(batch)} "
                f"({completed}/{total_records} done)...",
                flush=True,
            )
        scored_rows.extend(
            score_title_batch(
                batch,
                api_key=api_key,
                model=model,
                include_metadata=include_metadata,
            )
        )
        if show_progress:
            elapsed = time.time() - started_at
            batch_elapsed = time.time() - batch_started_at
            completed = len(scored_rows)
            rate = completed / elapsed if elapsed > 0 else 0
            remaining = total_records - completed
            eta = remaining / rate if rate > 0 else 0
            print(
                f"[{batch_index}/{total_batches}] done in {batch_elapsed:.1f}s; "
                f"{completed}/{total_records} complete; elapsed {elapsed:.1f}s; ETA {eta:.1f}s",
                flush=True,
            )
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    scores = pd.DataFrame.from_records(scored_rows)
    result = frame.merge(scores, on="article_id", how="left")
    if compact_output:
        duplicate_columns = ["title", "url", "domain", "seendate", "language", "sourcecountry", "sentiment"]
        result = result.drop(columns=[column for column in duplicate_columns if column in result.columns])
    return result


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help="GDELT DOC API query. Defaults to US-source corn market news.",
    )
    parser.add_argument("--max-records", type=int, default=100, help="Maximum GDELT articles to request.")
