# Dataframe: `CORN:gdelt_weekly_scores` - GDELT Weekly News Scores

# Current Write-up: CORN ETF Trading Signal Pipeline

Updated: `2026-05-28`.

## Executive Summary

This project studies whether structured agricultural information can improve CORN ETF trading-signal research. The current model results use four completed data blocks:

- Historical CORN ETF prices from Yahoo Finance.
- Deterministic corn-season calendar features.
- USDA Weekly Weather and Crop Bulletin text parsed from PDFs and scored with GLM into seven crop-risk features.
- GDELT weekly corn-market news scores.

One planned data block is still pending from teammates:

- Weather features.

The main finding so far is that USDA, GDELT, and seasonal information are more useful for risk and horizon-regime analysis than for precise one-week return prediction. One-week return forecasts remain weak statistically, but GDELT improves the best one-week trading result and improves several volatility/risk-regime tests. The next model iteration should add weather as the remaining explicit input block.

## Research Question

The project asks whether agricultural information can improve trading decisions for `CORN`, the Teucrium Corn ETF. We frame this as a trading-signal problem rather than a raw price-level prediction problem.

The completed experiments compare eight input sets:

| input set | description |
| --- | --- |
| `price_only` | Historical CORN ETF price features. |
| `price_ai` | Price features plus GLM-extracted USDA report scores. |
| `price_calendar` | Price features plus deterministic crop-season calendar controls. |
| `price_gdelt` | Price features plus GDELT weekly news scores. |
| `price_ai_gdelt` | Price features plus GLM USDA scores and GDELT news scores. |
| `price_calendar_ai` | Price, calendar, and GLM USDA scores. |
| `price_calendar_gdelt` | Price, calendar, and GDELT news scores. |
| `price_calendar_ai_gdelt` | Price, calendar, GLM USDA scores, and GDELT news scores. |

The GLM scores are derived from parsed USDA Weekly Weather and Crop Bulletin text. They measure moisture stress, heat stress, excess rain risk, planting delay risk, harvest delay risk, yield risk, and crop condition trend. The GDELT scores summarize relevance, yield/supply risk, inventory tightness, demand strength, ethanol/export signals, and trade policy risk.

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
| `price_gdelt` | 45.1% | 32.2% | 31.9% |
| `price_ai_gdelt` | 46.3% | 32.1% | 32.0% |
| `price_calendar` | 42.3% | 30.9% | 30.4% |
| `price_calendar_gdelt` | 38.9% | 30.8% | 29.3% |
| `price_calendar_ai` | 42.9% | 30.0% | 30.0% |
| `price_calendar_ai_gdelt` | 40.0% | 29.8% | 29.1% |

For the one-week direction task, `price_ai` is still the best of the tested inputs. GDELT alone is competitive with `price_only`, but adding GDELT does not improve the one-week fixed-band classifier once calendar and GLM features are included.

### Horizon robustness for direction

| horizon | best input set | balanced accuracy | macro F1 |
| --- | --- | ---: | ---: |
| 1 week | `price_ai` | 32.6% | 32.6% |
| 4 weeks | `price_calendar_ai_gdelt` | 46.0% | 44.8% |
| 13 weeks | `price_calendar` | 46.6% | 44.8% |

The direction task improves when the target horizon is extended. GDELT is most helpful at the 4-week horizon when combined with calendar and GLM features. This is economically plausible: crop reports, news, and seasonal risk windows may not move the ETF immediately in the next week, but they can matter over a multi-week horizon.

## Pipeline 2: Expected Return

The expected-return pipeline directly forecasts forward cumulative log return and trades only when predicted return clears transaction cost plus a buffer.

The one-week expected-return results are weak statistically:

| best one-week run | strategy return | Sharpe | R2 |
| --- | ---: | ---: | ---: |
| `price_calendar_ai_gdelt` + HGB | 18.3% | 0.481 | -0.028 |

GDELT improves the best one-week trading result, especially when combined with calendar and GLM features. However, the return forecast R2 remains negative. The 4-week and 13-week expected-return runs also have negative R2 and poor strategy Sharpe. We therefore do not treat expected-return forecasting as the main project result.

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
| 1 week | `price_calendar_gdelt` + HGB | 0.083 | 0.211 | 58.3% |
| 4 weeks | `price_calendar` + Ridge | 0.233 | 0.420 | 68.6% |
| 13 weeks | `price_calendar_ai_gdelt` + HGB | 0.266 | 0.687 | 69.9% |

The volatility pipeline is the strongest current result. Forecast quality improves at 4-week and 13-week horizons, especially when crop-season calendar features are included.

### Volatility input comparison

| input set | conclusion |
| --- | --- |
| `price_only` | Weak baseline; limited volatility predictability. |
| `price_ai` | GLM scores alone do not materially improve volatility forecasting. |
| `price_gdelt` | GDELT alone is weak, but it improves several combined feature sets. |
| `price_calendar` | Most stable volatility signal; seasonality is the main driver. |
| `price_calendar_ai` | Competitive with calendar and sometimes better for high-volatility flags, but not consistently better than calendar alone. |
| `price_calendar_gdelt` | Best one-week volatility R2 after adding GDELT. |
| `price_calendar_ai_gdelt` | Best 13-week volatility R2 and best 4-week direction classifier. |

This suggests that USDA/GLM and GDELT scores are best interpreted inside the crop calendar. A report about planting delay, heat stress, export demand, or trade policy has different meaning depending on the crop stage.

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

- Weather features are not yet included.
- Multi-week horizon results use overlapping targets, so they should not be treated as independent quarterly observations.
- Expected-return R2 remains negative across horizons.
- GLM scores are model-generated structured features, not ground-truth agronomic measurements.
- Current results should be presented as evidence about signal shape and risk regimes, not as a deployable trading strategy.

## Next Steps

The next iteration should add:

1. Weather features as a separate input block.
2. A final comparison table:
   - price only
   - price + GLM
   - price + calendar
   - price + calendar + GLM
   - price + calendar + GLM + GDELT
   - price + calendar + GLM + weather
   - full model
3. A concise final conclusion focused on whether new information improves:
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



## DataFrame Glimpse

```
Rows: 577
Columns: 7
$ week                       <str> '2026-03-30'
$ relevance_score            <f64> 1.9090909090909092
$ yield_supply_risk          <f64> 0.8888888888888888
$ inventory_supply_tightness <f64> 0.42857142857142855
$ demand_strength            <f64> 1.0317460317460319
$ ethanol_export_signal      <f64> 1.0793650793650793
$ trade_policy_risk          <f64> 0.015873015873015872


```

## Dataframe Manifest

| Dataframe Name                 | GDELT Weekly News Scores                                                   |
|--------------------------------|--------------------------------------------------------------------------------------|
| Dataframe ID                   | [gdelt_weekly_scores](../dataframes/CORN/gdelt_weekly_scores.md)                                       |
| Data Sources                   | GDELT                                        |
| Data Providers                 | FINM 33200 Group 8                                      |
| Links to Providers             |                              |
| Topic Tags                     | Gdelt, News, Corn, Integrated Feature Block                                          |
| Type of Data Access            |                                   |
| How is data pulled?            | Prepared by teammate feature pipeline and staged under data/interim.                                                    |
| Data available up to (min)     | N/A                                                             |
| Data available up to (max)     | N/A                                                             |
| Dataframe Path                 | /private/tmp/FINM_33200_Group_8_three_inputs/data/interim/gdelt_weekly_scores.parquet                                                   |


**Linked Charts:**

- None


## Pipeline Manifest

| Pipeline Name                   | CORN ETF Trading Signal Pipeline                       |
|---------------------------------|--------------------------------------------------------|
| Pipeline ID                     | [CORN](../../../index.md)              |
| Lead Pipeline Developer         | FINM 33200 Group 8             |
| Contributors                    | FINM 33200 Group 8           |
| Git Repo URL                    | local                        |
| Pipeline Web Page               | <a href="file:///private/tmp/FINM_33200_Group_8_three_inputs/docs/index.html">Pipeline Web Page      |
| Date of Last Code Update        | 2026-05-27 22:39:20           |
| OS Compatibility                |  |
| Linked Dataframes               |  [CORN:feature_panel](../../dataframes/CORN/feature_panel.md)<br>  [CORN:price_target_predictions](../../dataframes/CORN/price_target_predictions.md)<br>  [CORN:expected_return_predictions](../../dataframes/CORN/expected_return_predictions.md)<br>  [CORN:volatility_predictions](../../dataframes/CORN/volatility_predictions.md)<br>  [CORN:horizon_robustness_metrics](../../dataframes/CORN/horizon_robustness_metrics.md)<br>  [CORN:horizon_robustness_predictions](../../dataframes/CORN/horizon_robustness_predictions.md)<br>  [CORN:gdelt_weekly_scores](../../dataframes/CORN/gdelt_weekly_scores.md)<br>  |


