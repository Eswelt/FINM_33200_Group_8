# Limitations, Discussion, and Future Work

## Project-Level Takeaway

The project tests whether `CORN` ETF returns can be predicted better when market history is combined with domain-specific information. The weekly text/news pipeline asks whether USDA-style text, AI scores, GDELT news signals, calendar variables, and price history improve return classification or expected-return trading. The daily weather pipeline asks whether short-lead CFSv2 forecasts add incremental value beyond a price/calendar baseline.

The two strands tell a consistent story. Classification accuracy is difficult because large weekly moves are sparse and noisy, but strategy-based evaluation shows more encouraging evidence of signal value. The weather results are strongest at short forecast leads, especially when forecast anomalies are measured relative to current observed weather conditions.

## Discussion Across The Two Experiments

The text/news experiment is best interpreted as an information-set comparison. Price-only signals provide the necessary baseline. Calendar variables add crop-season structure, while AI/USDA-style and GDELT news features attempt to capture market-relevant information that is not fully summarized by recent returns. The fixed +/-2% classifier remains weak because the target is imbalanced: most weeks are flat, while the up and down classes are relatively rare. Expected-return and strategy metrics therefore provide a more useful evaluation lens than raw classification accuracy alone.

The weather experiment is more directly tied to a commodity-market mechanism. `CORN` ETF is linked to CBOT corn futures, and corn futures prices reflect expectations about future crop supply and demand. Forecasts of heat and dryness can matter when they change expected crop stress or yield risk. The projected-change variables are especially important because they compare future forecast conditions with the observed state near the decision date. This framing is closer to how markets process new information: a hot and dry forecast is more relevant if it represents a meaningful deterioration from current conditions.

Across both experiments, the most persuasive evidence is not a single metric. OOS R2, correlation, direction accuracy, Sharpe ratio, drawdown, turnover, and cumulative return need to be read together. A model can have small R2 but still improve a trading rule if it ranks signs or large opportunities better than the baseline. Conversely, a visually attractive equity curve can be fragile if it depends on a short sample, high turnover, or a few concentrated episodes.

## Limitations

The main limitation is sample size. The weekly model has 175 out-of-sample weeks, and the daily weather model covers 2022-2025. These samples are useful for walk-forward and expanding-window testing, but they do not span many commodity-market regimes. Any strong-looking strategy result should therefore be treated as exploratory evidence rather than as proof of a production trading system.

The classification target is another limitation. A fixed +/-2% weekly threshold creates a highly imbalanced three-class problem. The flat class dominates, so conventional accuracy can be misleading. This is why balanced accuracy, macro F1, and trading outcomes are more informative than raw accuracy.

The text/news pipeline depends on feature proxies. USDA-style text scores, AI features, and GDELT news measures may capture useful information, but they are still noisy summaries of a much larger information environment. The current design does not fully model how quickly news is incorporated into futures prices or how different types of news should decay over time.

The weather pipeline uses a single U.S. Corn Belt bounding box. This is a reasonable MVP design, but corn futures also respond to global supply risks and to weather outside the U.S. South America is especially relevant during the U.S. winter, and the current U.S.-only weather specification may miss Brazil and Argentina corn-region signals.

The same heat and dryness variables are used across the full calendar year. This is transparent, but the economic meaning of weather changes by crop stage. Hot and dry conditions are most relevant during pollination, wet and cold conditions may matter more during planting, wet conditions can delay harvest, and winter U.S. Corn Belt weather is less directly tied to current production. A season-gated specification would let weather variables have different coefficients during planting, pollination, harvest, and winter-storage periods.

The weather backtest is also a simplified implementation. The regression target is the future 5-trading-day `CORN` ETF return, but the plotted trading strategy converts the predicted 5-day return into a daily long/short position and compounds realized next-day returns. This makes the equity curves useful for comparing signals, but it is not the same as a fully realistic weekly holding-period strategy.

The backtests include a transaction-cost assumption, but they do not fully model bid-ask spreads, ETF liquidity, borrow costs for short positions, market impact, taxes, or execution timing. Long/short rules are useful for measuring directional signal value, but a long/cash rule may be more realistic for weather supply-risk signals because bearish weather interpretations are not necessarily symmetric with bullish hot/dry crop-stress signals.

## Future Proposed Work

1. Add season-specific weather interactions. Weather coefficients should be allowed to differ across planting, pollination, harvest, and winter-storage periods.

2. Add forecast-revision variables. A useful weather feature is the change in the forecast for the same valid date from one decision date to the next, because markets should react more strongly to new information than to already known forecast levels.

3. Add South America weather factors for December-May. Brazil and Argentina corn-region weather can affect global supply expectations when U.S. Corn Belt weather is less directly relevant.

4. Compare daily-rebalanced and 5-trading-day holding-period strategies. The current weather regression target is a future 5-trading-day return, so a weekly or non-overlapping holding-period backtest would be a useful robustness check.

5. Evaluate long/cash strategies in addition to long/short rules. Weather supply-risk signals may be asymmetric: hot and dry crop stress can be bullish, but benign weather does not necessarily imply an equally strong bearish trade.

6. Improve target definitions for text/news models. Alternatives include volatility-adjusted thresholds, quantile targets, ranking losses, or direct expected-return objectives rather than fixed absolute return bands.

7. Add turnover-aware model selection. Strategy performance should be evaluated with transaction costs and turnover constraints inside the validation loop, not only after forecasts are generated.

8. Test robustness across alternative commodities and weather regions. A broader commodity panel would help determine whether the observed patterns are specific to `CORN` ETF or reflect a more general agricultural futures mechanism.
