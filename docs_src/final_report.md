# Final Report: CORN ETF Trading Signal Pipeline

Generated: `2026-05-26 21:53:14 UTC`.

## How To Open

```bash
open reports/chartbook/index.html
open reports/html/corn_forecast_workflow.html
```

## Executive Summary

| item | result |
| --- | --- |
| Frozen sample | 2011-01-07 to 2026-05-15, 802 weekly rows |
| OOS window | 2023-01-06 to 2026-05-08, 175 weeks / 700 prediction rows |
| Main fixed-band classifier | price_only: balanced acc 36.9%, macro F1 28.5% |
| Best expected-return strategy | price_only_hgb: return 7.1%, Sharpe 0.353 |
| Best volatility-threshold strategy | k_1_price_calendar: return 6.2%, Sharpe 0.508 |
| Secondary binary direction result | C_price_weather_text_logit: return 6.7%, Sharpe 0.655 |

## Strategy Ranking Snapshot

| objective | run | strategy return | Sharpe |
| --- | --- | --- | --- |
| binary secondary | C_price_weather_text_logit | 6.7% | 0.655 |
| binary secondary | B_price_weather_hgb | 15.5% | 0.608 |
| vol threshold | k_1_price_calendar | 6.2% | 0.508 |
| binary secondary | C_price_weather_text_hgb | 7.8% | 0.399 |
| expected return | price_only_hgb | 7.1% | 0.353 |
| binary secondary | B_price_weather_logit | 0.5% | 0.085 |
| expected return | price_calendar_hgb | 0.4% | 0.025 |
| binary secondary | A_price_hgb | 0.4% | 0.020 |
| vol threshold | k_1_price_only | -0.6% | -0.074 |
| expected return | price_only_ridge | -0.5% | -0.136 |

## Main Result: Fixed 2 Percent Three-Class Target

| features | accuracy | balanced acc | macro F1 | down | flat | up | OOS rows | folds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| price_only | 32.6% | 36.9% | 28.5% | 20 | 131 | 24 | 175 | 14 |
| price_calendar | 30.9% | 30.2% | 25.2% | 20 | 131 | 24 | 175 | 14 |

Interpretation: the current fixed-band classifier is weak; the price-only baseline is stronger than price+calendar on balanced accuracy in this run.

## Auxiliary Expected-Return Strategy

| run | features | model | MAE | RMSE | R2 | direction acc | trade freq | strategy return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| price_only_hgb | price_only | hgb | 0.0140 | 0.0175 | -0.1209 | 54.3% | 27.4% | 7.1% | 0.353 | -8.0% |
| price_calendar_hgb | price_calendar | hgb | 0.0140 | 0.0177 | -0.1433 | 50.3% | 24.6% | 0.4% | 0.025 | -7.6% |
| price_only_ridge | price_only | ridge | 0.0138 | 0.0168 | -0.0316 | 42.3% | 1.7% | -0.5% | -0.136 | -1.8% |
| price_calendar_ridge | price_calendar | ridge | 0.0141 | 0.0170 | -0.0530 | 44.0% | 5.7% | -5.2% | -0.700 | -5.6% |

## Volatility-Adjusted Threshold Check

| run | k | features | accuracy | balanced acc | macro F1 | strategy return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k_1_price_calendar | 1.000 | price_calendar | 37.7% | 37.2% | 33.1% | 6.2% | 0.508 | -2.9% |
| k_1_price_only | 1.000 | price_only | 37.1% | 36.9% | 32.7% | -0.6% | -0.074 | -5.4% |

## Secondary Binary Direction Pipeline

| run | accuracy | balanced acc | F1 | ROC-AUC | strategy return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C_price_weather_text_logit | 47.4% | 47.9% | 28.1% | 47.9% | 6.7% | 0.655 | -5.3% |
| B_price_weather_hgb | 52.0% | 52.3% | 44.0% | 50.4% | 15.5% | 0.608 | -10.8% |
| C_price_weather_text_hgb | 51.4% | 51.7% | 43.0% | 51.4% | 7.8% | 0.399 | -5.2% |
| B_price_weather_logit | 53.7% | 54.3% | 31.9% | 50.9% | 0.5% | 0.085 | -2.4% |
| A_price_hgb | 50.3% | 50.4% | 47.3% | 49.8% | 0.4% | 0.020 | -13.4% |
| A_price_logit | 47.4% | 47.6% | 43.2% | 49.2% | -3.4% | -0.323 | -5.4% |

## Figures

### Final Class Distribution

![Final Class Distribution](figures/final_class_distribution.png)

### Final Strategy Sharpe

![Final Strategy Sharpe](figures/final_strategy_sharpe.png)

### Final Strategy Return

![Final Strategy Return](figures/final_strategy_return.png)

### Final Expected Return Cumulative

![Final Expected Return Cumulative](figures/final_expected_return_cumulative.png)

### Final Threshold Cumulative

![Final Threshold Cumulative](figures/final_threshold_cumulative.png)

### Final Fixed Target Confusion

![Final Fixed Target Confusion](figures/final_fixed_target_confusion.png)

## Data And Code Coverage

| rows | cols | first_week | last_week | price_features | calendar_features | weather_features | text_features | ai_features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 802 | 52 | 2011-01-07 | 2026-05-15 | 11 | 9 | 10 | 8 | 7 |

| artifact | exists | rows | cols |
| --- | --- | --- | --- |
| data/raw/prices_CORN.csv | yes | 4014 | 7 |
| data/raw/usda_releases.csv | yes | 1606 | 5 |
| data/interim/weather_weekly.parquet | yes | 802 | 11 |
| data/interim/ai_weekly.parquet | yes | 789 | 8 |
| data/processed/feature_panel.parquet | yes | 802 | 52 |
| reports/price_target_predictions.csv | yes | 700 | 13 |
| reports/expected_return_predictions.csv | yes | 700 | 18 |
| reports/threshold_selection_predictions.csv | yes | 350 | 22 |
| reports/predictions.csv | yes | 1050 | 19 |

| area | files | role |
| --- | --- | --- |
| Task graph | dodo.py | Single pydoit entrypoint for data, models, reports, ChartBook, tests. |
| CLI orchestration | src/corn_forecast/cli.py | Command surface used by pydoit; now reuses cached prices when available. |
| Configuration | src/corn_forecast/config.py | Research defaults, dates, paths, thresholds, feature-set names. |
| Data adapters | data/prices.py, data/weather.py, data/usda.py | Price pulls, weather cache/demo adapter, USDA text adapter. |
| Feature panel | src/corn_forecast/features.py | Weekly price, calendar, weather, text, AI feature joins. |
| Main target test | src/corn_forecast/price_target_tests.py | Fixed 2 percent three-class target plus return-regression diagnostics. |
| Return strategy | src/corn_forecast/expected_return_strategy.py | Expected-return models, trading threshold, strategy returns. |
| Threshold robustness | src/corn_forecast/threshold_selection.py | Volatility-adjusted 3-class target selection. |
| Binary direction | src/corn_forecast/models.py, strategy.py | Secondary up/down classifier and trading backtest. |
| WWCB/AI text | src/corn_forecast/text/*.py, scripts/*.py | PDF download/parse and GLM/mock structured AI features. |
| Report generation | src/corn_forecast/reports.py, scripts/build_project_notebook.py | Figures, markdown, notebook, standalone HTML. |
| Tests | tests/*.py | 37 tests covering adapters, features, models, targets, strategy, parser, AI features. |

## Problems And Caveats

- The fixed 2 percent target is imbalanced: 131 of 175 OOS weeks are flat. Accuracy alone is not enough.
- Calendar seasonality does not improve the main fixed-band classifier in this run; balanced accuracy is 6.7% lower than price-only.
- All expected-return regressions have negative OOS R2, so trading metrics should be treated as fragile.
- The binary direction results use a different target (`target_up_next`) and are secondary, not the main 2 percent classification result.
- Optional weather/text/AI data exist locally, but the main default feature sets are still `price_only` and `price_calendar`.
- Generated report and data outputs are ignored by git; rerun `uv run --extra dev doit docs` before submission.

## Reproducibility Commands

```bash
uv sync --python 3.12 --extra dev --extra docs
uv run --extra dev doit research
uv run --extra dev doit docs
uv run --extra dev doit tests
```
