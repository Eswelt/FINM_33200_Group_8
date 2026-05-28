import pandas as pd

from text.ai_features import (
    GLMClient,
    aggregate_weekly_ai_features,
    api_key_from_env_file,
    build_user_prompt,
    extract_ai_feature_rows,
    parse_json_object,
    truncate_report_text,
    validate_ai_features,
)


def test_parse_json_object_accepts_fenced_json():
    content = """```json
    {"ai_moisture_stress": 1, "ai_heat_stress": 0}
    ```"""

    parsed = parse_json_object(content)

    assert parsed["ai_moisture_stress"] == 1


def test_validate_ai_features_rejects_missing_columns():
    raw = {
        "ai_moisture_stress": 1,
        "ai_heat_stress": 0,
        "ai_excess_rain_risk": 0,
        "ai_planting_delay_risk": 0,
        "ai_harvest_delay_risk": 0,
        "ai_yield_risk": 1,
    }

    try:
        validate_ai_features(raw)
    except ValueError as exc:
        assert "ai_crop_condition_trend" in str(exc)
    else:
        raise AssertionError("Expected missing-column validation error.")


def test_validate_ai_features_accepts_answer_wrapper():
    raw = {
        "answer": {
            "ai_moisture_stress": 1,
            "ai_heat_stress": 0,
            "ai_excess_rain_risk": 0,
            "ai_planting_delay_risk": 0,
            "ai_harvest_delay_risk": 0,
            "ai_yield_risk": 1,
            "ai_crop_condition_trend": -1,
        }
    }

    features = validate_ai_features(raw)

    assert features["ai_moisture_stress"] == 1
    assert features["ai_crop_condition_trend"] == -1


def test_mock_extraction_and_weekly_aggregation():
    core_text = pd.DataFrame(
        {
            "week": ["2026-05-08", "2026-05-08"],
            "report_date": ["2026-05-05", "2026-05-05"],
            "source_file": ["a.pdf", "b.pdf"],
            "report_text": [
                "Corn planting was behind average after wet rain delayed fieldwork.",
                "Dry conditions and drought increased moisture stress.",
            ],
        }
    )

    rows = extract_ai_feature_rows(core_text, mock=True)
    weekly = aggregate_weekly_ai_features(rows)

    assert len(rows) == 2
    assert weekly.loc[0, "week"] == pd.Timestamp("2026-05-08")
    assert weekly.loc[0, "ai_planting_delay_risk"] > 0
    assert weekly.loc[0, "ai_moisture_stress"] > 0


def test_build_user_prompt_contains_fixed_schema():
    row = pd.Series({"report_date": "2026-05-05", "week": "2026-05-08", "report_text": "Corn text."})

    prompt = build_user_prompt(row)

    assert "ai_moisture_stress" in prompt
    assert "Output exactly these seven keys" in prompt
    assert "Corn text." in prompt


def test_build_user_prompt_truncates_long_report_text():
    row = pd.Series({"report_date": "2026-05-05", "week": "2026-05-08", "report_text": "a" * 100})

    prompt = build_user_prompt(row, max_report_chars=10)

    assert "a" * 10 in prompt
    assert "[TRUNCATED]" in prompt
    assert "a" * 20 not in prompt


def test_truncate_report_text_keeps_short_text():
    assert truncate_report_text("short", max_chars=10) == "short"


def test_glm_client_has_retry_defaults():
    client = GLMClient(api_key="test")

    assert client.max_retries >= 1
    assert client.retry_sleep_seconds > 0


def test_api_key_from_env_file_reads_bigmodel_key(tmp_path):
    env_file = tmp_path / ".env.local"
    env_file.write_text("OTHER=value\nBIGMODEL_API_KEY='abc.def'\n")

    assert api_key_from_env_file(env_file) == "abc.def"
