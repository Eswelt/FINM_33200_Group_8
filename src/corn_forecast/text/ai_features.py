"""LLM-based feature extraction for USDA WWCB core text."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd
import requests


DEFAULT_GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
DEFAULT_GLM_MODEL = "glm-4.5-flash"
DEFAULT_MAX_REPORT_CHARS = 8000
AI_FEATURE_COLUMNS = [
    "ai_moisture_stress",
    "ai_heat_stress",
    "ai_excess_rain_risk",
    "ai_planting_delay_risk",
    "ai_harvest_delay_risk",
    "ai_yield_risk",
    "ai_crop_condition_trend",
]
RISK_COLUMNS = [column for column in AI_FEATURE_COLUMNS if column != "ai_crop_condition_trend"]


SYSTEM_PROMPT = """You extract structured agricultural features from USDA Weekly Weather and Crop Bulletin text.
You do not predict ETF prices. You only convert the report into point-in-time crop/weather feature scores.
Return valid JSON only."""


USER_PROMPT_TEMPLATE = """Read the USDA Weekly Weather and Crop Bulletin excerpt for a CORN ETF forecasting project.

Feature definitions:
- ai_moisture_stress: 0 none/irrelevant, 1 mild dryness, 2 moderate drought/soil moisture stress, 3 severe drought/moisture stress for corn areas.
- ai_heat_stress: 0 none/irrelevant, 1 mild heat, 2 moderate heat stress, 3 severe heat stress for corn areas.
- ai_excess_rain_risk: 0 none/irrelevant, 1 mild wetness, 2 moderate excessive rain/flooding/fieldwork disruption, 3 severe excessive rain risk.
- ai_planting_delay_risk: 0 none/not planting season/no delay, 1 mild delay, 2 moderate delay, 3 severe delay.
- ai_harvest_delay_risk: 0 none/not harvest season/no delay, 1 mild delay, 2 moderate delay, 3 severe delay.
- ai_yield_risk: 0 none/supportive conditions, 1 mild yield risk, 2 moderate yield risk, 3 severe yield risk.
- ai_crop_condition_trend: -2 clearly worsening, -1 slightly worsening, 0 neutral/mixed/unknown, 1 slightly improving, 2 clearly improving.

Rules:
- Use only the text below.
- Focus on corn-producing regions and corn progress/condition.
- If the text lacks evidence for a field, use 0.
- Output exactly these seven keys as numbers. No extra keys.

Report date: {report_date}
Prediction week: {week}

Text:
{report_text}
"""


@dataclass
class GLMClient:
    api_key: str
    model: str = DEFAULT_GLM_MODEL
    base_url: str = DEFAULT_GLM_BASE_URL
    timeout: int = 60
    max_retries: int = 6
    retry_sleep_seconds: float = 10.0

    def extract_json(self, prompt: str) -> Dict[str, Any]:
        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "do_sample": False,
            "stream": False,
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
        }
        response = None
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self.timeout,
                )
                if response.status_code not in {429, 500, 502, 503, 504}:
                    break
                last_error = requests.HTTPError(f"Retryable HTTP status {response.status_code}", response=response)
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else self.retry_sleep_seconds * (2**attempt)
            except (requests.Timeout, requests.ConnectionError) as error:
                last_error = error
                delay = self.retry_sleep_seconds * (2**attempt)

            if attempt >= self.max_retries:
                if response is not None:
                    break
                raise last_error
            time.sleep(delay)
        if response is None:
            raise last_error
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        features = parse_json_object(content)
        usage = payload.get("usage", {})
        features["_glm_model"] = payload.get("model", self.model)
        features["_glm_prompt_tokens"] = usage.get("prompt_tokens")
        features["_glm_completion_tokens"] = usage.get("completion_tokens")
        features["_glm_total_tokens"] = usage.get("total_tokens")
        return features


def api_key_from_env() -> Optional[str]:
    return os.getenv("BIGMODEL_API_KEY") or os.getenv("ZHIPUAI_API_KEY") or os.getenv("GLM_API_KEY")


def api_key_from_env_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() in {"BIGMODEL_API_KEY", "ZHIPUAI_API_KEY", "GLM_API_KEY"}:
            return value.strip().strip('"').strip("'")
    return None


def truncate_report_text(text: str, max_chars: int = DEFAULT_MAX_REPORT_CHARS) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[TRUNCATED]"


def build_user_prompt(row: pd.Series, max_report_chars: int = DEFAULT_MAX_REPORT_CHARS) -> str:
    return USER_PROMPT_TEMPLATE.format(
        report_date=row.get("report_date", ""),
        week=row.get("week", ""),
        report_text=truncate_report_text(str(row.get("report_text", "")), max_chars=max_report_chars),
    )


def parse_json_object(content: str) -> Dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def validate_ai_features(raw: Dict[str, Any]) -> Dict[str, float]:
    if isinstance(raw.get("answer"), dict):
        raw = raw["answer"]
    elif isinstance(raw.get("features"), dict):
        raw = raw["features"]

    missing = [column for column in AI_FEATURE_COLUMNS if column not in raw]
    extra = [key for key in raw if key.startswith("ai_") and key not in AI_FEATURE_COLUMNS]
    if missing:
        raise ValueError(f"Missing AI feature columns: {missing}")
    if extra:
        raise ValueError(f"Unexpected AI feature columns: {extra}")

    features: Dict[str, float] = {}
    for column in RISK_COLUMNS:
        value = float(raw[column])
        if value < 0 or value > 3:
            raise ValueError(f"{column} must be between 0 and 3, got {value}")
        features[column] = value

    trend = float(raw["ai_crop_condition_trend"])
    if trend < -2 or trend > 2:
        raise ValueError(f"ai_crop_condition_trend must be between -2 and 2, got {trend}")
    features["ai_crop_condition_trend"] = trend
    return features


def mock_extract_features(report_text: str) -> Dict[str, float]:
    """Deterministic fallback for tests and pipeline dry-runs without an API key."""
    text = report_text.lower()
    features = {column: 0.0 for column in AI_FEATURE_COLUMNS}
    if any(word in text for word in ("dry", "drought", "short topsoil", "moisture stress")):
        features["ai_moisture_stress"] = 1.0
        features["ai_yield_risk"] = max(features["ai_yield_risk"], 1.0)
    if any(word in text for word in ("hot", "heat", "above-normal temperatures")):
        features["ai_heat_stress"] = 1.0
        features["ai_yield_risk"] = max(features["ai_yield_risk"], 1.0)
    if any(word in text for word in ("wet", "rain", "flood", "excessive precipitation")):
        features["ai_excess_rain_risk"] = 1.0
    if "plant" in text and any(word in text for word in ("behind", "delay", "slow")):
        features["ai_planting_delay_risk"] = 1.0
    if "harvest" in text and any(word in text for word in ("behind", "delay", "slow")):
        features["ai_harvest_delay_risk"] = 1.0
    if "good to excellent" in text and any(word in text for word in ("above", "improved", "ahead")):
        features["ai_crop_condition_trend"] = 1.0
    if "behind" in text or "decline" in text:
        features["ai_crop_condition_trend"] = min(features["ai_crop_condition_trend"], -1.0)
    return features


def extract_ai_feature_rows(
    core_text: pd.DataFrame,
    client: Optional[GLMClient] = None,
    mock: bool = False,
    limit: Optional[int] = None,
    sleep_seconds: float = 0.2,
    max_report_chars: int = DEFAULT_MAX_REPORT_CHARS,
) -> pd.DataFrame:
    frame = core_text.copy()
    frame["week"] = pd.to_datetime(frame["week"]).dt.normalize()
    if limit is not None:
        frame = frame.head(limit)

    records = []
    for _, row in frame.iterrows():
        if mock:
            raw_features = mock_extract_features(str(row.get("report_text", "")))
            metadata: Dict[str, Any] = {"glm_model": "mock", "glm_prompt_tokens": None, "glm_completion_tokens": None, "glm_total_tokens": None}
        else:
            if client is None:
                raise ValueError("A GLMClient is required unless mock=True.")
            raw = client.extract_json(build_user_prompt(row, max_report_chars=max_report_chars))
            raw_features = raw
            metadata = {
                "glm_model": raw.get("_glm_model", client.model),
                "glm_prompt_tokens": raw.get("_glm_prompt_tokens"),
                "glm_completion_tokens": raw.get("_glm_completion_tokens"),
                "glm_total_tokens": raw.get("_glm_total_tokens"),
            }
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        features = validate_ai_features(raw_features)
        record = {
            "week": row["week"],
            "report_date": row.get("report_date"),
            "source_file": row.get("source_file"),
            **features,
            **metadata,
        }
        records.append(record)
    return pd.DataFrame.from_records(records)


def aggregate_weekly_ai_features(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame(columns=["week"] + AI_FEATURE_COLUMNS)
    frame = rows.copy()
    frame["week"] = pd.to_datetime(frame["week"]).dt.normalize()
    aggregations = {column: "mean" for column in AI_FEATURE_COLUMNS}
    weekly = frame.groupby("week", as_index=False).agg(aggregations)
    return weekly.sort_values("week").reset_index(drop=True)
