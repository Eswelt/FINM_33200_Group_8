# Weather Forecast Signals and Daily Trading Results

## Why Weather Signals Matter

Corn prices are closely tied to expectations about crop supply. Heat and dryness during key growing periods can change yield expectations, and those expectations can move futures-linked instruments such as the Teucrium Corn ETF (`CORN`).

The weather experiment asks whether forward-looking weather forecasts add trading value beyond a price/calendar baseline. Instead of predicting weekly classes, this part of the project makes daily trading decisions using short-lead weather forecasts.

## Experiment Design

The weather pipeline combines three information sets:

| Information set | Role in the experiment |
| --- | --- |
| Price and calendar baseline | Captures recent `CORN` market behavior and crop-season timing. |
| CFSv2 forecast anomalies | Measures expected heat, dryness, and heat-by-dryness risk at specific forecast leads. |
| ERA5/GPCP observed anomalies | Measures current physical conditions before the forecast horizon. |

Each model predicts the future 5-trading-day `CORN` return. Trading performance is measured through a daily-rebalanced strategy that applies the model signal to the next one-day realized return.

The out-of-sample period covers 2022 through 2025. Each lead/model comparison uses 826 daily decision rows and an expanding yearly training design.

## Lead Days and Model Variants

The analysis focuses on short forecast leads:

| Lead day | Interpretation |
| --- | --- |
| +7 | One-week-ahead weather information. |
| +14 | Two-week-ahead weather information. |
| +21 | Three-week-ahead weather information. |
| +28 | Four-week-ahead weather information. |
| +30 | Roughly one-month-ahead weather information. |

For each lead, the experiment compares:

| Model variant | Description |
| --- | --- |
| `price_calendar` | Price and crop-calendar baseline. |
| `forecast_anom` | Baseline plus CFSv2 forecast anomaly factors. |
| `forecast_anom_projected_change` | Baseline plus forecast anomalies measured relative to observed initialization conditions. |

The projected-change feature set is the most economically intuitive weather signal: it asks whether the forecast is becoming hotter or drier relative to the current observed state.

## Headline Weather Results

The strongest result is the +14-day projected-change model. It delivers the highest daily-rebalanced total return and Sharpe ratio in the no-buffer comparison.

| Lead | Model | Total return | Sharpe | Max drawdown | OOS R2 | Corr. |
| --- | --- | --- | --- | --- | --- | --- |
| +14 | `forecast_anom_projected_change` | 116.1% | 1.303 | -11.7% | 0.0001 | 0.086 |
| +30 | `forecast_anom_projected_change` | 80.9% | 1.022 | -13.0% | -0.0011 | 0.083 |
| +7 | `forecast_anom_projected_change` | 63.0% | 0.859 | -13.6% | 0.0049 | 0.102 |
| +28 | `forecast_anom_projected_change` | 48.2% | 0.711 | -23.8% | -0.0019 | 0.080 |
| +21 | `forecast_anom_projected_change` | 39.1% | 0.612 | -20.3% | -0.0068 | 0.070 |
| Baseline | `price_calendar` | 24.9% | 0.444 | -25.3% | -0.0036 | 0.072 |

The trading metrics are stronger than the regression diagnostics. OOS R2 and correlation are small, so the result should be interpreted as an exploratory trading signal rather than a high-precision return forecast.

## Summary Charts

### Daily-Rebalanced Total Return

![Daily decision total return summary](figures/weather_daily_decision/daily_decision_total_return_summary.png)

The total return summary shows that projected-change weather factors dominate the price/calendar baseline across the most important short leads. The +14 and +30 projected-change models are the clearest standouts.

### Daily-Rebalanced Sharpe Ratio

![Daily decision Sharpe summary](figures/weather_daily_decision/daily_decision_sharpe_summary.png)

The Sharpe comparison tells the same story in risk-adjusted terms. The +14 projected-change model has the strongest Sharpe, while the +7 and +30 projected-change models also improve meaningfully over the baseline.

### Out-of-Sample R2

![Daily decision OOS R2 summary](figures/weather_daily_decision/daily_decision_oos_r2_summary.png)

The R2 chart is much more conservative than the trading charts. Only a few specifications are near or slightly above the train-mean benchmark. This gap is important: the weather models are not explaining large fractions of daily return variance, but they may still rank or sign returns well enough to improve a trading rule.

## Lead-Specific Equity Curves

### Lead +7

![Lead +7 daily-rebalanced equity](figures/weather_daily_decision/lead_07_daily_rebalanced_equity.png)

At +7 days, the projected-change signal improves both total return and risk-adjusted performance relative to the price/calendar baseline.

### Lead +14

![Lead +14 daily-rebalanced equity](figures/weather_daily_decision/lead_14_daily_rebalanced_equity.png)

The +14-day lead is the strongest result. The projected-change model compounds well through the test period and has the best Sharpe ratio in the weather experiment.

### Lead +21

![Lead +21 daily-rebalanced equity](figures/weather_daily_decision/lead_21_daily_rebalanced_equity.png)

The +21-day lead remains positive but is less compelling than +14 and +30. Weather information still helps, but the signal is weaker.

### Lead +28

![Lead +28 daily-rebalanced equity](figures/weather_daily_decision/lead_28_daily_rebalanced_equity.png)

The +28-day lead shows positive performance for the projected-change model, but with larger drawdowns than the best short-lead results.

### Lead +30

![Lead +30 daily-rebalanced equity](figures/weather_daily_decision/lead_30_daily_rebalanced_equity.png)

The +30-day projected-change model is the second strongest weather result by Sharpe and total return. This suggests that one-month-ahead forecast shifts may contain useful market information.

## Interpretation

The weather experiment provides the clearest evidence that domain-specific information can improve `CORN` trading signals. The projected-change framing works better than raw forecast anomalies because it measures how the forecast differs from current observed conditions.

The results should still be presented carefully. The strongest models have attractive trading metrics, but their R2 values are small and the experiment does not include every real-world trading friction. The practical conclusion is not that weather forecasts perfectly predict `CORN` returns; it is that weather forecast changes, especially around +14 days, appear to contain useful timing information in this sample.
