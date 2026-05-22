# Experiments

Use this folder for experiment notes and exported comparison tables.

Current launch tasks:

```bash
uv run python -m corn_forecast.cli return-strategy --start 2011-01-01 --end 2026-05-15 --split-date 2022-12-31 --validation-scheme expanding --transaction-cost-bps 5 --buffer-bps 25
uv run python -m corn_forecast.cli test-price-targets --start 2011-01-01 --end 2026-05-15 --split-date 2022-12-31 --fixed-return-threshold 0.02
uv run python -m corn_forecast.cli select-threshold --start 2011-01-01 --end 2026-05-15 --split-date 2022-12-31 --threshold-grid 1.0 --validation-scheme expanding --long-threshold 0.45
uv run python -m corn_forecast.cli select-threshold --start 2011-01-01 --end 2026-05-15 --split-date 2022-12-31 --threshold-grid 1.0 --validation-scheme rolling --train-window-weeks 260 --long-threshold 0.45
```

Do not commit large generated CSVs from local runs unless the team explicitly decides to version a small final result table.
