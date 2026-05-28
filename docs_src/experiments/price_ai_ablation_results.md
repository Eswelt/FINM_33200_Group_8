# Price Plus GLM Ablation Results

Run date: 2026-05-27.

This ablation adds a fourth input set:

- `price_ai`: historical CORN ETF price features plus GLM-extracted USDA Weekly Weather and Crop Bulletin scores, with no calendar seasonality features.

The purpose is to separate the contribution of GLM USDA scores from the contribution of deterministic crop-season calendar controls.

Common setup:

- Sample: `2011-01-01` to `2026-05-15`
- Split date: `2022-12-31`
- OOS window: 175 weekly observations
- Walk-forward folds: 14
- Test window: 13 weeks
- Retrain step: 13 weeks

Feature sets compared:

```text
price_only
price_ai
price_calendar
price_calendar_ai
```

## Direction Pipeline

Fixed +/-2% three-class classification:

| input set | accuracy | balanced accuracy | macro F1 |
| --- | ---: | ---: | ---: |
| `price_only` | 46.9% | 31.9% | 31.4% |
| `price_ai` | 49.7% | 32.6% | 32.6% |
| `price_calendar` | 42.3% | 30.9% | 30.4% |
| `price_calendar_ai` | 42.9% | 30.0% | 30.0% |

Auxiliary return-regression diagnostic from the same runner:

| input set | MAE | RMSE | R2 | direction accuracy |
| --- | ---: | ---: | ---: | ---: |
| `price_only` | 0.0175 | 0.0246 | -0.0449 | 52.0% |
| `price_ai` | 0.0182 | 0.0254 | -0.1161 | 48.6% |
| `price_calendar` | 0.0173 | 0.0243 | -0.0220 | 53.1% |
| `price_calendar_ai` | 0.0180 | 0.0252 | -0.1018 | 53.7% |

Interpretation: `price_ai` is the best fixed-band direction classifier in this run, modestly improving accuracy, balanced accuracy, and macro F1 over `price_only`. That improvement does not carry over to return regression diagnostics.

## Expected-Return Pipeline

| input set | model | MAE | RMSE | R2 | direction accuracy | trade frequency | strategy return | Sharpe | max drawdown |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `price_only` | Ridge | 0.0175 | 0.0246 | -0.0449 | 52.0% | 11.4% | 3.3% | 0.089 | -14.2% |
| `price_ai` | Ridge | 0.0182 | 0.0254 | -0.1161 | 48.6% | 20.6% | 3.1% | 0.077 | -20.7% |
| `price_calendar` | Ridge | 0.0173 | 0.0243 | -0.0220 | 53.1% | 21.1% | -6.2% | -0.188 | -16.8% |
| `price_calendar_ai` | Ridge | 0.0180 | 0.0252 | -0.1018 | 53.7% | 27.4% | 10.7% | 0.322 | -14.8% |
| `price_only` | HGB | 0.0187 | 0.0258 | -0.1535 | 50.9% | 32.0% | -25.9% | -0.769 | -32.8% |
| `price_ai` | HGB | 0.0189 | 0.0259 | -0.1640 | 46.9% | 30.9% | -30.9% | -0.997 | -33.6% |
| `price_calendar` | HGB | 0.0181 | 0.0252 | -0.0989 | 53.7% | 30.9% | 3.6% | 0.130 | -9.4% |
| `price_calendar_ai` | HGB | 0.0182 | 0.0247 | -0.0527 | 53.1% | 33.7% | -5.8% | -0.208 | -13.6% |

Interpretation: `price_ai` alone does not improve expected-return forecasting. The best trading result remains `price_calendar_ai` with Ridge.

## Volatility Pipeline

| input set | model | MAE | RMSE | R2 | Spearman | high-vol balanced accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `price_only` | Ridge | 0.0127 | 0.0173 | -0.0252 | -0.046 | 54.5% |
| `price_ai` | Ridge | 0.0125 | 0.0173 | -0.0245 | 0.027 | 56.0% |
| `price_calendar` | Ridge | 0.0126 | 0.0168 | 0.0411 | 0.160 | 59.0% |
| `price_calendar_ai` | Ridge | 0.0125 | 0.0168 | 0.0377 | 0.158 | 57.2% |
| `price_only` | HGB | 0.0129 | 0.0181 | -0.1248 | 0.020 | 51.3% |
| `price_ai` | HGB | 0.0131 | 0.0186 | -0.1775 | 0.003 | 48.8% |
| `price_calendar` | HGB | 0.0122 | 0.0170 | 0.0160 | 0.250 | 55.4% |
| `price_calendar_ai` | HGB | 0.0124 | 0.0169 | 0.0201 | 0.216 | 56.4% |

Interpretation: GLM scores without calendar features do not materially improve volatility forecasting. The volatility result is mainly driven by seasonality; GLM scores remain more useful as a complement to calendar controls than as a standalone replacement.
