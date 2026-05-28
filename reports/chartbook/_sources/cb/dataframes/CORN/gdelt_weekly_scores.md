# Dataframe: `CORN:gdelt_weekly_scores` - GDELT Weekly News Scores

# Final Write-up: CORN ETF Volatility Forecasting

Updated: `2026-05-28`.

## Executive Summary

This project studies whether agricultural information can help forecast the risk environment of `CORN`, the Teucrium Corn ETF. After testing direction classification, expected-return forecasting, and volatility forecasting, we choose **future realized volatility** as the final prediction target.

The empirical result is clear:

- Return direction and expected return are difficult to predict reliably.
- Volatility becomes more predictable as the forecast horizon lengthens.
- Seasonality is the dominant source of predictability.
- AI-read USDA report scores and GDELT news scores do not consistently improve on a clean calendar-only volatility benchmark.

The main conclusion is that for an asset strongly tied to an agricultural production cycle, **knowing the crop-season window is more important than adding noisy text or news features**. AI/NLP features can still be useful for qualitative interpretation, but in our current out-of-sample tests they do not beat the simpler seasonal signal.

## Prediction Target

The final target is forward realized volatility:

```text
1-week volatility = abs(next weekly log return)
4-week volatility = sqrt(sum of squared weekly returns over the next 4 weeks)
13-week volatility = sqrt(sum of squared weekly returns over the next 13 weeks)
```

The 13-week target represents the risk environment over the next quarter, not the return or volatility of only the 13th week.

## Data And Features

The model panel uses weekly observations from 2011-01-01 to 2026-05-15. The out-of-sample window starts after 2022-12-31 and uses expanding walk-forward validation with 13-week test windows.

We tested these feature groups:

| feature group | description |
| --- | --- |
| price | Lagged CORN returns, rolling volatility, momentum, and volume change. |
| calendar | Month, quarter, week-of-year cyclic terms, planting season, pollination risk season, harvest season, and winter storage season. |
| USDA/GLM | USDA Weekly Weather and Crop Bulletin text parsed from PDFs and scored by GLM into crop-risk variables. |
| GDELT | Weekly corn-market news scores for relevance, supply risk, demand strength, ethanol/export signals, and trade policy risk. |

The core tested combinations include `price_only`, `price_ai`, `price_gdelt`, `price_ai_gdelt`, `price_calendar`, `price_calendar_ai`, `price_calendar_gdelt`, and `price_calendar_ai_gdelt`. We also ran a clean seasonality benchmark comparing `calendar_only` against `calendar_ai_gdelt`.

## Main Volatility Results

The best official volatility runs by horizon are:

| horizon | best run | R2 | Spearman | high-vol balanced accuracy |
| --- | --- | ---: | ---: | ---: |
| 1 week | `price_calendar_gdelt` + HGB | 0.083 | 0.211 | 58.3% |
| 4 weeks | `price_calendar` + Ridge | 0.233 | 0.420 | 68.6% |
| 13 weeks | `price_calendar_ai_gdelt` + HGB | 0.266 | 0.687 | 69.9% |

The result improves as the horizon moves from one week to multi-week windows. This supports the idea that agricultural information is more useful for forecasting the width of the return distribution over a crop-risk window than for predicting next week's direction.

## Seasonality Benchmark

To test whether AI and news features add value beyond seasonality, we ran a clean benchmark with no price variables:

| horizon | best `calendar_only` R2 | best `calendar_ai_gdelt` R2 | conclusion |
| --- | ---: | ---: | --- |
| 1 week | 0.072 | 0.015 | Calendar is better. |
| 4 weeks | 0.252 | 0.088 | Calendar is much better. |
| 13 weeks | 0.205 | 0.078 | Calendar is much better. |

High-volatility classification shows the same pattern:

| horizon | best `calendar_only` high-vol balanced accuracy | best `calendar_ai_gdelt` high-vol balanced accuracy |
| --- | ---: | ---: |
| 1 week | 58.7% | 59.5% |
| 4 weeks | 81.9% | 74.5% |
| 13 weeks | 81.2% | 73.2% |

The clean benchmark changes the interpretation of the project. AI-read USDA scores and GDELT news scores are not a stable improvement over the crop calendar. The dominant signal is the seasonal structure itself.

## Is High Volatility Always In The Same Season?

High volatility is strongly seasonal, but not identical every year.

Average 13-week realized volatility by crop-season window:

| starting period | mean 13-week volatility | high-vol rate |
| --- | ---: | ---: |
| planting | 0.137 | 67.2% |
| other | 0.109 | 41.8% |
| pollination/weather-risk | 0.097 | 32.0% |
| winter storage | 0.087 | 19.6% |
| harvest | 0.069 | 9.7% |

Average 13-week realized volatility by calendar quarter:

| starting quarter | mean 13-week volatility | high-vol rate |
| --- | ---: | ---: |
| Q1 | 0.097 | 28.5% |
| Q2 | 0.133 | 66.2% |
| Q3 | 0.079 | 13.6% |
| Q4 | 0.072 | 12.2% |

Planting and Q2 are the most common high-volatility windows, but there are exceptions. For example, 2020 had stronger high-volatility concentration around harvest, while 2021 had more high-volatility weeks around winter storage. This means seasonality is not a perfect deterministic rule, but it is the strongest and most stable predictor in our tests.

## Why AI And News Features May Underperform

Several mechanisms could explain why GLM/GDELT features reduce performance relative to the calendar-only benchmark:

1. **Seasonality already captures the main base rate.** CORN volatility is heavily driven by the agricultural production cycle. Once the model knows the crop window, additional text signals may add limited incremental information.

2. **Text features are noisy relative to the target.** USDA reports and GDELT news can describe important conditions, but converting narrative text into weekly numeric scores introduces measurement error.

3. **Small out-of-sample sample size.** The post-2022 test window has limited crisis and crop-shock examples. Flexible models can overfit rare text/news patterns that do not repeat.

4. **GDELT may measure attention as much as fundamentals.** News intensity can rise after prices already move, or around broad market stories that are not specific enough to improve CORN volatility forecasts.

5. **AI scores can be collinear with season.** Planting delay, heat stress, harvest delay, and yield risk naturally occur in specific crop windows. If these features mostly restate the calendar with noise, the model can become less stable.

6. **Timing alignment is difficult.** Weekly aggregation may blur whether a report or news item was available before the market repriced the risk.

These explanations do not mean AI is useless. They mean that in this project, the most robust quantitative signal is seasonal timing, while AI/NLP features are better treated as qualitative context or candidate features for future refinement.

## Direction And Return Experiments

We also tested direction classification and expected-return prediction. They are not the final target because performance is weaker and less stable.

Best direction results:

| horizon | best input set | balanced accuracy | macro F1 |
| --- | --- | ---: | ---: |
| 1 week | `price_ai` | 32.6% | 32.6% |
| 4 weeks | `price_calendar_ai_gdelt` | 46.0% | 44.8% |
| 13 weeks | `price_calendar` | 46.6% | 44.8% |

Best one-week expected-return trading result:

| best run | strategy return | Sharpe | R2 |
| --- | ---: | ---: | ---: |
| `price_calendar_ai_gdelt` + HGB | 18.3% | 0.481 | -0.028 |

The expected-return R2 remains negative, so we do not present return forecasting as the main empirical success.

## Investment Interpretation

Volatility prediction does not tell an investor whether to buy or sell CORN. Its value is as a risk overlay:

- Reduce position size when predicted volatility is high.
- Require stronger return signals before trading in high-risk seasonal windows.
- Use high-volatility forecasts to inform hedging or options-related decisions.
- Recognize that CORN risk is structurally higher in parts of the crop cycle.

The final investment lesson is:

> For seasonally driven assets, the calendar itself can be more informative than complex AI-read news features. A simple seasonal risk model may be more robust than a larger model that adds noisy text signals.

## AI Usage

Human team members made the main research decisions, including choosing the prediction target, defining feature groups, interpreting the economic meaning of the results, and deciding which findings should be emphasized.

Claude Code and Codex were used as coding assistants to batch-run experiments, integrate feature files, regenerate model outputs, update ChartBook pages, and draft reproducible write-ups from the experiment results.

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
| How is data pulled?            | Prepared by the project feature pipeline and staged under data/interim.                                                    |
| Data available up to (min)     | N/A                                                             |
| Data available up to (max)     | N/A                                                             |
| Dataframe Path                 | /private/tmp/FINM_33200_Group_8_three_inputs/data/interim/gdelt_weekly_scores.parquet                                                   |


**Linked Charts:**

- None


## Pipeline Manifest

| Pipeline Name                   | CORN ETF Volatility Forecasting Pipeline                       |
|---------------------------------|--------------------------------------------------------|
| Pipeline ID                     | [CORN](../../../index.md)              |
| Lead Pipeline Developer         | FINM 33200 Group 8             |
| Contributors                    | FINM 33200 Group 8           |
| Git Repo URL                    | local                        |
| Pipeline Web Page               | <a href="file:///private/tmp/FINM_33200_Group_8_three_inputs/docs/index.html">Pipeline Web Page      |
| Date of Last Code Update        | 2026-05-27 23:19:14           |
| OS Compatibility                |  |
| Linked Dataframes               |  [CORN:feature_panel](../../dataframes/CORN/feature_panel.md)<br>  [CORN:price_target_predictions](../../dataframes/CORN/price_target_predictions.md)<br>  [CORN:expected_return_predictions](../../dataframes/CORN/expected_return_predictions.md)<br>  [CORN:volatility_predictions](../../dataframes/CORN/volatility_predictions.md)<br>  [CORN:horizon_robustness_metrics](../../dataframes/CORN/horizon_robustness_metrics.md)<br>  [CORN:horizon_robustness_predictions](../../dataframes/CORN/horizon_robustness_predictions.md)<br>  [CORN:gdelt_weekly_scores](../../dataframes/CORN/gdelt_weekly_scores.md)<br>  |


