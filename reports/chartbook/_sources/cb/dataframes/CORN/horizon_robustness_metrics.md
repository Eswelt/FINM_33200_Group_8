# Dataframe: `CORN:horizon_robustness_metrics` - Horizon Robustness Metrics

# Horizon Robustness Results

Run date: 2026-05-27.

This experiment keeps the weekly prediction cadence but changes the forward target horizon:

- 1 week
- 4 weeks
- 13 weeks

For return and direction tasks, the target is cumulative log return over the next horizon. For volatility, the target is realized volatility over the next horizon, measured as the square root of the sum of squared weekly returns. Multi-week targets overlap across adjacent prediction dates, so the results should be read as horizon-sensitivity diagnostics rather than independent quarterly observations.

Feature sets:

- `price_only`
- `price_ai`
- `price_calendar`
- `price_calendar_ai`

## Direction Pipeline

| horizon_weeks | feature_set | accuracy | balanced_accuracy | macro_f1 | n_test |
| --- | --- | --- | --- | --- | --- |
| 1 | price_only | 0.4686 | 0.3191 | 0.3142 | 175 |
| 1 | price_ai | 0.4971 | 0.3261 | 0.3257 | 175 |
| 1 | price_calendar | 0.4229 | 0.3091 | 0.3042 | 175 |
| 1 | price_calendar_ai | 0.4286 | 0.3001 | 0.2997 | 175 |
| 4 | price_only | 0.3488 | 0.3439 | 0.3255 | 172 |
| 4 | price_ai | 0.3605 | 0.3560 | 0.3318 | 172 |
| 4 | price_calendar | 0.4419 | 0.4336 | 0.4263 | 172 |
| 4 | price_calendar_ai | 0.4419 | 0.4346 | 0.4301 | 172 |
| 13 | price_only | 0.4172 | 0.3967 | 0.3944 | 163 |
| 13 | price_ai | 0.3865 | 0.4032 | 0.3839 | 163 |
| 13 | price_calendar | 0.4540 | 0.4662 | 0.4477 | 163 |
| 13 | price_calendar_ai | 0.4294 | 0.4470 | 0.4237 | 163 |

## Expected-Return Pipeline

| horizon_weeks | feature_set | estimator | mae | rmse | r2 | direction_accuracy | strategy_total_return | strategy_sharpe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | price_ai | hgb | 0.0189 | 0.0259 | -0.1640 | 0.4686 | -0.3088 | -0.9971 |
| 1 | price_ai | ridge | 0.0182 | 0.0254 | -0.1161 | 0.4857 | 0.0305 | 0.0768 |
| 1 | price_calendar_ai | hgb | 0.0182 | 0.0247 | -0.0527 | 0.5314 | -0.0583 | -0.2080 |
| 1 | price_calendar_ai | ridge | 0.0180 | 0.0252 | -0.1018 | 0.5371 | 0.1072 | 0.3216 |
| 1 | price_calendar | hgb | 0.0181 | 0.0252 | -0.0989 | 0.5371 | 0.0364 | 0.1302 |
| 1 | price_calendar | ridge | 0.0173 | 0.0243 | -0.0220 | 0.5314 | -0.0618 | -0.1884 |
| 1 | price_only | hgb | 0.0187 | 0.0258 | -0.1535 | 0.5086 | -0.2585 | -0.7686 |
| 1 | price_only | ridge | 0.0175 | 0.0246 | -0.0449 | 0.5200 | 0.0332 | 0.0886 |
| 4 | price_ai | hgb | 0.0358 | 0.0450 | -0.1609 | 0.5465 | -0.3131 | -0.5862 |
| 4 | price_ai | ridge | 0.0345 | 0.0439 | -0.1053 | 0.5465 | -0.2163 | -0.4085 |
| 4 | price_calendar_ai | hgb | 0.0343 | 0.0423 | -0.0252 | 0.5291 | -0.1358 | -0.2208 |
| 4 | price_calendar_ai | ridge | 0.0347 | 0.0435 | -0.0824 | 0.5349 | -0.0900 | -0.1505 |
| 4 | price_calendar | hgb | 0.0344 | 0.0425 | -0.0365 | 0.5465 | -0.0168 | -0.0280 |
| 4 | price_calendar | ridge | 0.0334 | 0.0419 | -0.0058 | 0.5233 | -0.0652 | -0.1192 |
| 4 | price_only | hgb | 0.0371 | 0.0459 | -0.2058 | 0.4651 | -0.5775 | -1.3480 |
| 4 | price_only | ridge | 0.0347 | 0.0433 | -0.0754 | 0.5174 | -0.3224 | -1.0337 |
| 13 | price_ai | hgb | 0.0567 | 0.0708 | -0.2155 | 0.5521 | -0.6881 | -1.7083 |
| 13 | price_ai | ridge | 0.0543 | 0.0676 | -0.1089 | 0.5460 | -0.5895 | -1.4315 |
| 13 | price_calendar_ai | hgb | 0.0603 | 0.0742 | -0.3345 | 0.5215 | -0.7026 | -1.6651 |
| 13 | price_calendar_ai | ridge | 0.0534 | 0.0664 | -0.0700 | 0.5706 | -0.5720 | -1.0420 |
| 13 | price_calendar | hgb | 0.0604 | 0.0723 | -0.2658 | 0.4969 | -0.6251 | -1.8715 |
| 13 | price_calendar | ridge | 0.0531 | 0.0650 | -0.0239 | 0.5828 | -0.5123 | -1.0120 |
| 13 | price_only | hgb | 0.0588 | 0.0750 | -0.3640 | 0.5276 | -0.7700 | -2.2014 |
| 13 | price_only | ridge | 0.0534 | 0.0669 | -0.0855 | 0.5828 | -0.2810 | -1.0320 |

## Volatility Pipeline

| horizon_weeks | feature_set | estimator | mae | rmse | r2 | spearman_corr | high_vol_balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | price_ai | hgb | 0.0131 | 0.0186 | -0.1775 | 0.0030 | 0.4879 |
| 1 | price_ai | ridge | 0.0125 | 0.0173 | -0.0245 | 0.0267 | 0.5599 |
| 1 | price_calendar_ai | hgb | 0.0124 | 0.0169 | 0.0201 | 0.2163 | 0.5645 |
| 1 | price_calendar_ai | ridge | 0.0125 | 0.0168 | 0.0377 | 0.1580 | 0.5721 |
| 1 | price_calendar | hgb | 0.0122 | 0.0170 | 0.0160 | 0.2501 | 0.5538 |
| 1 | price_calendar | ridge | 0.0126 | 0.0168 | 0.0411 | 0.1597 | 0.5903 |
| 1 | price_only | hgb | 0.0129 | 0.0181 | -0.1248 | 0.0200 | 0.5127 |
| 1 | price_only | ridge | 0.0127 | 0.0173 | -0.0252 | -0.0455 | 0.5452 |
| 4 | price_ai | hgb | 0.0197 | 0.0282 | -0.2255 | 0.0271 | 0.5017 |
| 4 | price_ai | ridge | 0.0186 | 0.0257 | -0.0243 | 0.0663 | 0.5777 |
| 4 | price_calendar_ai | hgb | 0.0170 | 0.0229 | 0.1926 | 0.2882 | 0.7235 |
| 4 | price_calendar_ai | ridge | 0.0171 | 0.0224 | 0.2254 | 0.3877 | 0.6858 |
| 4 | price_calendar | hgb | 0.0166 | 0.0225 | 0.2166 | 0.3303 | 0.7235 |
| 4 | price_calendar | ridge | 0.0170 | 0.0223 | 0.2331 | 0.4200 | 0.6858 |
| 4 | price_only | hgb | 0.0195 | 0.0279 | -0.2012 | 0.0078 | 0.5017 |
| 4 | price_only | ridge | 0.0186 | 0.0254 | 0.0039 | 0.0156 | 0.5980 |
| 13 | price_ai | hgb | 0.0273 | 0.0373 | -0.0041 | 0.2497 | 0.5396 |
| 13 | price_ai | ridge | 0.0320 | 0.0411 | -0.2221 | 0.1021 | 0.5227 |
| 13 | price_calendar_ai | hgb | 0.0252 | 0.0326 | 0.2332 | 0.6645 | 0.7324 |
| 13 | price_calendar_ai | ridge | 0.0265 | 0.0337 | 0.1760 | 0.6457 | 0.7986 |
| 13 | price_calendar | hgb | 0.0249 | 0.0324 | 0.2413 | 0.6875 | 0.7059 |
| 13 | price_calendar | ridge | 0.0266 | 0.0337 | 0.1788 | 0.6495 | 0.8020 |
| 13 | price_only | hgb | 0.0270 | 0.0369 | 0.0171 | 0.2709 | 0.5295 |
| 13 | price_only | ridge | 0.0313 | 0.0405 | -0.1869 | 0.0811 | 0.5532 |

## Takeaway

The horizon comparison is intended to show whether USDA/GLM and seasonality features work better as medium-horizon signals than as one-week signals. Direction and return results should be interpreted cautiously because multi-week cumulative returns are still noisy and overlapping. The volatility pipeline is the most economically natural horizon test because crop and weather information often changes the width of the return distribution before it gives a clean directional edge.



## DataFrame Glimpse

```
Rows: 72
Columns: 54
$ task                                   <str> 'volatility'
$ horizon_weeks                          <i64> 13
$ run_id                                 <str> 'price_only_ridge'
$ target                                 <str> 'next_13_week_realized_volatility'
$ model                                  <str> null
$ feature_set                            <str> 'price_only'
$ n_test                                 <i64> 163
$ n_folds                                <i64> 13
$ mae                                    <f64> 0.031263590213389605
$ rmse                                   <f64> 0.040504134681650955
$ r2                                     <f64> -0.1869040712578658
$ direction_accuracy                     <f64> null
$ mean_actual_return                     <f64> null
$ mean_predicted_return                  <f64> null
$ threshold                              <f64> null
$ accuracy                               <f64> null
$ balanced_accuracy_present_classes      <f64> null
$ macro_f1                               <f64> null
$ n_down                                 <f64> null
$ n_flat                                 <f64> null
$ n_up                                   <f64> null
$ extreme_event_rate                     <f64> null
$ has_both_extreme_classes              <bool> null
$ confusion_matrix_labels                <str> null
$ confusion_matrix                       <str> null
$ estimator                              <str> 'ridge'
$ validation_scheme                      <str> 'expanding'
$ train_window_weeks                     <str> null
$ transaction_cost_bps                   <f64> null
$ buffer_bps                             <f64> null
$ trade_threshold                        <f64> null
$ allow_short                           <bool> null
$ trade_count                            <f64> null
$ trade_frequency                        <f64> null
$ hit_rate_traded_weeks                  <f64> null
$ average_return_traded_weeks            <f64> null
$ average_predicted_return_traded_weeks  <f64> null
$ strategy_total_return                  <f64> null
$ benchmark_total_return                 <f64> null
$ strategy_annual_return                 <f64> null
$ strategy_annual_vol                    <f64> null
$ strategy_sharpe                        <f64> null
$ benchmark_sharpe                       <f64> null
$ max_drawdown                           <f64> null
$ mean_position                          <f64> null
$ turnover                               <f64> null
$ high_vol_quantile                      <f64> 0.7
$ spearman_corr                          <f64> 0.08109298884399888
$ mean_actual_volatility                 <f64> 0.08014991480534744
$ mean_predicted_volatility              <f64> 0.09328923531306292
$ high_vol_accuracy                      <f64> 0.8957055214723927
$ high_vol_balanced_accuracy             <f64> 0.5531531531531532
$ high_vol_rate_actual                   <f64> 0.09202453987730061
$ high_vol_rate_predicted                <f64> 0.03680981595092025


```

## Dataframe Manifest

| Dataframe Name                 | Horizon Robustness Metrics                                                   |
|--------------------------------|--------------------------------------------------------------------------------------|
| Dataframe ID                   | [horizon_robustness_metrics](../dataframes/CORN/horizon_robustness_metrics.md)                                       |
| Data Sources                   | Generated model output                                        |
| Data Providers                 | scripts/run_horizon_robustness.py                                      |
| Links to Providers             |                              |
| Topic Tags                     | Horizon Robustness, Volatility, Direction, Expected Return                                          |
| Type of Data Access            |                                   |
| How is data pulled?            | Generated by scripts/run_horizon_robustness.py.                                                    |
| Data available up to (min)     | N/A                                                             |
| Data available up to (max)     | N/A                                                             |
| Dataframe Path                 | /private/tmp/FINM_33200_Group_8_three_inputs/reports/horizon_robustness_metrics.csv                                                   |


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
| Date of Last Code Update        | 2026-05-27 22:01:14           |
| OS Compatibility                |  |
| Linked Dataframes               |  [CORN:feature_panel](../../dataframes/CORN/feature_panel.md)<br>  [CORN:price_target_predictions](../../dataframes/CORN/price_target_predictions.md)<br>  [CORN:expected_return_predictions](../../dataframes/CORN/expected_return_predictions.md)<br>  [CORN:volatility_predictions](../../dataframes/CORN/volatility_predictions.md)<br>  [CORN:horizon_robustness_metrics](../../dataframes/CORN/horizon_robustness_metrics.md)<br>  [CORN:horizon_robustness_predictions](../../dataframes/CORN/horizon_robustness_predictions.md)<br>  [CORN:gdelt_weekly_scores](../../dataframes/CORN/gdelt_weekly_scores.md)<br>  |


