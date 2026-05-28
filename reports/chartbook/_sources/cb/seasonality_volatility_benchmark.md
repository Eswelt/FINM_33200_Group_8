# Seasonality Volatility Benchmark

Run date: 2026-05-28.

This benchmark tests whether AI-read USDA scores and GDELT news scores improve volatility forecasting once the model already knows the crop-season calendar. It compares:

- `calendar_only`: calendar variables only.
- `calendar_ai_gdelt`: calendar variables plus USDA/GLM and GDELT scores.

No price variables are included in this benchmark.

## Results

| horizon | feature set | estimator | R2 | Spearman | high-vol balanced accuracy |
| --- | --- | --- | ---: | ---: | ---: |
| 1 week | `calendar_only` | HGB | 0.072 | 0.299 | 58.4% |
| 1 week | `calendar_only` | Ridge | 0.021 | 0.275 | 58.7% |
| 1 week | `calendar_ai_gdelt` | Ridge | 0.015 | 0.229 | 56.1% |
| 1 week | `calendar_ai_gdelt` | HGB | -0.068 | 0.225 | 59.5% |
| 4 weeks | `calendar_only` | HGB | 0.252 | 0.503 | 80.7% |
| 4 weeks | `calendar_only` | Ridge | 0.160 | 0.513 | 81.9% |
| 4 weeks | `calendar_ai_gdelt` | Ridge | 0.088 | 0.406 | 73.6% |
| 4 weeks | `calendar_ai_gdelt` | HGB | 0.046 | 0.319 | 74.5% |
| 13 weeks | `calendar_only` | HGB | 0.205 | 0.734 | 80.5% |
| 13 weeks | `calendar_only` | Ridge | 0.166 | 0.713 | 81.2% |
| 13 weeks | `calendar_ai_gdelt` | Ridge | 0.078 | 0.625 | 73.2% |
| 13 weeks | `calendar_ai_gdelt` | HGB | -0.008 | 0.634 | 63.2% |

## Interpretation

The clean benchmark shows that the seasonal calendar is the strongest standalone volatility predictor. Adding USDA/GLM and GDELT features does not consistently improve performance and often reduces out-of-sample R2 and high-volatility classification accuracy.

This does not imply that text or news features have no economic content. Rather, for the current sample and model design, the crop calendar captures the main volatility base rate, while AI/news scores add noisy, partly collinear signals.
