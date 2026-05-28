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
| 1 | price_only | 0.3486 | 0.3992 | 0.3054 | 175 |
| 1 | price_ai | 0.3371 | 0.3641 | 0.2859 | 175 |
| 1 | price_gdelt | 0.2457 | 0.2856 | 0.2132 | 175 |
| 1 | price_ai_gdelt | 0.2629 | 0.3122 | 0.2324 | 175 |
| 1 | price_calendar | 0.3257 | 0.3587 | 0.2789 | 175 |
| 1 | price_calendar_ai | 0.2800 | 0.2970 | 0.2385 | 175 |
| 1 | price_calendar_gdelt | 0.3657 | 0.3954 | 0.3120 | 175 |
| 1 | price_calendar_ai_gdelt | 0.3143 | 0.3199 | 0.2608 | 175 |
| 4 | price_only | 0.3488 | 0.3412 | 0.3412 | 172 |
| 4 | price_ai | 0.3256 | 0.3279 | 0.3214 | 172 |
| 4 | price_gdelt | 0.3721 | 0.3678 | 0.3628 | 172 |
| 4 | price_ai_gdelt | 0.3430 | 0.3345 | 0.3309 | 172 |
| 4 | price_calendar | 0.3198 | 0.3142 | 0.3107 | 172 |
| 4 | price_calendar_ai | 0.3314 | 0.3224 | 0.3202 | 172 |
| 4 | price_calendar_gdelt | 0.3895 | 0.3844 | 0.3774 | 172 |
| 4 | price_calendar_ai_gdelt | 0.3837 | 0.3802 | 0.3726 | 172 |
| 13 | price_only | 0.4110 | 0.4120 | 0.4104 | 163 |
| 13 | price_ai | 0.4417 | 0.4427 | 0.4421 | 163 |
| 13 | price_gdelt | 0.4294 | 0.4258 | 0.4224 | 163 |
| 13 | price_ai_gdelt | 0.4049 | 0.4021 | 0.4001 | 163 |
| 13 | price_calendar | 0.4110 | 0.4086 | 0.4054 | 163 |
| 13 | price_calendar_ai | 0.4172 | 0.4146 | 0.4129 | 163 |
| 13 | price_calendar_gdelt | 0.3865 | 0.3850 | 0.3832 | 163 |
| 13 | price_calendar_ai_gdelt | 0.3926 | 0.3905 | 0.3882 | 163 |

## Expected-Return Pipeline

| horizon_weeks | feature_set | estimator | mae | rmse | r2 | direction_accuracy | strategy_total_return | strategy_sharpe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | price_ai_gdelt | hgb | 0.0145 | 0.0180 | -0.1893 | 0.5200 | -0.0791 | -0.4036 |
| 1 | price_ai_gdelt | ridge | 0.0141 | 0.0171 | -0.0700 | 0.4571 | -0.0285 | -0.1995 |
| 1 | price_ai | hgb | 0.0142 | 0.0177 | -0.1493 | 0.5086 | 0.0382 | 0.2391 |
| 1 | price_ai | ridge | 0.0140 | 0.0171 | -0.0640 | 0.4171 | 0.0289 | 0.5134 |
| 1 | price_calendar_ai_gdelt | hgb | 0.0143 | 0.0176 | -0.1381 | 0.4743 | -0.0457 | -0.3053 |
| 1 | price_calendar_ai_gdelt | ridge | 0.0142 | 0.0173 | -0.0901 | 0.4686 | -0.0237 | -0.1589 |
| 1 | price_calendar_ai | hgb | 0.0142 | 0.0178 | -0.1560 | 0.4971 | 0.0474 | 0.2834 |
| 1 | price_calendar_ai | ridge | 0.0142 | 0.0173 | -0.0889 | 0.4343 | -0.0773 | -0.7502 |
| 1 | price_calendar_gdelt | hgb | 0.0143 | 0.0176 | -0.1378 | 0.4629 | -0.0369 | -0.2206 |
| 1 | price_calendar_gdelt | ridge | 0.0141 | 0.0170 | -0.0560 | 0.4914 | -0.0231 | -0.1601 |
| 1 | price_calendar | hgb | 0.0140 | 0.0177 | -0.1433 | 0.5029 | 0.0042 | 0.0254 |
| 1 | price_calendar | ridge | 0.0141 | 0.0170 | -0.0530 | 0.4400 | -0.0521 | -0.6999 |
| 1 | price_gdelt | hgb | 0.0143 | 0.0177 | -0.1417 | 0.5257 | -0.0517 | -0.2652 |
| 1 | price_gdelt | ridge | 0.0139 | 0.0168 | -0.0368 | 0.4857 | 0.0240 | 0.2175 |
| 1 | price_only | hgb | 0.0140 | 0.0175 | -0.1209 | 0.5429 | 0.0710 | 0.3528 |
| 1 | price_only | ridge | 0.0138 | 0.0168 | -0.0316 | 0.4229 | -0.0048 | -0.1356 |
| 4 | price_ai_gdelt | hgb | 0.0269 | 0.0331 | -0.1386 | 0.5349 | 0.4228 | 0.9687 |
| 4 | price_ai_gdelt | ridge | 0.0269 | 0.0327 | -0.1139 | 0.5581 | 0.3235 | 0.6481 |
| 4 | price_ai | hgb | 0.0268 | 0.0330 | -0.1363 | 0.4884 | 0.2258 | 0.4860 |
| 4 | price_ai | ridge | 0.0272 | 0.0328 | -0.1211 | 0.4826 | 0.1878 | 0.4724 |
| 4 | price_calendar_ai_gdelt | hgb | 0.0272 | 0.0328 | -0.1191 | 0.5640 | 0.9318 | 1.4198 |
| 4 | price_calendar_ai_gdelt | ridge | 0.0262 | 0.0320 | -0.0649 | 0.5581 | 1.2554 | 1.6849 |
| 4 | price_calendar_ai | hgb | 0.0266 | 0.0328 | -0.1227 | 0.5872 | 0.7066 | 1.2974 |
| 4 | price_calendar_ai | ridge | 0.0268 | 0.0324 | -0.0934 | 0.4942 | 0.2671 | 0.5287 |
| 4 | price_calendar_gdelt | hgb | 0.0272 | 0.0328 | -0.1176 | 0.5640 | 0.8222 | 1.4174 |
| 4 | price_calendar_gdelt | ridge | 0.0260 | 0.0316 | -0.0426 | 0.5523 | 0.7914 | 1.4108 |
| 4 | price_calendar | hgb | 0.0263 | 0.0326 | -0.1057 | 0.5814 | 0.9015 | 1.4739 |
| 4 | price_calendar | ridge | 0.0267 | 0.0323 | -0.0860 | 0.4884 | 0.2279 | 0.5276 |
| 4 | price_gdelt | hgb | 0.0274 | 0.0332 | -0.1483 | 0.5116 | 0.3422 | 0.8352 |
| 4 | price_gdelt | ridge | 0.0263 | 0.0322 | -0.0792 | 0.4884 | 0.3074 | 0.6344 |
| 4 | price_only | hgb | 0.0268 | 0.0330 | -0.1341 | 0.4767 | 0.2261 | 0.5894 |
| 4 | price_only | ridge | 0.0269 | 0.0325 | -0.1014 | 0.4535 | -0.0777 | -0.2774 |
| 13 | price_ai_gdelt | hgb | 0.0501 | 0.0622 | -0.4322 | 0.5215 | 0.0825 | 0.1492 |
| 13 | price_ai_gdelt | ridge | 0.0459 | 0.0590 | -0.2872 | 0.5460 | 0.7512 | 0.8248 |
| 13 | price_ai | hgb | 0.0466 | 0.0598 | -0.3221 | 0.5276 | 0.3856 | 0.5568 |
| 13 | price_ai | ridge | 0.0447 | 0.0566 | -0.1848 | 0.5215 | 0.8707 | 1.0452 |
| 13 | price_calendar_ai_gdelt | hgb | 0.0470 | 0.0589 | -0.2837 | 0.5031 | 0.3975 | 0.6228 |
| 13 | price_calendar_ai_gdelt | ridge | 0.0442 | 0.0552 | -0.1254 | 0.5706 | 0.9201 | 0.9512 |
| 13 | price_calendar_ai | hgb | 0.0455 | 0.0581 | -0.2467 | 0.5706 | 1.4307 | 1.5685 |
| 13 | price_calendar_ai | ridge | 0.0426 | 0.0529 | -0.0363 | 0.5706 | 1.7017 | 1.5530 |
| 13 | price_calendar_gdelt | hgb | 0.0478 | 0.0604 | -0.3490 | 0.4847 | 0.4373 | 0.6864 |
| 13 | price_calendar_gdelt | ridge | 0.0451 | 0.0550 | -0.1196 | 0.5460 | 1.1672 | 1.3175 |
| 13 | price_calendar | hgb | 0.0454 | 0.0579 | -0.2388 | 0.5706 | 1.3843 | 1.6971 |
| 13 | price_calendar | ridge | 0.0431 | 0.0528 | -0.0318 | 0.5583 | 1.7060 | 1.7737 |
| 13 | price_gdelt | hgb | 0.0514 | 0.0631 | -0.4745 | 0.4969 | 0.3683 | 0.5910 |
| 13 | price_gdelt | ridge | 0.0467 | 0.0589 | -0.2847 | 0.5215 | 0.5707 | 0.7715 |
| 13 | price_only | hgb | 0.0482 | 0.0608 | -0.3685 | 0.4847 | 0.4857 | 0.6794 |
| 13 | price_only | ridge | 0.0452 | 0.0567 | -0.1872 | 0.5153 | 1.2578 | 1.5907 |

## Volatility Pipeline

| horizon_weeks | feature_set | estimator | mae | rmse | r2 | spearman_corr | high_vol_balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | price_ai_gdelt | hgb | 0.0082 | 0.0101 | -0.1304 | 0.0370 | 0.4609 |
| 1 | price_ai_gdelt | ridge | 0.0079 | 0.0097 | -0.0396 | -0.0154 | 0.5000 |
| 1 | price_ai | hgb | 0.0082 | 0.0103 | -0.1718 | 0.0397 | 0.4747 |
| 1 | price_ai | ridge | 0.0080 | 0.0096 | -0.0283 | -0.0100 | 0.5000 |
| 1 | price_calendar_ai_gdelt | hgb | 0.0082 | 0.0102 | -0.1693 | 0.0045 | 0.4787 |
| 1 | price_calendar_ai_gdelt | ridge | 0.0080 | 0.0098 | -0.0807 | 0.0228 | 0.4735 |
| 1 | price_calendar_ai | hgb | 0.0083 | 0.0104 | -0.2102 | -0.0011 | 0.4724 |
| 1 | price_calendar_ai | ridge | 0.0080 | 0.0097 | -0.0584 | 0.0012 | 0.4994 |
| 1 | price_calendar_gdelt | hgb | 0.0081 | 0.0102 | -0.1595 | 0.0348 | 0.4805 |
| 1 | price_calendar_gdelt | ridge | 0.0079 | 0.0098 | -0.0780 | 0.0087 | 0.4937 |
| 1 | price_calendar | hgb | 0.0083 | 0.0103 | -0.1883 | 0.0250 | 0.4862 |
| 1 | price_calendar | ridge | 0.0080 | 0.0097 | -0.0558 | -0.0079 | 0.5115 |
| 1 | price_gdelt | hgb | 0.0082 | 0.0101 | -0.1292 | 0.0787 | 0.4805 |
| 1 | price_gdelt | ridge | 0.0078 | 0.0096 | -0.0330 | -0.0372 | 0.5000 |
| 1 | price_only | hgb | 0.0082 | 0.0103 | -0.1833 | 0.0596 | 0.4787 |
| 1 | price_only | ridge | 0.0079 | 0.0096 | -0.0249 | -0.0347 | 0.5000 |
| 4 | price_ai_gdelt | hgb | 0.0086 | 0.0106 | -0.2753 | 0.0176 | 0.4597 |
| 4 | price_ai_gdelt | ridge | 0.0084 | 0.0101 | -0.1531 | -0.1296 | 0.5000 |
| 4 | price_ai | hgb | 0.0087 | 0.0107 | -0.2935 | 0.0165 | 0.4637 |
| 4 | price_ai | ridge | 0.0082 | 0.0100 | -0.1226 | -0.1259 | 0.5000 |
| 4 | price_calendar_ai_gdelt | hgb | 0.0088 | 0.0108 | -0.3083 | -0.0147 | 0.4741 |
| 4 | price_calendar_ai_gdelt | ridge | 0.0085 | 0.0103 | -0.1929 | -0.0737 | 0.4839 |
| 4 | price_calendar_ai | hgb | 0.0089 | 0.0110 | -0.3714 | -0.0376 | 0.4741 |
| 4 | price_calendar_ai | ridge | 0.0083 | 0.0101 | -0.1554 | -0.0434 | 0.4879 |
| 4 | price_calendar_gdelt | hgb | 0.0088 | 0.0109 | -0.3493 | -0.0425 | 0.4845 |
| 4 | price_calendar_gdelt | ridge | 0.0084 | 0.0101 | -0.1443 | -0.0390 | 0.4943 |
| 4 | price_calendar | hgb | 0.0088 | 0.0111 | -0.3994 | -0.0304 | 0.4788 |
| 4 | price_calendar | ridge | 0.0082 | 0.0099 | -0.1078 | -0.0061 | 0.4983 |
| 4 | price_gdelt | hgb | 0.0086 | 0.0107 | -0.2856 | -0.0046 | 0.4701 |
| 4 | price_gdelt | ridge | 0.0082 | 0.0098 | -0.0926 | -0.0679 | 0.5000 |
| 4 | price_only | hgb | 0.0088 | 0.0109 | -0.3445 | -0.0227 | 0.4516 |
| 4 | price_only | ridge | 0.0080 | 0.0097 | -0.0602 | -0.0837 | 0.5000 |
| 13 | price_ai_gdelt | hgb | 0.0070 | 0.0089 | -0.4789 | 0.0924 | 0.5411 |
| 13 | price_ai_gdelt | ridge | 0.0071 | 0.0088 | -0.4300 | -0.1038 | 0.4816 |
| 13 | price_ai | hgb | 0.0070 | 0.0088 | -0.4437 | 0.0721 | 0.4818 |
| 13 | price_ai | ridge | 0.0068 | 0.0082 | -0.2354 | -0.0644 | 0.4963 |
| 13 | price_calendar_ai_gdelt | hgb | 0.0070 | 0.0092 | -0.5591 | 0.1739 | 0.5226 |
| 13 | price_calendar_ai_gdelt | ridge | 0.0072 | 0.0088 | -0.4323 | -0.0608 | 0.4669 |
| 13 | price_calendar_ai | hgb | 0.0070 | 0.0092 | -0.5698 | 0.1799 | 0.5114 |
| 13 | price_calendar_ai | ridge | 0.0067 | 0.0080 | -0.1858 | 0.0733 | 0.4926 |
| 13 | price_calendar_gdelt | hgb | 0.0068 | 0.0091 | -0.5419 | 0.2514 | 0.4931 |
| 13 | price_calendar_gdelt | ridge | 0.0069 | 0.0086 | -0.3700 | 0.0755 | 0.4634 |
| 13 | price_calendar | hgb | 0.0067 | 0.0092 | -0.5731 | 0.2448 | 0.5116 |
| 13 | price_calendar | ridge | 0.0065 | 0.0078 | -0.1411 | 0.2152 | 0.4891 |
| 13 | price_gdelt | hgb | 0.0068 | 0.0088 | -0.4481 | 0.1885 | 0.5633 |
| 13 | price_gdelt | ridge | 0.0070 | 0.0088 | -0.4364 | 0.0119 | 0.4375 |
| 13 | price_only | hgb | 0.0069 | 0.0088 | -0.4348 | 0.1175 | 0.4819 |
| 13 | price_only | ridge | 0.0066 | 0.0078 | -0.1307 | 0.0335 | 0.5000 |

## Takeaway

The horizon comparison is intended to show whether USDA/GLM and seasonality features work better as medium-horizon signals than as one-week signals. Direction and return results should be interpreted cautiously because multi-week cumulative returns are still noisy and overlapping. The volatility pipeline is the most economically natural horizon test because crop and weather information often changes the width of the return distribution before it gives a clean directional edge.
