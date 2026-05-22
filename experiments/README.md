# Experiments

Use this folder for experiment notes and exported comparison tables.

Current launch tasks:

```bash
uv run python -m corn_forecast.cli select-threshold --start 2011-01-01 --end 2026-05-15 --split-date 2022-12-31 --threshold-grid 1.0 --validation-scheme expanding --long-threshold 0.45
uv run python -m corn_forecast.cli select-threshold --start 2011-01-01 --end 2026-05-15 --split-date 2022-12-31 --threshold-grid 1.0 --validation-scheme rolling --train-window-weeks 260 --long-threshold 0.45
uv run python -m corn_forecast.cli test-price-targets --start 2011-01-01 --end 2026-05-15 --split-date 2022-12-31
```

Do not commit large generated CSVs from local runs unless the team explicitly decides to version a small final result table.
