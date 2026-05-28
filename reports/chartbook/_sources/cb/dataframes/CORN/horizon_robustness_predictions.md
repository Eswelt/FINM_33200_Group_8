# Dataframe: `CORN:horizon_robustness_predictions` - Horizon Robustness Predictions

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
- `price_gdelt`
- `price_ai_gdelt`
- `price_calendar`
- `price_calendar_ai`
- `price_calendar_gdelt`
- `price_calendar_ai_gdelt`

## Direction Pipeline

| horizon_weeks | feature_set | accuracy | balanced_accuracy | macro_f1 | n_test |
| --- | --- | --- | --- | --- | --- |
| 1 | price_only | 0.4686 | 0.3191 | 0.3142 | 175 |
| 1 | price_ai | 0.4971 | 0.3261 | 0.3257 | 175 |
| 1 | price_gdelt | 0.4514 | 0.3224 | 0.3190 | 175 |
| 1 | price_ai_gdelt | 0.4629 | 0.3211 | 0.3199 | 175 |
| 1 | price_calendar | 0.4229 | 0.3091 | 0.3042 | 175 |
| 1 | price_calendar_ai | 0.4286 | 0.3001 | 0.2997 | 175 |
| 1 | price_calendar_gdelt | 0.3886 | 0.3075 | 0.2935 | 175 |
| 1 | price_calendar_ai_gdelt | 0.4000 | 0.2979 | 0.2912 | 175 |
| 4 | price_only | 0.3488 | 0.3439 | 0.3255 | 172 |
| 4 | price_ai | 0.3605 | 0.3560 | 0.3318 | 172 |
| 4 | price_gdelt | 0.3256 | 0.3144 | 0.2828 | 172 |
| 4 | price_ai_gdelt | 0.3488 | 0.3397 | 0.3088 | 172 |
| 4 | price_calendar | 0.4419 | 0.4336 | 0.4263 | 172 |
| 4 | price_calendar_ai | 0.4419 | 0.4346 | 0.4301 | 172 |
| 4 | price_calendar_gdelt | 0.4419 | 0.4347 | 0.4239 | 172 |
| 4 | price_calendar_ai_gdelt | 0.4651 | 0.4601 | 0.4479 | 172 |
| 13 | price_only | 0.4172 | 0.3967 | 0.3944 | 163 |
| 13 | price_ai | 0.3865 | 0.4032 | 0.3839 | 163 |
| 13 | price_gdelt | 0.3620 | 0.3727 | 0.3561 | 163 |
| 13 | price_ai_gdelt | 0.3988 | 0.4422 | 0.3982 | 163 |
| 13 | price_calendar | 0.4540 | 0.4662 | 0.4477 | 163 |
| 13 | price_calendar_ai | 0.4294 | 0.4470 | 0.4237 | 163 |
| 13 | price_calendar_gdelt | 0.3681 | 0.3663 | 0.3510 | 163 |
| 13 | price_calendar_ai_gdelt | 0.3620 | 0.3706 | 0.3567 | 163 |

## Expected-Return Pipeline

| horizon_weeks | feature_set | estimator | mae | rmse | r2 | direction_accuracy | strategy_total_return | strategy_sharpe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | price_ai_gdelt | hgb | 0.0184 | 0.0252 | -0.0957 | 0.5200 | -0.0031 | -0.0125 |
| 1 | price_ai_gdelt | ridge | 0.0182 | 0.0254 | -0.1197 | 0.5200 | -0.0140 | -0.0344 |
| 1 | price_ai | hgb | 0.0189 | 0.0259 | -0.1640 | 0.4686 | -0.3088 | -0.9971 |
| 1 | price_ai | ridge | 0.0182 | 0.0254 | -0.1161 | 0.4857 | 0.0305 | 0.0768 |
| 1 | price_calendar_ai_gdelt | hgb | 0.0182 | 0.0244 | -0.0279 | 0.5486 | 0.1833 | 0.4809 |
| 1 | price_calendar_ai_gdelt | ridge | 0.0179 | 0.0253 | -0.1037 | 0.5543 | 0.1422 | 0.4063 |
| 1 | price_calendar_ai | hgb | 0.0182 | 0.0247 | -0.0527 | 0.5314 | -0.0583 | -0.2080 |
| 1 | price_calendar_ai | ridge | 0.0180 | 0.0252 | -0.1018 | 0.5371 | 0.1072 | 0.3216 |
| 1 | price_calendar_gdelt | hgb | 0.0183 | 0.0252 | -0.0975 | 0.5429 | -0.0459 | -0.1578 |
| 1 | price_calendar_gdelt | ridge | 0.0174 | 0.0243 | -0.0197 | 0.5371 | 0.0247 | 0.0621 |
| 1 | price_calendar | hgb | 0.0181 | 0.0252 | -0.0989 | 0.5371 | 0.0364 | 0.1302 |
| 1 | price_calendar | ridge | 0.0173 | 0.0243 | -0.0220 | 0.5314 | -0.0618 | -0.1884 |
| 1 | price_gdelt | hgb | 0.0188 | 0.0255 | -0.1250 | 0.4857 | -0.0924 | -0.2314 |
| 1 | price_gdelt | ridge | 0.0176 | 0.0246 | -0.0494 | 0.5257 | -0.0410 | -0.1097 |
| 1 | price_only | hgb | 0.0187 | 0.0258 | -0.1535 | 0.5086 | -0.2585 | -0.7686 |
| 1 | price_only | ridge | 0.0175 | 0.0246 | -0.0449 | 0.5200 | 0.0332 | 0.0886 |
| 4 | price_ai_gdelt | hgb | 0.0355 | 0.0445 | -0.1371 | 0.5058 | -0.3910 | -0.7846 |
| 4 | price_ai_gdelt | ridge | 0.0347 | 0.0441 | -0.1167 | 0.5000 | -0.3753 | -0.8366 |
| 4 | price_ai | hgb | 0.0358 | 0.0450 | -0.1609 | 0.5465 | -0.3131 | -0.5862 |
| 4 | price_ai | ridge | 0.0345 | 0.0439 | -0.1053 | 0.5465 | -0.2163 | -0.4085 |
| 4 | price_calendar_ai_gdelt | hgb | 0.0339 | 0.0432 | -0.0693 | 0.5756 | -0.2812 | -0.4889 |
| 4 | price_calendar_ai_gdelt | ridge | 0.0348 | 0.0440 | -0.1080 | 0.5465 | -0.2480 | -0.4460 |
| 4 | price_calendar_ai | hgb | 0.0343 | 0.0423 | -0.0252 | 0.5291 | -0.1358 | -0.2208 |
| 4 | price_calendar_ai | ridge | 0.0347 | 0.0435 | -0.0824 | 0.5349 | -0.0900 | -0.1505 |
| 4 | price_calendar_gdelt | hgb | 0.0333 | 0.0426 | -0.0384 | 0.5756 | -0.0656 | -0.0994 |
| 4 | price_calendar_gdelt | ridge | 0.0332 | 0.0421 | -0.0133 | 0.5407 | -0.3090 | -0.7448 |
| 4 | price_calendar | hgb | 0.0344 | 0.0425 | -0.0365 | 0.5465 | -0.0168 | -0.0280 |
| 4 | price_calendar | ridge | 0.0334 | 0.0419 | -0.0058 | 0.5233 | -0.0652 | -0.1192 |
| 4 | price_gdelt | hgb | 0.0373 | 0.0456 | -0.1894 | 0.4360 | -0.5056 | -1.2676 |
| 4 | price_gdelt | ridge | 0.0348 | 0.0437 | -0.0927 | 0.4826 | -0.5192 | -1.5927 |
| 4 | price_only | hgb | 0.0371 | 0.0459 | -0.2058 | 0.4651 | -0.5775 | -1.3480 |
| 4 | price_only | ridge | 0.0347 | 0.0433 | -0.0754 | 0.5174 | -0.3224 | -1.0337 |
| 13 | price_ai_gdelt | hgb | 0.0599 | 0.0734 | -0.3075 | 0.5092 | -0.7328 | -1.9537 |
| 13 | price_ai_gdelt | ridge | 0.0539 | 0.0664 | -0.0705 | 0.5706 | -0.4906 | -0.8537 |
| 13 | price_ai | hgb | 0.0567 | 0.0708 | -0.2155 | 0.5521 | -0.6881 | -1.7083 |
| 13 | price_ai | ridge | 0.0543 | 0.0676 | -0.1089 | 0.5460 | -0.5895 | -1.4315 |
| 13 | price_calendar_ai_gdelt | hgb | 0.0597 | 0.0742 | -0.3362 | 0.5153 | -0.7579 | -1.7167 |
| 13 | price_calendar_ai_gdelt | ridge | 0.0532 | 0.0653 | -0.0348 | 0.5828 | -0.2120 | -0.3151 |
| 13 | price_calendar_ai | hgb | 0.0603 | 0.0742 | -0.3345 | 0.5215 | -0.7026 | -1.6651 |
| 13 | price_calendar_ai | ridge | 0.0534 | 0.0664 | -0.0700 | 0.5706 | -0.5720 | -1.0420 |
| 13 | price_calendar_gdelt | hgb | 0.0628 | 0.0769 | -0.4329 | 0.4601 | -0.8483 | -2.0921 |
| 13 | price_calendar_gdelt | ridge | 0.0540 | 0.0661 | -0.0592 | 0.5828 | -0.2816 | -0.4660 |
| 13 | price_calendar | hgb | 0.0604 | 0.0723 | -0.2658 | 0.4969 | -0.6251 | -1.8715 |
| 13 | price_calendar | ridge | 0.0531 | 0.0650 | -0.0239 | 0.5828 | -0.5123 | -1.0120 |
| 13 | price_gdelt | hgb | 0.0630 | 0.0784 | -0.4910 | 0.4847 | -0.9075 | -2.6085 |
| 13 | price_gdelt | ridge | 0.0549 | 0.0688 | -0.1480 | 0.5890 | -0.6454 | -1.3411 |
| 13 | price_only | hgb | 0.0588 | 0.0750 | -0.3640 | 0.5276 | -0.7700 | -2.2014 |
| 13 | price_only | ridge | 0.0534 | 0.0669 | -0.0855 | 0.5828 | -0.2810 | -1.0320 |

## Volatility Pipeline

| horizon_weeks | feature_set | estimator | mae | rmse | r2 | spearman_corr | high_vol_balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | price_ai_gdelt | hgb | 0.0126 | 0.0179 | -0.0909 | 0.0610 | 0.5239 |
| 1 | price_ai_gdelt | ridge | 0.0124 | 0.0172 | -0.0093 | 0.1049 | 0.5528 |
| 1 | price_ai | hgb | 0.0131 | 0.0186 | -0.1775 | 0.0030 | 0.4879 |
| 1 | price_ai | ridge | 0.0125 | 0.0173 | -0.0245 | 0.0267 | 0.5599 |
| 1 | price_calendar_ai_gdelt | hgb | 0.0121 | 0.0165 | 0.0664 | 0.2039 | 0.6304 |
| 1 | price_calendar_ai_gdelt | ridge | 0.0126 | 0.0168 | 0.0361 | 0.1593 | 0.5609 |
| 1 | price_calendar_ai | hgb | 0.0124 | 0.0169 | 0.0201 | 0.2163 | 0.5645 |
| 1 | price_calendar_ai | ridge | 0.0125 | 0.0168 | 0.0377 | 0.1580 | 0.5721 |
| 1 | price_calendar_gdelt | hgb | 0.0122 | 0.0164 | 0.0833 | 0.2113 | 0.5827 |
| 1 | price_calendar_gdelt | ridge | 0.0125 | 0.0167 | 0.0472 | 0.1674 | 0.5538 |
| 1 | price_calendar | hgb | 0.0122 | 0.0170 | 0.0160 | 0.2501 | 0.5538 |
| 1 | price_calendar | ridge | 0.0126 | 0.0168 | 0.0411 | 0.1597 | 0.5903 |
| 1 | price_gdelt | hgb | 0.0126 | 0.0177 | -0.0750 | 0.0537 | 0.5198 |
| 1 | price_gdelt | ridge | 0.0125 | 0.0171 | 0.0015 | 0.0864 | 0.5310 |
| 1 | price_only | hgb | 0.0129 | 0.0181 | -0.1248 | 0.0200 | 0.5127 |
| 1 | price_only | ridge | 0.0127 | 0.0173 | -0.0252 | -0.0455 | 0.5452 |
| 4 | price_ai_gdelt | hgb | 0.0183 | 0.0268 | -0.1108 | 0.0771 | 0.5259 |
| 4 | price_ai_gdelt | ridge | 0.0183 | 0.0256 | -0.0147 | 0.1786 | 0.5574 |
| 4 | price_ai | hgb | 0.0197 | 0.0282 | -0.2255 | 0.0271 | 0.5017 |
| 4 | price_ai | ridge | 0.0186 | 0.0257 | -0.0243 | 0.0663 | 0.5777 |
| 4 | price_calendar_ai_gdelt | hgb | 0.0172 | 0.0229 | 0.1906 | 0.2637 | 0.6684 |
| 4 | price_calendar_ai_gdelt | ridge | 0.0175 | 0.0229 | 0.1899 | 0.3600 | 0.6757 |
| 4 | price_calendar_ai | hgb | 0.0170 | 0.0229 | 0.1926 | 0.2882 | 0.7235 |
| 4 | price_calendar_ai | ridge | 0.0171 | 0.0224 | 0.2254 | 0.3877 | 0.6858 |
| 4 | price_calendar_gdelt | hgb | 0.0168 | 0.0229 | 0.1890 | 0.2821 | 0.6684 |
| 4 | price_calendar_gdelt | ridge | 0.0173 | 0.0227 | 0.2008 | 0.3905 | 0.6791 |
| 4 | price_calendar | hgb | 0.0166 | 0.0225 | 0.2166 | 0.3303 | 0.7235 |
| 4 | price_calendar | ridge | 0.0170 | 0.0223 | 0.2331 | 0.4200 | 0.6858 |
| 4 | price_gdelt | hgb | 0.0181 | 0.0267 | -0.1022 | 0.1019 | 0.5051 |
| 4 | price_gdelt | ridge | 0.0181 | 0.0252 | 0.0187 | 0.1785 | 0.5743 |
| 4 | price_only | hgb | 0.0195 | 0.0279 | -0.2012 | 0.0078 | 0.5017 |
| 4 | price_only | ridge | 0.0186 | 0.0254 | 0.0039 | 0.0156 | 0.5980 |
| 13 | price_ai_gdelt | hgb | 0.0243 | 0.0354 | 0.0913 | 0.4260 | 0.4962 |
| 13 | price_ai_gdelt | ridge | 0.0293 | 0.0391 | -0.1050 | 0.2761 | 0.5561 |
| 13 | price_ai | hgb | 0.0273 | 0.0373 | -0.0041 | 0.2497 | 0.5396 |
| 13 | price_ai | ridge | 0.0320 | 0.0411 | -0.2221 | 0.1021 | 0.5227 |
| 13 | price_calendar_ai_gdelt | hgb | 0.0243 | 0.0319 | 0.2658 | 0.6869 | 0.6991 |
| 13 | price_calendar_ai_gdelt | ridge | 0.0269 | 0.0341 | 0.1604 | 0.6184 | 0.7687 |
| 13 | price_calendar_ai | hgb | 0.0252 | 0.0326 | 0.2332 | 0.6645 | 0.7324 |
| 13 | price_calendar_ai | ridge | 0.0265 | 0.0337 | 0.1760 | 0.6457 | 0.7986 |
| 13 | price_calendar_gdelt | hgb | 0.0244 | 0.0323 | 0.2463 | 0.6879 | 0.6923 |
| 13 | price_calendar_gdelt | ridge | 0.0272 | 0.0342 | 0.1547 | 0.6243 | 0.7687 |
| 13 | price_calendar | hgb | 0.0249 | 0.0324 | 0.2413 | 0.6875 | 0.7059 |
| 13 | price_calendar | ridge | 0.0266 | 0.0337 | 0.1788 | 0.6495 | 0.8020 |
| 13 | price_gdelt | hgb | 0.0239 | 0.0345 | 0.1397 | 0.4398 | 0.5396 |
| 13 | price_gdelt | ridge | 0.0289 | 0.0388 | -0.0880 | 0.3209 | 0.5561 |
| 13 | price_only | hgb | 0.0270 | 0.0369 | 0.0171 | 0.2709 | 0.5295 |
| 13 | price_only | ridge | 0.0313 | 0.0405 | -0.1869 | 0.0811 | 0.5532 |

## Takeaway

The horizon comparison is intended to show whether USDA/GLM and seasonality features work better as medium-horizon signals than as one-week signals. Direction and return results should be interpreted cautiously because multi-week cumulative returns are still noisy and overlapping. The volatility pipeline is the most economically natural horizon test because crop and weather information often changes the width of the return distribution before it gives a clean directional edge.



## DataFrame Glimpse

```
Rows: 24480
Columns: 30
$ week                      <str> '2026-02-13'
$ fold                      <i64> 12
$ experiment                <str> null
$ feature_set               <str> 'price_only'
$ model                     <str> 'price_only_ridge'
$ y_true_return             <f64> null
$ y_pred_return             <f64> null
$ train_start               <str> '2011-01-07'
$ train_end                 <str> '2025-12-26'
$ n_train                   <i64> 782
$ y_true_3class             <str> null
$ y_pred_3class             <str> null
$ target_log_return_next    <str> '0.04865531558686076'
$ task                      <str> 'volatility'
$ horizon_weeks             <i64> 13
$ estimator                 <str> 'ridge'
$ predicted_return          <str> null
$ trade_threshold           <str> null
$ position                  <str> null
$ turnover                  <str> null
$ transaction_cost          <str> null
$ strategy_log_return       <str> null
$ benchmark_log_return      <str> null
$ cum_strategy_return       <str> null
$ cum_benchmark_return      <str> null
$ target_abs_return_next    <str> '0.06727859785137007'
$ predicted_abs_return_next <str> '0.08174361033391511'
$ high_vol_threshold        <str> '0.10904334802952614'
$ y_true_high_vol           <str> '0.0'
$ y_pred_high_vol           <str> '0.0'


```

## Dataframe Manifest

| Dataframe Name                 | Horizon Robustness Predictions                                                   |
|--------------------------------|--------------------------------------------------------------------------------------|
| Dataframe ID                   | [horizon_robustness_predictions](../dataframes/CORN/horizon_robustness_predictions.md)                                       |
| Data Sources                   | Generated model output                                        |
| Data Providers                 | scripts/run_horizon_robustness.py                                      |
| Links to Providers             |                              |
| Topic Tags                     | Horizon Robustness, Predictions, Corn                                          |
| Type of Data Access            |                                   |
| How is data pulled?            | Generated by scripts/run_horizon_robustness.py.                                                    |
| Data available up to (min)     | None                                                             |
| Data available up to (max)     | None                                                             |
| Dataframe Path                 | /Users/Haruki/Library/Mobile Documents/com~apple~CloudDocs/Python/AIF/final/FINM_33200_Group_8/reports/horizon_robustness_predictions.csv                                                   |


**Linked Charts:**

- None


## Pipeline Manifest

| Pipeline Name                   | CORN ETF Volatility Forecasting Pipeline                       |
|---------------------------------|--------------------------------------------------------|
| Pipeline ID                     | [CORN](../../../index.md)              |
| Lead Pipeline Developer         | FINM 33200 Group 8             |
| Contributors                    | FINM 33200 Group 8           |
| Git Repo URL                    | local                        |
| Pipeline Web Page               | <a href="file:///Users/Haruki/Library/Mobile Documents/com~apple~CloudDocs/Python/AIF/final/FINM_33200_Group_8/docs/index.html">Pipeline Web Page      |
| Date of Last Code Update        | 2026-05-28 00:30:21           |
| OS Compatibility                |  |
| Linked Dataframes               |  [CORN:feature_panel](../../dataframes/CORN/feature_panel.md)<br>  [CORN:price_target_predictions](../../dataframes/CORN/price_target_predictions.md)<br>  [CORN:expected_return_predictions](../../dataframes/CORN/expected_return_predictions.md)<br>  [CORN:volatility_predictions](../../dataframes/CORN/volatility_predictions.md)<br>  [CORN:horizon_robustness_metrics](../../dataframes/CORN/horizon_robustness_metrics.md)<br>  [CORN:horizon_robustness_predictions](../../dataframes/CORN/horizon_robustness_predictions.md)<br>  [CORN:gdelt_weekly_scores](../../dataframes/CORN/gdelt_weekly_scores.md)<br>  |


