# Three Input Pipeline Results

Run date: 2026-05-27.

This run compares point-in-time input sets under the same frozen sample, split, and walk-forward schedule:

- `price_only`: historical CORN ETF price features.
- `price_ai`: historical price features plus GLM-extracted USDA Weekly Weather and Crop Bulletin scores.
- `price_calendar`: historical price features plus corn-season calendar features.
- `price_calendar_ai`: historical price features, calendar features, and GLM-extracted USDA Weekly Weather and Crop Bulletin scores.

Common setup:

- Sample: `2011-01-01` to `2026-05-15`
- Split date: `2022-12-31`
- OOS window: 175 weekly observations
- Walk-forward folds: 14
- Test window: 13 weeks
- Retrain step: 13 weeks
- Fixed direction target: down / flat / up using +/-2% next-week log-return bands
- Expected-return strategy: long if predicted return exceeds 5 bps transaction cost plus 25 bps buffer

Commands:

```bash
uv run --extra dev doit fetch_prices build_features

PYTHONPATH=src uv run python -m cli classify-move \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --fixed-return-threshold 0.02 \
  --feature-sets price_only,price_ai,price_calendar,price_calendar_ai

PYTHONPATH=src uv run python -m cli return-strategy \
  --start 2011-01-01 \
  --end 2026-05-15 \
  --split-date 2022-12-31 \
  --feature-sets price_only,price_ai,price_calendar,price_calendar_ai \
  --transaction-cost-bps 5 \
  --buffer-bps 25
```

## Direction Pipeline

Main fixed-band three-class classification results:

| input set | accuracy | balanced accuracy | macro F1 | OOS rows | folds |
| --- | ---: | ---: | ---: | ---: | ---: |
| `price_only` | 46.9% | 31.9% | 31.4% | 175 | 14 |
| `price_ai` | 49.7% | 32.6% | 32.6% | 175 | 14 |
| `price_calendar` | 42.3% | 30.9% | 30.4% | 175 | 14 |
| `price_calendar_ai` | 42.9% | 30.0% | 30.0% | 175 | 14 |

Auxiliary return-regression diagnostics emitted by the same direction-target runner:

| input set | MAE | RMSE | R2 | direction accuracy |
| --- | ---: | ---: | ---: | ---: |
| `price_only` | 0.0175 | 0.0246 | -0.0449 | 52.0% |
| `price_ai` | 0.0182 | 0.0254 | -0.1161 | 48.6% |
| `price_calendar` | 0.0173 | 0.0243 | -0.0220 | 53.1% |
| `price_calendar_ai` | 0.0180 | 0.0252 | -0.1018 | 53.7% |

Interpretation: under the fixed +/-2% three-class target, `price_ai` modestly improves the three-class classification metrics versus `price_only`. That improvement does not appear in the return-regression diagnostic, where `price_ai` worsens error and sign accuracy.

## Expected-Return Pipeline

Expected-return forecast and trading diagnostics:

| input set | model | MAE | RMSE | R2 | direction accuracy | trade frequency | strategy return | Sharpe | max drawdown |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `price_only` | Ridge | 0.0175 | 0.0246 | -0.0449 | 52.0% | 11.4% | 3.3% | 0.089 | -14.2% |
| `price_only` | HGB | 0.0187 | 0.0258 | -0.1535 | 50.9% | 32.0% | -25.9% | -0.769 | -32.8% |
| `price_ai` | Ridge | 0.0182 | 0.0254 | -0.1161 | 48.6% | 20.6% | 3.1% | 0.077 | -20.7% |
| `price_ai` | HGB | 0.0189 | 0.0259 | -0.1640 | 46.9% | 30.9% | -30.9% | -0.997 | -33.6% |
| `price_calendar` | Ridge | 0.0173 | 0.0243 | -0.0220 | 53.1% | 21.1% | -6.2% | -0.188 | -16.8% |
| `price_calendar` | HGB | 0.0181 | 0.0252 | -0.0989 | 53.7% | 30.9% | 3.6% | 0.130 | -9.4% |
| `price_calendar_ai` | Ridge | 0.0180 | 0.0252 | -0.1018 | 53.7% | 27.4% | 10.7% | 0.322 | -14.8% |
| `price_calendar_ai` | HGB | 0.0182 | 0.0247 | -0.0527 | 53.1% | 33.7% | -5.8% | -0.208 | -13.6% |

Interpretation: all return regressions have negative OOS R2, so the return forecasts remain weak in a statistical sense. The best trading outcome in this run is `price_calendar_ai` with Ridge, which produces a 10.7% OOS strategy return and Sharpe 0.322. This should be presented as suggestive rather than conclusive evidence because the forecast errors remain poor and the HGB version of the same feature set loses money.

## Files Updated

- `docs_src/reports/price_target_tests.json`
- `docs_src/reports/price_target_predictions.csv`
- `docs_src/reports/expected_return_metrics.json`
- `docs_src/reports/expected_return_predictions.csv`
