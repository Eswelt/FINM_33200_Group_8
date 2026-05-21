from pathlib import Path

import pandas as pd

from corn_forecast.cli import main


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
    assert (tmp_path / "reports" / "metrics.json").exists()
    assert (tmp_path / "reports" / "predictions.csv").exists()
    assert (tmp_path / "reports" / "figures" / "predicted_probabilities.png").exists()

    predictions = pd.read_csv(tmp_path / "reports" / "predictions.csv")
    assert set(predictions["model"]) == {"A_price", "B_price_weather", "C_price_weather_text"}
