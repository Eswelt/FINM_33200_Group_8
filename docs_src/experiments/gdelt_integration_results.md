# GDELT Integration Results

Run date: 2026-05-28.

This run adds GDELT weekly corn-market news scores to the existing no-weather feature grid. The tested input sets are:

- `price_only`
- `price_ai`
- `price_gdelt`
- `price_ai_gdelt`
- `price_calendar`
- `price_calendar_ai`
- `price_calendar_gdelt`
- `price_calendar_ai_gdelt`

GDELT weekly dates were aligned to the Friday weekly prediction calendar before merging into the feature panel.

## One-week Direction

| input set | accuracy | balanced accuracy | macro F1 |
| --- | ---: | ---: | ---: |
| `price_ai` | 49.7% | 32.6% | 32.6% |
| `price_gdelt` | 45.1% | 32.2% | 31.9% |
| `price_ai_gdelt` | 46.3% | 32.1% | 32.0% |
| `price_only` | 46.9% | 31.9% | 31.4% |
| `price_calendar` | 42.3% | 30.9% | 30.4% |
| `price_calendar_gdelt` | 38.9% | 30.8% | 29.3% |
| `price_calendar_ai` | 42.9% | 30.0% | 30.0% |
| `price_calendar_ai_gdelt` | 40.0% | 29.8% | 29.1% |

GDELT does not improve the one-week fixed-band direction classifier once calendar and GLM features are included. The best one-week direction model remains `price_ai`.

## One-week Expected Return

Best runs by trading Sharpe:

| input set | model | R2 | direction accuracy | strategy return | Sharpe |
| --- | --- | ---: | ---: | ---: | ---: |
| `price_calendar_ai_gdelt` | HGB | -0.0279 | 54.9% | 18.3% | 0.481 |
| `price_calendar_ai_gdelt` | Ridge | -0.1037 | 55.4% | 14.2% | 0.406 |
| `price_calendar_ai` | Ridge | -0.1018 | 53.7% | 10.7% | 0.322 |

GDELT improves the best one-week trading result when combined with calendar and GLM scores. The return R2 is still negative, so this should be framed as a trading-filter result rather than a precise return-forecasting result.

## Volatility

Best volatility runs by horizon:

| horizon | best run | R2 | Spearman | high-vol balanced accuracy |
| --- | --- | ---: | ---: | ---: |
| 1 week | `price_calendar_gdelt` + HGB | 0.083 | 0.211 | 58.3% |
| 4 weeks | `price_calendar` + Ridge | 0.233 | 0.420 | 68.6% |
| 13 weeks | `price_calendar_ai_gdelt` + HGB | 0.266 | 0.687 | 69.9% |

GDELT helps most clearly in the one-week and 13-week volatility settings when used with calendar features. The 4-week volatility result is still led by calendar-only features, suggesting that crop-season timing remains the main volatility signal.

## Takeaway

GDELT is not a standalone replacement for crop-season controls or USDA/GLM scores. Its value appears in combined models:

- It improves the best one-week expected-return trading result.
- It improves the best one-week volatility R2.
- It improves the best 13-week volatility R2.
- It improves the best 4-week direction classifier when combined with calendar and GLM.

The current story is therefore: calendar features provide the main crop-cycle structure, GLM USDA scores add crop-condition risk signals, and GDELT adds a market-news layer that is useful in some combined models.
