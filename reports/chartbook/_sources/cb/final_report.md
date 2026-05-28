# Final Report: CORN ETF Trading Signal Pipeline

Generated: `2026-05-28 05:30:19 UTC`.

## How To Open

```bash
open reports/chartbook/index.html
open reports/html/corn_forecast_workflow.html
```

## Executive Summary

| item | result |
| --- | --- |
| Frozen sample | 2011-01-07 to 2026-05-15, 802 weekly rows |
| OOS window | 2023-01-06 to 2026-05-08, 175 weeks / 2800 prediction rows |
| Main fixed-band classifier | price_ai: balanced acc 32.6%, macro F1 32.6% |
| Best expected-return strategy | price_calendar_ai_gdelt_hgb: return 18.3%, Sharpe 0.481 |
| Best volatility forecast | price_only_ridge: R2 -0.0249, high-vol balanced acc 50.0% |
| Best volatility-threshold strategy | k_1_price_calendar: return 6.2%, Sharpe 0.508 |
| Secondary binary direction result | C_price_weather_text_logit: return 6.7%, Sharpe 0.655 |

## Project Architecture And File Directory

| directory | contains | role |
| --- | --- | --- |
| ./ | README.md, pyproject.toml, dodo.py, chartbook.toml | Project metadata, dependencies, task graph, and ChartBook configuration. |
| src/corn_forecast/ | cli.py, features.py, models.py, strategy.py | Forecasting package and command surface used by pydoit. |
| src/corn_forecast/data/ | prices.py, weather.py, usda.py | Data adapters for price, weather, and USDA release inputs. |
| src/corn_forecast/text/ | wwcb*.py, ai_features.py | Optional WWCB parsing and AI feature extraction helpers. |
| scripts/ | build_project_notebook.py, run_horizon_robustness.py, WWCB scripts | One-off report, robustness, and text-processing scripts. |
| data/raw/ | prices_CORN.csv, usda_releases.csv | Frozen raw inputs used by the default local workflow. |
| data/interim/ | weather_weekly.parquet, ai_weekly.parquet, gdelt_weekly_scores.parquet | Staged weekly feature blocks before the final modeling panel. |
| data/processed/ | feature_panel.parquet | Final weekly modeling panel consumed by all model tasks. |
| experiments/ | *_results.md | Experiment notes and robustness write-ups included in ChartBook. |
| docs_src/ | project_workflow.md, final_report.md, data_glimpses.md, figures/ | Markdown and assets that ChartBook turns into the HTML site. |
| reports/ | metrics, predictions, figures, notebooks, html, chartbook | Generated model outputs, notebook, standalone HTML, and ChartBook site. |
| tests/ | test_*.py | Unit and smoke tests for adapters, feature engineering, models, and reports. |

## Workflow Outputs Generated

| workflow | status | main outputs |
| --- | --- | --- |
| research | ready | reports/price_target_tests.json, reports/price_target_predictions.csv, reports/expected_return_metrics.json, reports/expected_return_predictions.csv, reports/volatility_metrics.json ... |
| docs | ready | reports/notebooks/corn_forecast_workflow.ipynb, reports/html/corn_forecast_workflow.html, docs_src/final_report.md, docs_src/data_glimpses.md, reports/chartbook/index.html |

## Strategy Ranking Snapshot

| objective | run | strategy return | Sharpe |
| --- | --- | --- | --- |
| binary secondary | C_price_weather_text_logit | 6.7% | 0.655 |
| binary secondary | B_price_weather_hgb | 15.5% | 0.608 |
| vol threshold | k_1_price_calendar | 6.2% | 0.508 |
| expected return | price_calendar_ai_gdelt_hgb | 18.3% | 0.481 |
| expected return | price_calendar_ai_gdelt_ridge | 14.2% | 0.406 |
| binary secondary | C_price_weather_text_hgb | 7.8% | 0.399 |
| expected return | price_calendar_ai_ridge | 10.7% | 0.322 |
| expected return | price_calendar_hgb | 3.6% | 0.130 |
| expected return | price_only_ridge | 3.3% | 0.089 |
| binary secondary | B_price_weather_logit | 0.5% | 0.085 |

## Main Result: Fixed 2 Percent Three-Class Target

| features | accuracy | balanced acc | macro F1 | down | flat | up | OOS rows | folds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| price_ai | 49.7% | 32.6% | 32.6% | 32 | 119 | 24 | 175 | 14 |
| price_gdelt | 45.1% | 32.2% | 31.9% | 32 | 119 | 24 | 175 | 14 |
| price_ai_gdelt | 46.3% | 32.1% | 32.0% | 32 | 119 | 24 | 175 | 14 |
| price_only | 46.9% | 31.9% | 31.4% | 32 | 119 | 24 | 175 | 14 |
| price_calendar | 42.3% | 30.9% | 30.4% | 32 | 119 | 24 | 175 | 14 |
| price_calendar_gdelt | 38.9% | 30.8% | 29.3% | 32 | 119 | 24 | 175 | 14 |
| price_calendar_ai | 42.9% | 30.0% | 30.0% | 32 | 119 | 24 | 175 | 14 |
| price_calendar_ai_gdelt | 40.0% | 29.8% | 29.1% | 32 | 119 | 24 | 175 | 14 |

Interpretation: the current fixed-band classifier is weak; the price-only baseline is stronger than price+calendar on balanced accuracy in this run.

## Direct Volatility Forecast

| run | features | model | MAE | RMSE | R2 | Spearman | high-vol balanced acc | actual high-vol rate | pred high-vol rate | OOS rows | folds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| price_only_ridge | price_only | ridge | 0.0079 | 0.0096 | -0.0249 | -0.035 | 50.0% | 29.1% | 0.0% | 175 | 14 |
| price_ai_ridge | price_ai | ridge | 0.0080 | 0.0096 | -0.0283 | -0.010 | 50.0% | 29.1% | 0.0% | 175 | 14 |
| price_gdelt_ridge | price_gdelt | ridge | 0.0078 | 0.0096 | -0.0330 | -0.037 | 50.0% | 29.1% | 0.0% | 175 | 14 |
| price_ai_gdelt_ridge | price_ai_gdelt | ridge | 0.0079 | 0.0097 | -0.0396 | -0.015 | 50.0% | 29.1% | 0.0% | 175 | 14 |
| price_calendar_ridge | price_calendar | ridge | 0.0080 | 0.0097 | -0.0558 | -0.008 | 51.2% | 29.1% | 2.3% | 175 | 14 |
| price_calendar_ai_ridge | price_calendar_ai | ridge | 0.0080 | 0.0097 | -0.0584 | 0.001 | 49.9% | 29.1% | 4.0% | 175 | 14 |
| price_calendar_gdelt_ridge | price_calendar_gdelt | ridge | 0.0079 | 0.0098 | -0.0780 | 0.009 | 49.4% | 29.1% | 2.9% | 175 | 14 |
| price_calendar_ai_gdelt_ridge | price_calendar_ai_gdelt | ridge | 0.0080 | 0.0098 | -0.0807 | 0.023 | 47.4% | 29.1% | 5.7% | 175 | 14 |
| price_gdelt_hgb | price_gdelt | hgb | 0.0082 | 0.0101 | -0.1292 | 0.079 | 48.0% | 29.1% | 12.6% | 175 | 14 |
| price_ai_gdelt_hgb | price_ai_gdelt | hgb | 0.0082 | 0.0101 | -0.1304 | 0.037 | 46.1% | 29.1% | 11.4% | 175 | 14 |
| price_calendar_gdelt_hgb | price_calendar_gdelt | hgb | 0.0081 | 0.0102 | -0.1595 | 0.035 | 48.0% | 29.1% | 12.6% | 175 | 14 |
| price_calendar_ai_gdelt_hgb | price_calendar_ai_gdelt | hgb | 0.0082 | 0.0102 | -0.1693 | 0.004 | 47.9% | 29.1% | 10.9% | 175 | 14 |
| price_ai_hgb | price_ai | hgb | 0.0082 | 0.0103 | -0.1718 | 0.040 | 47.5% | 29.1% | 11.4% | 175 | 14 |
| price_only_hgb | price_only | hgb | 0.0082 | 0.0103 | -0.1833 | 0.060 | 47.9% | 29.1% | 10.9% | 175 | 14 |
| price_calendar_hgb | price_calendar | hgb | 0.0083 | 0.0103 | -0.1883 | 0.025 | 48.6% | 29.1% | 13.7% | 175 | 14 |
| price_calendar_ai_hgb | price_calendar_ai | hgb | 0.0083 | 0.0104 | -0.2102 | -0.001 | 47.2% | 29.1% | 13.7% | 175 | 14 |

Interpretation: the direct one-week volatility forecast is the risk-focused diagnostic; high-volatility balanced accuracy is more relevant than directional accuracy for this target.

## Auxiliary Expected-Return Strategy

| run | features | model | MAE | RMSE | R2 | direction acc | trade freq | strategy return | Sharpe | max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| price_calendar_ai_gdelt_hgb | price_calendar_ai_gdelt | hgb | 0.0182 | 0.0244 | -0.0279 | 54.9% | 33.1% | 18.3% | 0.481 | -13.2% |
| price_calendar_ai_gdelt_ridge | price_calendar_ai_gdelt | ridge | 0.0179 | 0.0253 | -0.1037 | 55.4% | 30.3% | 14.2% | 0.406 | -17.5% |
| price_calendar_ai_ridge | price_calendar_ai | ridge | 0.0180 | 0.0252 | -0.1018 | 53.7% | 27.4% | 10.7% | 0.322 | -14.8% |
| price_calendar_hgb | price_calendar | hgb | 0.0181 | 0.0252 | -0.0989 | 53.7% | 30.9% | 3.6% | 0.130 | -9.4% |
| price_only_ridge | price_only | ridge | 0.0175 | 0.0246 | -0.0449 | 52.0% | 11.4% | 3.3% | 0.089 | -14.2% |
| price_ai_ridge | price_ai | ridge | 0.0182 | 0.0254 | -0.1161 | 48.6% | 20.6% | 3.1% | 0.077 | -20.7% |
| price_calendar_gdelt_ridge | price_calendar_gdelt | ridge | 0.0174 | 0.0243 | -0.0197 | 53.7% | 22.3% | 2.5% | 0.062 | -19.9% |
| price_ai_gdelt_hgb | price_ai_gdelt | hgb | 0.0184 | 0.0252 | -0.0957 | 52.0% | 28.6% | -0.3% | -0.012 | -19.9% |
| price_ai_gdelt_ridge | price_ai_gdelt | ridge | 0.0182 | 0.0254 | -0.1197 | 52.0% | 24.0% | -1.4% | -0.034 | -22.4% |
| price_gdelt_ridge | price_gdelt | ridge | 0.0176 | 0.0246 | -0.0494 | 52.6% | 19.4% | -4.1% | -0.110 | -18.4% |
| price_calendar_gdelt_hgb | price_calendar_gdelt | hgb | 0.0183 | 0.0252 | -0.0975 | 54.3% | 34.9% | -4.6% | -0.158 | -14.0% |
| price_calendar_ridge | price_calendar | ridge | 0.0173 | 0.0243 | -0.0220 | 53.1% | 21.1% | -6.2% | -0.188 | -16.8% |
| price_calendar_ai_hgb | price_calendar_ai | hgb | 0.0182 | 0.0247 | -0.0527 | 53.1% | 33.7% | -5.8% | -0.208 | -13.6% |
| price_gdelt_hgb | price_gdelt | hgb | 0.0188 | 0.0255 | -0.1250 | 48.6% | 27.4% | -9.2% | -0.231 | -20.2% |
| price_only_hgb | price_only | hgb | 0.0187 | 0.0258 | -0.1535 | 50.9% | 32.0% | -25.9% | -0.769 | -32.8% |
| price_ai_hgb | price_ai | hgb | 0.0189 | 0.0259 | -0.1640 | 46.9% | 30.9% | -30.9% | -0.997 | -33.6% |

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
| 802 | 39 | 2011-01-07 | 2026-05-15 | 11 | 9 | 0 | 0 | 7 |

| artifact | exists | rows | cols |
| --- | --- | --- | --- |
| data/raw/prices_CORN.csv | yes | 4014 | 7 |
| data/raw/usda_releases.csv | yes | 1606 | 5 |
| data/interim/weather_weekly.parquet | yes | 802 | 11 |
| data/interim/ai_weekly.parquet | yes | 789 | 8 |
| data/processed/feature_panel.parquet | yes | 802 | 39 |
| reports/price_target_predictions.csv | yes | 2800 | 13 |
| reports/expected_return_predictions.csv | yes | 2800 | 18 |
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

- The fixed 2 percent target is imbalanced: 119 of 175 OOS weeks are flat. Accuracy alone is not enough.
- Calendar seasonality does not improve the main fixed-band classifier in this run; balanced accuracy is 1.0% lower than price-only.
- All expected-return regressions have negative OOS R2, so trading metrics should be treated as fragile.
- The direct one-week volatility regressions have non-positive OOS R2 in this run.
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
