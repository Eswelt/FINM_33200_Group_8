from pathlib import Path

import pandas as pd

from cli import main


def test_demo_pipeline_writes_core_outputs(tmp_path: Path):
    exit_code = main(
        [
            "all",
            "--demo",
            "--root",
            str(tmp_path),
            "--start",
            "2018-01-01",
            "--end",
            "2024-03-31",
            "--split-date",
            "2022-12-31",
        ]
    )

    assert exit_code == 0
    reports_dir = tmp_path / "output" / "report"
    assert (reports_dir / "metrics.json").exists()
    assert (reports_dir / "predictions.csv").exists()
    assert (reports_dir / "figures" / "predicted_probabilities.png").exists()
    assert (reports_dir / "figures" / "cumulative_returns.png").exists()

    predictions = pd.read_csv(reports_dir / "predictions.csv")
    assert set(predictions["estimator"]) == {"logit", "hgb"}
    assert set(predictions["feature_set"]) == {"A_price", "B_price_weather", "C_price_weather_text"}
    assert {"fold", "position", "strategy_log_return", "cum_strategy_return"}.issubset(predictions.columns)
