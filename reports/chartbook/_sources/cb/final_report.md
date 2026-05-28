# Current Write-up: CORN ETF Trading Signal Pipeline

Updated: `2026-05-27`.

## Executive Summary

This project studies whether structured agricultural information can improve CORN ETF trading-signal research. The current model results use three completed data blocks:

- Historical CORN ETF prices from Yahoo Finance.
- Deterministic corn-season calendar features.
- USDA Weekly Weather and Crop Bulletin text parsed from PDFs and scored with GLM into seven crop-risk features.

One additional data block has been uploaded but is not yet integrated into the model comparison:

- GDELT weekly news scores.

One planned data block is still pending from teammates:

- Weather features.

The main finding so far is that USDA/seasonal information is more useful for risk and horizon-regime analysis than for precise one-week return prediction. One-week return forecasts remain weak, but 4-week and 13-week volatility forecasts improve materially when crop-season features are included. The next model iteration should add GDELT and weather as explicit input blocks.

## Research Question

The project asks whether agricultural information can improve trading decisions for `CORN`, the Teucrium Corn ETF. We frame this as a trading-signal problem rather than a raw price-level prediction problem.

The completed experiments compare four input sets:

| input set | description |
| --- | --- |
| `price_only` | Historical CORN ETF price features. |
| `price_ai` | Price features plus GLM-extracted USDA report scores. |
| `price_calendar` | Price features plus deterministic crop-season calendar controls. |
| `price_calendar_ai` | Price, calendar, and GLM USDA scores. |

The GLM scores are derived from parsed USDA Weekly Weather and Crop Bulletin text. They measure moisture stress, heat stress, excess rain risk, planting delay risk, harvest delay risk, yield risk, and crop condition trend.

## Validation Design

The sample is frozen at:

```text
2011-01-01 to 2026-05-15
```

The out-of-sample window starts after:

```text
2022-12-31
```

Validation uses expanding walk-forward splits:

- 13-week test windows.
- 13-week retrain step.
- No random train/test split.
- Features are point-in-time at the prediction week.

The horizon robustness experiment keeps a weekly prediction cadence but changes the forward target horizon:

- 1 week.
- 4 weeks.
- 13 weeks.

For 4-week and 13-week targets, adjacent predictions overlap. Those results should be read as horizon-sensitivity evidence rather than independent quarterly observations.

## Pipeline 1: Direction Classification

The main direction target is a fixed-threshold three-class label:

```text
Y =  1 if forward return >= +2%
Y =  0 if -2% < forward return < +2%
Y = -1 if forward return <= -2%
```

### One-week direction results

| input set | accuracy | balanced accuracy | macro F1 |
| --- | ---: | ---: | ---: |
| `price_only` | 46.9% | 31.9% | 31.4% |
| `price_ai` | 49.7% | 32.6% | 32.6% |
| `price_calendar` | 42.3% | 30.9% | 30.4% |
| `price_calendar_ai` | 42.9% | 30.0% | 30.0% |

For the one-week direction task, `price_ai` is the best of the tested inputs, but the improvement is modest. This is evidence that USDA/GLM scores contain some directional information, but the one-week fixed-band classification task remains hard.

### Horizon robustness for direction

| horizon | best input set | balanced accuracy | macro F1 |
| --- | --- | ---: | ---: |
| 1 week | `price_ai` | 32.6% | 32.6% |
| 4 weeks | `price_calendar_ai` | 43.5% | 43.0% |
| 13 weeks | `price_calendar` | 46.6% | 44.8% |

The direction task improves when the target horizon is extended. This is economically plausible: crop reports and seasonal risk windows may not move the ETF immediately in the next week, but they can matter over a 4-week or 13-week horizon.

## Pipeline 2: Expected Return

The expected-return pipeline directly forecasts forward cumulative log return and trades only when predicted return clears transaction cost plus a buffer.

The one-week expected-return results are weak statistically:

| best one-week run | strategy return | Sharpe | R2 |
| --- | ---: | ---: | ---: |
| `price_calendar_ai` + Ridge | 10.7% | 0.322 | -0.102 |

The trading outcome is positive for that run, but the return forecast R2 remains negative. The 4-week and 13-week expected-return runs also have negative R2 and poor strategy Sharpe. We therefore do not treat expected-return forecasting as the main project result.

Interpretation:

> The current features may help identify some risk regimes, but they do not reliably estimate return levels.

## Pipeline 3: Volatility Forecasting

The volatility pipeline predicts future realized volatility:

```text
1-week volatility = abs(next 1-week return)
4-week / 13-week volatility = sqrt(sum of squared forward weekly returns)
```

It also classifies high-volatility periods using each training window's 70th percentile volatility threshold.

### Volatility results by horizon

| horizon | best R2 run | R2 | Spearman | high-vol balanced accuracy |
| --- | --- | ---: | ---: | ---: |
| 1 week | `price_calendar` + Ridge | 0.041 | 0.160 | 59.0% |
| 4 weeks | `price_calendar` + Ridge | 0.233 | 0.420 | 68.6% |
| 13 weeks | `price_calendar` + HGB | 0.241 | 0.687 | 70.6% |

The volatility pipeline is the strongest current result. Forecast quality improves at 4-week and 13-week horizons, especially when crop-season calendar features are included.

### Volatility input comparison

| input set | conclusion |
| --- | --- |
| `price_only` | Weak baseline; limited volatility predictability. |
| `price_ai` | GLM scores alone do not materially improve volatility forecasting. |
| `price_calendar` | Most stable volatility signal; seasonality is the main driver. |
| `price_calendar_ai` | Competitive with calendar and sometimes better for high-volatility flags, but not consistently better than calendar alone. |

This suggests that USDA/GLM scores are best interpreted inside the crop calendar. A report about planting delay, heat stress, or harvest disruption has different meaning depending on the crop stage.

## Why Volatility Is More Predictable Than Return

USDA reports and crop-season signals often change uncertainty before they give a clean directional edge. A drought, planting delay, or crop condition deterioration may widen the market's risk distribution without saying exactly whether next week's ETF return will be positive or negative.

The project evidence matches that logic:

- One-week return and direction prediction remain noisy.
- Volatility prediction improves with longer horizons.
- Calendar features are especially important for risk prediction.
- GLM USDA scores provide some directional signal and may help high-volatility flagging, but they do not replace seasonality.

For investors, the volatility model is useful as a risk overlay:

- Scale position size down when predicted volatility is high.
- Require a stronger return signal before trading in high-risk windows.
- Flag periods where options or hedging may be more relevant than directional ETF exposure.

## Current Limitations

- GDELT weekly news scores have been uploaded but are not yet included in the reported model runs.
- Weather features are not yet included.
- Multi-week horizon results use overlapping targets, so they should not be treated as independent quarterly observations.
- Expected-return R2 remains negative across horizons.
- GLM scores are model-generated structured features, not ground-truth agronomic measurements.
- Current results should be presented as evidence about signal shape and risk regimes, not as a deployable trading strategy.

## Next Steps

The next iteration should add:

1. GDELT news features as a separate input block.
2. Weather features as a separate input block.
3. A final comparison table:
   - price only
   - price + GLM
   - price + calendar
   - price + calendar + GLM
   - price + calendar + GLM + GDELT
   - price + calendar + GLM + weather
   - full model
4. A concise final conclusion focused on whether new information improves:
   - direction classification,
   - expected-return trading,
   - volatility/risk-regime forecasting.

## Reproducibility

Core commands:

```bash
uv sync --python 3.12 --extra dev --extra docs
uv run --extra dev doit fetch_prices build_features
PYTHONPATH=src uv run python scripts/run_horizon_robustness.py
uv run pytest
```

ChartBook build:

```bash
PYTHONPATH=src uv run --extra docs chartbook build reports/chartbook -f --project-dir .
PYTHONPATH=src uv run python scripts/fix_chartbook_assets.py
```
