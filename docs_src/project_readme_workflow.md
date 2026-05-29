# CORN ETF Forecasting Project

## Project Motivation

Corn is one of the most weather-sensitive agricultural commodities, and the Teucrium Corn ETF (`CORN`) gives investors a liquid market instrument tied to corn futures exposure. The central question of this project is whether information beyond recent prices can improve trading signals for `CORN`.

We study three broad sources of information:

| Information source | Economic idea | How it enters the project |
| --- | --- | --- |
| Historical price behavior | Momentum, volatility, and recent return patterns may contain short-run market information. | Lagged returns, rolling volatility, momentum, and volume features. |
| Crop-market text and news | USDA-style reports and public news may reveal changing market expectations before they are fully reflected in prices. | AI/USDA scores and GDELT weekly news scores joined to the weekly panel. |
| Weather conditions and forecasts | Corn supply risk is strongly connected to heat, dryness, and timing during the growing season. | CFSv2 forecast anomalies, ERA5/GPCP observed anomalies, and projected weather changes in the daily weather experiment. |

The project is therefore not only a prediction exercise. It is a test of whether economically motivated feature blocks can improve out-of-sample trading decisions.

## Research Design

The main weekly pipeline predicts `CORN` market behavior using information available at the close of each week. The sample covers 2011 through the frozen 2026 project data, with out-of-sample evaluation beginning after 2022.

The weekly experiments use two related targets:

| Target | Purpose | Evaluation emphasis |
| --- | --- | --- |
| Fixed +/-2% class | Classify next week as down, flat, or up. | Balanced accuracy, macro F1, and confusion matrices. |
| Expected return | Forecast next-week log return directly and trade when the forecast clears a cost-aware threshold. | Total return, Sharpe ratio, drawdown, and turnover. |

The weather experiment shifts to a daily decision frequency. It tests whether lead-specific weather forecasts improve a 5-trading-day return signal relative to a price/calendar baseline.

## Modeling Workflow

The project uses a point-in-time workflow:

1. Align market, calendar, text/news, and weather information to the decision date.
2. Construct features that would have been known at that time.
3. Train models only on historical observations available before the test window.
4. Generate out-of-sample predictions through an expanding walk-forward design.
5. Evaluate both statistical performance and trading performance.

This structure is important because the project is framed as a deployable trading-signal problem. Random train/test splits are avoided because they do not match the time ordering of real trading decisions.

## Feature Families

| Feature family | Examples | Intended signal |
| --- | --- | --- |
| Price | Lagged returns, rolling volatility, momentum, volume change. | Short-run trend, mean reversion, and risk state. |
| Calendar | Month, quarter, week-of-year cyclic terms, planting/pollination/harvest/storage season indicators. | Crop-season timing and seasonal risk windows. |
| AI and USDA-style text | Structured sentiment or supply/demand scores derived from agricultural report text. | Report-driven changes in market expectations. |
| GDELT news | Weekly public-news scores related to corn markets. | Broader news attention and tone. |
| Weather forecasts | CFSv2 heat, dryness, and heat-by-dryness forecast anomalies. | Forward-looking production risk. |
| Observed weather | ERA5/GPCP initialization-date heat and precipitation anomalies. | Current physical conditions before the forecast horizon. |

## Validation and Metrics

The weekly experiments use expanding walk-forward validation with 13-week test folds and 14 out-of-sample folds. The out-of-sample weekly window contains 175 weeks from early 2023 through the frozen 2026 data.

The daily weather experiment evaluates daily decisions from 2022 through 2025, using expanding yearly training and 826 out-of-sample decision rows per lead/model combination.

The project reports several metrics because no single number is sufficient:

| Metric group | Why it matters |
| --- | --- |
| Classification metrics | Accuracy can be misleading when most weeks are flat; balanced accuracy and macro F1 better reflect class separation. |
| Regression diagnostics | R2, RMSE, MAE, and correlation show whether return magnitudes are being predicted. |
| Trading metrics | Total return, Sharpe ratio, max drawdown, and turnover translate forecasts into portfolio behavior. |

## Final Presentation Roadmap

This ChartBook site is organized as three presentation pages:

| Page | Focus |
| --- | --- |
| Project Overview | Motivation, data sources, feature design, modeling workflow, and validation approach. |
| Text, News, Calendar, and Price Results | Weekly fixed-band classification and expected-return strategy results using historical price, calendar, AI/USDA, and GDELT features. |
| Weather Forecast Signals | Daily trading results using CFSv2 forecast leads and observed weather anomalies. |

The overall finding is nuanced: the fixed +/-2% weekly classification problem is difficult and highly imbalanced, but feature-enriched strategy tests, especially weather-based projected-change signals, show more promising exploratory trading performance.
