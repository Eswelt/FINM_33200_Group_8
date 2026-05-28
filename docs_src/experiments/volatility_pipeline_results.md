# Volatility Pipeline Results

Run date: 2026-05-27.

This auxiliary pipeline tests whether the feature sets are better at forecasting next-week risk than next-week return direction. The volatility target is:

```text
target_abs_return_next = abs(next_week_log_return)
```

The high-volatility diagnostic uses a fold-specific threshold: the 70th percentile of `target_abs_return_next` in the training window. This avoids using test-period information to define high-volatility weeks.

Common setup:

- Sample: `2011-01-01` to `2026-05-15`
- Split date: `2022-12-31`
- OOS window: 175 weekly observations
- Walk-forward folds: 14
- Test window: 13 weeks
- Retrain step: 13 weeks
- Validation: expanding window

Command:

```bash
PYTHONPATH=src uv run python -m cli volatility \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --feature-sets price_only,price_ai,price_calendar,price_calendar_ai
```

## Results

| input set | model | MAE | RMSE | R2 | Spearman | high-vol acc | high-vol bal acc | predicted high-vol rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `price_only` | Ridge | 0.0127 | 0.0173 | -0.0252 | -0.046 | 78.9% | 54.5% | 7.4% |
| `price_only` | HGB | 0.0129 | 0.0181 | -0.1248 | 0.020 | 75.4% | 51.3% | 9.7% |
| `price_ai` | Ridge | 0.0125 | 0.0173 | -0.0245 | 0.027 | 79.4% | 56.0% | 8.0% |
| `price_ai` | HGB | 0.0131 | 0.0186 | -0.1775 | 0.003 | 71.4% | 48.8% | 13.7% |
| `price_calendar` | Ridge | 0.0126 | 0.0168 | 0.0411 | 0.160 | 77.1% | 59.0% | 14.9% |
| `price_calendar` | HGB | 0.0122 | 0.0170 | 0.0160 | 0.250 | 74.9% | 55.4% | 14.9% |
| `price_calendar_ai` | Ridge | 0.0125 | 0.0168 | 0.0377 | 0.158 | 76.0% | 57.2% | 14.9% |
| `price_calendar_ai` | HGB | 0.0124 | 0.0169 | 0.0201 | 0.216 | 76.6% | 56.4% | 13.1% |

Actual OOS high-volatility rate: 19.4%.

## Interpretation

Volatility appears more predictable than return direction in this sample. Price-only and price-plus-GLM volatility models have negative OOS R2, while adding calendar features produces positive OOS R2 and better rank correlation. The GLM USDA scores do not clearly improve over `price_calendar` here, but they remain competitive when combined with calendar features. This is a useful project result because it suggests agricultural seasonality is the main driver of predictable risk, while USDA-report signals may be better treated as a complement rather than a replacement for season controls.

## Files Updated

- `src/volatility.py`
- `docs_src/reports/volatility_metrics.json`
- `docs_src/reports/volatility_predictions.csv`
