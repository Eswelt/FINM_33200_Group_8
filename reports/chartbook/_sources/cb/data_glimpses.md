# Data Glimpses Report
Generated: 2026-05-26 16:53:15
Total files: 8

## Summary of Datasets by Task

### Build Features
- [`feature_panel.parquet`](#feature-panel-parquet)
- [`prices_CORN.csv`](#prices-corn-csv)

### Classify Move
- [`prices_CORN.csv`](#prices-corn-csv)
- [`price_target_predictions.csv`](#price-target-predictions-csv)

### Model Report
- [`predictions.csv`](#predictions-csv)

### Return Strategy
- [`prices_CORN.csv`](#prices-corn-csv)
- [`expected_return_predictions.csv`](#expected-return-predictions-csv)

### Select Threshold
- [`prices_CORN.csv`](#prices-corn-csv)
- [`threshold_selection_predictions.csv`](#threshold-selection-predictions-csv)

### Train Evaluate
- [`feature_panel.parquet`](#feature-panel-parquet)
- [`predictions.csv`](#predictions-csv)

### Wwcb Ai Features
- [`ai_weekly.parquet`](#ai-weekly-parquet)
- [`ai_wwcb_raw.parquet`](#ai-wwcb-raw-parquet)

---

## ai_weekly.parquet
**Path:** `data/interim/ai_weekly.parquet`
**Size:** 13931 bytes | **Type:** Parquet | **Shape:** 789 rows × 8 columns

### Columns
```
week                                     Datetime(time_unit='us', time_zone=None)
ai_moisture_stress                       Float64        
ai_heat_stress                           Float64        
ai_excess_rain_risk                      Float64        
ai_planting_delay_risk                   Float64        
ai_harvest_delay_risk                    Float64        
ai_yield_risk                            Float64        
ai_crop_condition_trend                  Float64        
```

### Sample Values (first 5 rows)
```
Rows: 789
Columns: 8
$ week                    <datetime[μs]> 2011-01-07 00:00:00, 2011-01-14 00:00:00, 2011-01-21 00:00:00, 2011-01-28 00:00:00, 2011-02-04 00:00:00
$ ai_moisture_stress               <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_heat_stress                   <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_excess_rain_risk              <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_planting_delay_risk           <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_harvest_delay_risk            <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_yield_risk                    <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_crop_condition_trend          <f64> 0.0, 0.0, 0.0, 0.0, 0.0
```

### Numeric Column Statistics
```
ai_moisture_stress: min=0.0, max=3.0, mean=0.17, median=0.0
ai_heat_stress: min=0.0, max=3.0, mean=0.12, median=0.0
ai_excess_rain_risk: min=0.0, max=3.0, mean=0.14, median=0.0
ai_planting_delay_risk: min=0.0, max=3.0, mean=0.17, median=0.0
ai_harvest_delay_risk: min=0.0, max=2.0, mean=0.12, median=0.0
ai_yield_risk: min=0.0, max=3.0, mean=0.30, median=0.0
ai_crop_condition_trend: min=-2.0, max=2.0, mean=-0.01, median=0.0
```

---

## ai_wwcb_raw.parquet
**Path:** `data/interim/ai_wwcb_raw.parquet`
**Size:** 31985 bytes | **Type:** Parquet | **Shape:** 789 rows × 14 columns

### Columns
```
week                                     Datetime(time_unit='us', time_zone=None)
report_date                              String         
source_file                              String         
ai_moisture_stress                       Float64        
ai_heat_stress                           Float64        
ai_excess_rain_risk                      Float64        
ai_planting_delay_risk                   Float64        
ai_harvest_delay_risk                    Float64        
ai_yield_risk                            Float64        
ai_crop_condition_trend                  Float64        
glm_model                                String         
glm_prompt_tokens                        Int64          
glm_completion_tokens                    Int64          
glm_total_tokens                         Int64          
```

### Sample Values (first 5 rows)
```
Rows: 789
Columns: 14
$ week                    <datetime[μs]> 2011-01-07 00:00:00, 2011-01-14 00:00:00, 2011-01-21 00:00:00, 2011-01-28 00:00:00, 2011-02-04 00:00:00
$ report_date                      <str> '2011-01-04', '2011-01-11', '2011-01-19', '2011-01-25', '2011-02-01'
$ source_file                      <str> 'data/external/wwcb_pdfs/weather_weekly-01-05-2011.pdf', 'data/external/wwcb_pdfs/weather_weekly-01-12-2011.pdf', 'data/external/wwcb_pdfs/weather_weekly-01-20-2011.pdf', 'data/external/wwcb_pdfs/weather_weekly-01-26-2011.pdf', 'data/external/wwcb_pdfs/weather_weekly-02-02-2011.pdf'
$ ai_moisture_stress               <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_heat_stress                   <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_excess_rain_risk              <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_planting_delay_risk           <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_harvest_delay_risk            <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_yield_risk                    <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_crop_condition_trend          <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ glm_model                        <str> 'glm-4.7-flash', 'glm-4.7-flash', 'glm-4.7-flash', 'glm-4.7-flash', 'glm-4.7-flash'
$ glm_prompt_tokens                <i64> 464, 464, 464, 464, 464
$ glm_completion_tokens            <i64> 96, 96, 96, 96, 96
$ glm_total_tokens                 <i64> 560, 560, 560, 560, 560
```

### Numeric Column Statistics
```
ai_moisture_stress: min=0.0, max=3.0, mean=0.17, median=0.0
ai_heat_stress: min=0.0, max=3.0, mean=0.12, median=0.0
ai_excess_rain_risk: min=0.0, max=3.0, mean=0.14, median=0.0
ai_planting_delay_risk: min=0.0, max=3.0, mean=0.17, median=0.0
ai_harvest_delay_risk: min=0.0, max=2.0, mean=0.12, median=0.0
ai_yield_risk: min=0.0, max=3.0, mean=0.30, median=0.0
ai_crop_condition_trend: min=-2.0, max=2.0, mean=-0.01, median=0.0
glm_prompt_tokens: min=464, max=4517, mean=812.76, median=602.0
glm_completion_tokens: min=89, max=96, mean=95.98, median=96.0
glm_total_tokens: min=560, max=4613, mean=908.75, median=698.0
```

---

## feature_panel.parquet
**Path:** `data/processed/feature_panel.parquet`
**Size:** 210890 bytes | **Type:** Parquet | **Shape:** 802 rows × 52 columns

### Columns
```
close                                    Float64        
volume                                   Int64          
week                                     Datetime(time_unit='us', time_zone=None)
price_log_close                          Float64        
price_log_return                         Float64         (0.1% null)
price_lag_return_1w                      Float64         (0.2% null)
price_lag_return_2w                      Float64         (0.4% null)
price_lag_return_4w                      Float64         (0.6% null)
price_lag_return_12w                     Float64         (1.6% null)
price_rolling_vol_4w                     Float64         (0.5% null)
price_rolling_vol_12w                    Float64         (1.5% null)
price_momentum_4w                        Float64         (0.5% null)
price_momentum_12w                       Float64         (1.5% null)
price_volume_change_4w                   Float64         (0.5% null)
target_log_return_next                   Float64         (0.1% null)
target_up_next                           Float64         (0.1% null)
calendar_month                           Int32          
calendar_quarter                         Int32          
calendar_week_of_year                    Int64          
calendar_week_sin                        Float64        
calendar_week_cos                        Float64        
calendar_is_planting_season              Int64          
calendar_is_pollination_weather_season   Int64          
calendar_is_harvest_season               Int64          
calendar_is_winter_storage_season        Int64          
weather_temp_mean_f                      Float64        
weather_precip_mm                        Float64        
weather_gdd                              Float64        
weather_temp_anomaly_f                   Float64        
weather_precip_anomaly_mm                Float64        
weather_forecast_temp_week1_f            Float64        
weather_forecast_precip_week1_mm         Float64        
weather_forecast_temp_week2_f            Float64        
weather_forecast_precip_week2_mm         Float64        
weather_year                             Int32          
report_text                              String         
report_count                             Int64          
text_kw_drought                          Int64          
text_kw_rain                             Int64          
text_kw_heat                             Int64          
text_kw_planting                         Int64          
text_kw_harvest                          Int64          
text_kw_yield                            Int64          
text_kw_export                           Int64          
text_kw_ethanol                          Int64          
ai_moisture_stress                       Float64         (1.6% null)
ai_heat_stress                           Float64         (1.6% null)
ai_excess_rain_risk                      Float64         (1.6% null)
ai_planting_delay_risk                   Float64         (1.6% null)
ai_harvest_delay_risk                    Float64         (1.6% null)
ai_yield_risk                            Float64         (1.6% null)
ai_crop_condition_trend                  Float64         (1.6% null)
```

### Sample Values (first 5 rows)
```
Rows: 802
Columns: 52
$ close                                           <f64> 22.45616321018651, 22.33453974462214, 22.392190003077836, 21.75809667646509, 22.178868211016503
$ volume                                          <i64> 1073599, 1135960, 1120464, 1217645, 1219154
$ week                                   <datetime[μs]> 2011-01-07 00:00:00, 2011-01-14 00:00:00, 2011-01-21 00:00:00, 2011-01-28 00:00:00, 2011-02-04 00:00:00
$ price_log_close                                 <f64> 3.1115651070322126, 3.106134347679831, 3.108712237487881, 3.0799859492496635, 3.0991399531638515
$ price_log_return                                <f64> null, -0.005430759352381465, 0.00257788980804996, -0.028726288238217546, 0.019154003914187978
$ price_lag_return_1w                             <f64> null, null, -0.005430759352381465, 0.00257788980804996, -0.028726288238217546
$ price_lag_return_2w                             <f64> null, null, null, -0.005430759352381465, 0.00257788980804996
$ price_lag_return_4w                             <f64> null, null, null, null, null
$ price_lag_return_12w                            <f64> null, null, null, null, null
$ price_rolling_vol_4w                            <f64> null, null, null, null, 0.01991329583245575
$ price_rolling_vol_12w                           <f64> null, null, null, null, null
$ price_momentum_4w                               <f64> null, null, null, null, -0.012425153868361072
$ price_momentum_12w                              <f64> null, null, null, null, null
$ price_volume_change_4w                          <f64> null, null, null, null, 0.12714061979042768
$ target_log_return_next                          <f64> -0.005430759352381465, 0.00257788980804996, -0.028726288238217546, 0.019154003914187978, -0.007852846750882936
$ target_up_next                                  <f64> 0.0, 1.0, 0.0, 1.0, 0.0
$ calendar_month                                  <i32> 1, 1, 1, 1, 2
$ calendar_quarter                                <i32> 1, 1, 1, 1, 1
$ calendar_week_of_year                           <i64> 1, 2, 3, 4, 5
$ calendar_week_sin                               <f64> 0.12053668025532305, 0.23931566428755774, 0.3546048870425356, 0.4647231720437685, 0.5680647467311558
$ calendar_week_cos                               <f64> 0.992708874098054, 0.970941817426052, 0.9350162426854148, 0.8854560256532099, 0.8229838658936564
$ calendar_is_planting_season                     <i64> 0, 0, 0, 0, 0
$ calendar_is_pollination_weather_season          <i64> 0, 0, 0, 0, 0
$ calendar_is_harvest_season                      <i64> 0, 0, 0, 0, 0
$ calendar_is_winter_storage_season               <i64> 1, 1, 1, 1, 1
$ weather_temp_mean_f                             <f64> 24.138762916729455, 27.705206811169017, 30.590972709341923, 34.412611356635175, 33.20059461592409
$ weather_precip_mm                               <f64> 7.383392305013175, 10.166843148745293, 11.799872327255878, 11.13757939408952, 14.973133901404852
$ weather_gdd                                     <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ weather_temp_anomaly_f                          <f64> -5.24448899537412, -1.6623283677233402, 0.06859144153178676, 2.2852389050530206, 2.396268533362388
$ weather_precip_anomaly_mm                       <f64> -1.6689264959935448, 2.0150364252257784, -0.3576529459245723, 1.3057155566209087, 4.894894104268705
$ weather_forecast_temp_week1_f                   <f64> 22.77857384956378, 28.225073377256063, 32.676367637233454, 34.246851773709125, 31.5193003497357
$ weather_forecast_precip_week1_mm                <f64> 1.178248349548526, 12.741298553260759, 15.12202477875238, 20.282685315286916, 21.69842376341291
$ weather_forecast_temp_week2_f                   <f64> 19.496900462617027, 29.383307177675206, 27.4660250540197, 34.56841451216575, 35.36437048110509
$ weather_forecast_precip_week2_mm                <f64> 5.690742036849238, 10.754046489919329, 12.053196427047673, 7.808407839788405, 16.84800157164146
$ weather_year                                    <i32> 2011, 2011, 2011, 2011, 2011
$ report_text                                     <str> 'Crop progress notes corn planting pace, yield condition, and harvest delays. Corn Belt yield rain soil moisture. Crop progress notes corn planting pace, yield condition, and harvest delays. Corn Belt yield rain soil moisture.', 'Weekly weather bulletin highlights rain, drought, heat, and soil moisture across the Corn Belt. Corn Belt yield rain soil moisture. Weekly weather bulletin highlights rain, drought, heat, and soil moisture across the Corn Belt. Corn Belt yield rain soil moisture.', 'Markets discuss export demand, ethanol use, and crop ratings for corn. Corn Belt yield rain soil moisture. Markets discuss export demand, ethanol use, and crop ratings for corn. Corn Belt yield rain soil moisture.', 'Crop progress notes corn planting pace, yield condition, and harvest delays. Corn Belt yield rain soil moisture. Crop progress notes corn planting pace, yield condition, and harvest delays. Corn Belt yield rain soil moisture.', 'Weekly weather bulletin highlights rain, drought, heat, and soil moisture across the Corn Belt. Corn Belt yield rain soil moisture. Weekly weather bulletin highlights rain, drought, heat, and soil moisture across the Corn Belt. Corn Belt yield rain soil moisture.'
$ report_count                                    <i64> 2, 2, 2, 2, 2
$ text_kw_drought                                 <i64> 0, 2, 0, 0, 2
$ text_kw_rain                                    <i64> 2, 4, 2, 2, 4
$ text_kw_heat                                    <i64> 0, 2, 0, 0, 2
$ text_kw_planting                                <i64> 2, 0, 0, 2, 0
$ text_kw_harvest                                 <i64> 2, 0, 0, 2, 0
$ text_kw_yield                                   <i64> 4, 2, 2, 4, 2
$ text_kw_export                                  <i64> 0, 0, 2, 0, 0
$ text_kw_ethanol                                 <i64> 0, 0, 2, 0, 0
$ ai_moisture_stress                              <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_heat_stress                                  <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_excess_rain_risk                             <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_planting_delay_risk                          <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_harvest_delay_risk                           <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_yield_risk                                   <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_crop_condition_trend                         <f64> 0.0, 0.0, 0.0, 0.0, 0.0
```

### Numeric Column Statistics
```
close: min=10.771362557195754, max=32.454616574824456, mean=20.21, median=21.99329894283777
volume: min=816013, max=1350999, mean=1074026.04, median=1075587.0
price_log_close: min=2.376890997297513, max=3.479842700360013, mean=2.95, median=3.090737662508623
price_log_return: min=-0.04967994866510317, max=0.0529566094015097, mean=-0.00, median=-0.00035372149320478385
price_lag_return_1w: min=-0.04967994866510317, max=0.0529566094015097, mean=-0.00, median=-0.00033014603484371463
price_lag_return_2w: min=-0.04967994866510317, max=0.0529566094015097, mean=-0.00, median=-0.0003065705764826454
price_lag_return_4w: min=-0.04967994866510317, max=0.0529566094015097, mean=-0.00, median=-0.00026690093345171917
price_lag_return_12w: min=-0.04967994866510317, max=0.0529566094015097, mean=-0.00, median=-0.00048154464968375166
price_rolling_vol_4w: min=0.0015885467944480685, max=0.036231878096158854, mean=0.02, median=0.015551830764662688
price_rolling_vol_12w: min=0.007555558486665588, max=0.026440798072540992, mean=0.02, median=0.016752351169801987
price_momentum_4w: min=-0.10102073782633347, max=0.09925102912748551, mean=-0.00, median=-0.0031695505832920468
price_momentum_12w: min=-0.19617381191835737, max=0.21358851117552957, mean=-0.01, median=-0.0117398816562293
price_volume_change_4w: min=-0.16714690655835346, max=0.18770733039090806, mean=-0.00, median=-0.004292832957425918
target_log_return_next: min=-0.04967994866510317, max=0.0529566094015097, mean=-0.00, median=-0.00035372149320478385
target_up_next: min=0.0, max=1.0, mean=0.49, median=0.0
calendar_month: min=1, max=12, mean=6.43, median=6.0
calendar_quarter: min=1, max=4, mean=2.48, median=2.0
calendar_week_of_year: min=1, max=53, mean=26.17, median=26.0
calendar_week_sin: min=-1.0, max=1.0, mean=0.02, median=6.432490598706546e-16
calendar_week_cos: min=-1.0, max=1.0, mean=0.01, median=-1.6081226496766366e-16
calendar_is_planting_season: min=0, max=1, mean=0.17, median=0.0
calendar_is_pollination_weather_season: min=0, max=1, mean=0.25, median=0.0
calendar_is_harvest_season: min=0, max=1, mean=0.24, median=0.0
calendar_is_winter_storage_season: min=0, max=1, mean=0.25, median=0.0
weather_temp_mean_f: min=24.105800392075874, max=87.38961319880403, mean=53.59, median=53.38310844817467
weather_precip_mm: min=0.0, max=40.488545937862014, mean=18.16, median=18.84287374615051
weather_gdd: min=0.0, max=261.7272923916282, mean=67.36, median=23.681759137222645
weather_temp_anomaly_f: min=-12.179558193469632, max=10.249991954370422, mean=0.00, median=-0.0018894469516510526
weather_precip_anomaly_mm: min=-14.182001642637282, max=17.523418270053362, mean=0.00, median=0.06379272920694312
weather_forecast_temp_week1_f: min=21.87789690850726, max=88.39781762061138, mean=53.63, median=54.17414676880444
weather_forecast_precip_week1_mm: min=0.0, max=50.08926895285116, mean=18.45, median=18.683879145220757
weather_forecast_temp_week2_f: min=19.496900462617027, max=89.11762214923885, mean=53.61, median=52.986969292580454
weather_forecast_precip_week2_mm: min=0.0, max=48.31869572004351, mean=18.22, median=18.23608412792977
weather_year: min=2011, max=2026, mean=2018.20, median=2018.0
report_count: min=2, max=2, mean=2.00, median=2.0
text_kw_drought: min=0, max=4, mean=1.00, median=0.0
text_kw_rain: min=0, max=4, mean=2.33, median=2.0
text_kw_heat: min=0, max=4, mean=1.00, median=0.0
text_kw_planting: min=0, max=4, mean=1.01, median=0.0
text_kw_harvest: min=0, max=4, mean=1.15, median=0.0
text_kw_yield: min=0, max=4, mean=1.84, median=2.0
text_kw_export: min=0, max=2, mean=0.67, median=0.0
text_kw_ethanol: min=0, max=2, mean=0.67, median=0.0
ai_moisture_stress: min=0.0, max=3.0, mean=0.17, median=0.0
ai_heat_stress: min=0.0, max=3.0, mean=0.12, median=0.0
ai_excess_rain_risk: min=0.0, max=3.0, mean=0.14, median=0.0
ai_planting_delay_risk: min=0.0, max=3.0, mean=0.17, median=0.0
ai_harvest_delay_risk: min=0.0, max=2.0, mean=0.12, median=0.0
ai_yield_risk: min=0.0, max=3.0, mean=0.30, median=0.0
ai_crop_condition_trend: min=-2.0, max=2.0, mean=-0.01, median=0.0
```

---

## prices_CORN.csv
**Path:** `data/raw/prices_CORN.csv`
**Size:** 447144 bytes | **Type:** Csv | **Shape:** 4,014 rows × 7 columns

### Columns
```
date                                     String         
open                                     Float64        
high                                     Float64        
low                                      Float64        
close                                    Float64        
adj_close                                Float64        
volume                                   Int64          
```

### Sample Values (first 5 rows)
```
Rows: 4014
Columns: 7
$ date      <str> '2011-01-03', '2011-01-04', '2011-01-05', '2011-01-06', '2011-01-07'
$ open      <f64> 22.14248619370409, 22.286173164779242, 22.467642394209545, 22.653097564874354, 22.41574797149947
$ high      <f64> 22.1484955424105, 22.31721884518081, 22.528934731665764, 22.74959581940239, 22.499934445280292
$ low       <f64> 22.135922649571697, 22.253746424855084, 22.382015644591, 22.580065402466676, 22.363407837487916
$ close     <f64> 22.136727392150547, 22.257675573156668, 22.430743749409164, 22.62189390554007, 22.45616321018651
$ adj_close <f64> 22.136727392150547, 22.257675573156668, 22.430743749409164, 22.62189390554007, 22.45616321018651
$ volume    <i64> 224197, 203252, 198926, 223346, 223878
```

### Numeric Column Statistics
```
open: min=10.814056892585334, max=32.456320220922905, mean=20.21, median=22.008949650214866
high: min=10.830804998257996, max=32.643888347095654, mean=20.26, median=22.054549024488942
low: min=10.748182697476071, max=32.384391804830216, mean=20.15, median=21.935101942671057
close: min=10.771362557195754, max=32.569995391864694, mean=20.21, median=22.000967411537722
adj_close: min=10.771362557195754, max=32.569995391864694, mean=20.21, median=22.000967411537722
volume: min=143919, max=291292, mean=214779.39, median=215205.5
```

---

## expected_return_predictions.csv
**Path:** `reports/expected_return_predictions.csv`
**Size:** 145226 bytes | **Type:** Csv | **Shape:** 700 rows × 18 columns

### Columns
```
week                                     String         
fold                                     Int64          
feature_set                              String         
estimator                                String         
model                                    String         
target_log_return_next                   Float64        
predicted_return                         Float64        
train_start                              String         
train_end                                String         
n_train                                  Int64          
trade_threshold                          Float64        
position                                 Float64        
turnover                                 Float64        
transaction_cost                         Float64        
strategy_log_return                      Float64        
benchmark_log_return                     Float64        
cum_strategy_return                      Float64        
cum_benchmark_return                     Float64        
```

### Sample Values (first 5 rows)
```
Rows: 700
Columns: 18
$ week                   <str> '2023-01-06', '2023-01-13', '2023-01-20', '2023-01-27', '2023-02-03'
$ fold                   <i64> 0, 0, 0, 0, 0
$ feature_set            <str> 'price_calendar', 'price_calendar', 'price_calendar', 'price_calendar', 'price_calendar'
$ estimator              <str> 'hgb', 'hgb', 'hgb', 'hgb', 'hgb'
$ model                  <str> 'price_calendar_hgb', 'price_calendar_hgb', 'price_calendar_hgb', 'price_calendar_hgb', 'price_calendar_hgb'
$ target_log_return_next <f64> 0.0024110656570526245, -0.007558729831937505, 0.04091419471991031, -0.00465628239000182, -0.0015193966698214822
$ predicted_return       <f64> 0.008489099733810127, 0.004242262824826182, -0.002621742966443223, 0.009952973865791396, 3.7244199907186776e-05
$ train_start            <str> '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07'
$ train_end              <str> '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30'
$ n_train                <i64> 626, 626, 626, 626, 626
$ trade_threshold        <f64> 0.003, 0.003, 0.003, 0.003, 0.003
$ position               <f64> 1.0, 1.0, 0.0, 1.0, 0.0
$ turnover               <f64> 1.0, 0.0, 1.0, 1.0, 1.0
$ transaction_cost       <f64> 0.0005, 0.0, 0.0005, 0.0005, 0.0005
$ strategy_log_return    <f64> 0.0019110656570526245, -0.007558729831937505, -0.0005, -0.005156282390001821, -0.0005
$ benchmark_log_return   <f64> 0.0024110656570526245, -0.007558729831937505, 0.04091419471991031, -0.00465628239000182, -0.0015193966698214822
$ cum_strategy_return    <f64> 0.0019128929068381595, -0.005631746100313362, -0.006128805951944871, -0.011240297017027112, -0.011734553294152295
$ cum_benchmark_return   <f64> 0.0024139746132789686, -0.0051344376566132555, 0.03641384726626007, 0.03159922952916583, 0.030033011249957386
```

### Numeric Column Statistics
```
fold: min=0, max=13, mean=6.24, median=6.0
target_log_return_next: min=-0.04705158725929204, max=0.04091419471991031, mean=0.00, median=0.0004587613480366848
predicted_return: min=-0.01671334611219972, max=0.01807692672272437, mean=-0.00, median=-0.0007957815765080265
n_train: min=626, max=795, mean=707.12, median=704.0
trade_threshold: min=0.003, max=0.003, mean=0.00, median=0.003
position: min=0.0, max=1.0, mean=0.15, median=0.0
turnover: min=0.0, max=1.0, mean=0.20, median=0.0
transaction_cost: min=0.0, max=0.0005, mean=0.00, median=0.0
strategy_log_return: min=-0.038672138662130984, max=0.02737802063894995, mean=0.00, median=-0.0
benchmark_log_return: min=-0.04705158725929204, max=0.04091419471991031, mean=0.00, median=0.0004587613480366848
cum_strategy_return: min=-0.07790436672785361, max=0.07324013247701933, mean=-0.01, median=-0.0074596142273398724
cum_benchmark_return: min=-0.04075585041612628, max=0.15913636058971115, mean=0.05, median=0.050862385429549795
```

---

## predictions.csv
**Path:** `reports/predictions.csv`
**Size:** 217351 bytes | **Type:** Csv | **Shape:** 1,050 rows × 19 columns

### Columns
```
week                                     String         
fold                                     Int64          
feature_set                              String         
estimator                                String         
model                                    String         
y_true                                   Int64          
y_prob                                   Float64        
y_pred                                   Int64          
target_log_return_next                   Float64        
train_start                              String         
train_end                                String         
n_train                                  Int64          
position                                 Float64        
turnover                                 Float64        
transaction_cost                         Float64        
strategy_log_return                      Float64        
benchmark_log_return                     Float64        
cum_strategy_return                      Float64        
cum_benchmark_return                     Float64        
```

### Sample Values (first 5 rows)
```
Rows: 1050
Columns: 19
$ week                   <str> '2023-01-06', '2023-01-13', '2023-01-20', '2023-01-27', '2023-02-03'
$ fold                   <i64> 0, 0, 0, 0, 0
$ feature_set            <str> 'A_price', 'A_price', 'A_price', 'A_price', 'A_price'
$ estimator              <str> 'hgb', 'hgb', 'hgb', 'hgb', 'hgb'
$ model                  <str> 'A_price_hgb', 'A_price_hgb', 'A_price_hgb', 'A_price_hgb', 'A_price_hgb'
$ y_true                 <i64> 1, 0, 1, 0, 0
$ y_prob                 <f64> 0.6402188047812658, 0.5234132278043067, 0.4443435314635209, 0.7757737221520584, 0.34346249158893427
$ y_pred                 <i64> 1, 1, 0, 1, 0
$ target_log_return_next <f64> 0.0024110656570526245, -0.007558729831937505, 0.04091419471991031, -0.00465628239000182, -0.0015193966698214822
$ train_start            <str> '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07'
$ train_end              <str> '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30'
$ n_train                <i64> 626, 626, 626, 626, 626
$ position               <f64> 1.0, 0.0, 0.0, 1.0, 0.0
$ turnover               <f64> 1.0, 1.0, 0.0, 1.0, 1.0
$ transaction_cost       <f64> 0.0005, 0.0005, 0.0, 0.0005, 0.0005
$ strategy_log_return    <f64> 0.0019110656570526245, -0.0005, 0.0, -0.005156282390001821, -0.0005
$ benchmark_log_return   <f64> 0.0024110656570526245, -0.007558729831937505, 0.04091419471991031, -0.00465628239000182, -0.0015193966698214822
$ cum_strategy_return    <f64> 0.0019128929068381595, 0.0014120616786257312, 0.0014120616786257312, -0.0037382121560421977, -0.004236218537993608
$ cum_benchmark_return   <f64> 0.0024139746132789686, -0.0051344376566132555, 0.03641384726626007, 0.03159922952916583, 0.030033011249957386
```

### Numeric Column Statistics
```
fold: min=0, max=13, mean=6.24, median=6.0
y_true: min=0, max=1, mean=0.51, median=1.0
y_prob: min=0.02823961613811589, max=0.8832203549030702, mean=0.45, median=0.45332479516151225
y_pred: min=0, max=1, mean=0.32, median=0.0
target_log_return_next: min=-0.04705158725929204, max=0.04091419471991031, mean=0.00, median=0.0004587613480366848
n_train: min=626, max=795, mean=707.12, median=704.0
position: min=0.0, max=1.0, mean=0.18, median=0.0
turnover: min=0.0, max=1.0, mean=0.25, median=0.0
transaction_cost: min=0.0, max=0.0005, mean=0.00, median=0.0
strategy_log_return: min=-0.04705158725929204, max=0.0332447468782755, mean=0.00, median=-0.0
benchmark_log_return: min=-0.04705158725929204, max=0.04091419471991031, mean=0.00, median=0.0004587613480366848
cum_strategy_return: min=-0.115060323996101, max=0.15510986273523808, mean=0.01, median=0.005102775281234262
cum_benchmark_return: min=-0.04075585041612628, max=0.15913636058971115, mean=0.05, median=0.050862385429549795
```

---

## price_target_predictions.csv
**Path:** `reports/price_target_predictions.csv`
**Size:** 88735 bytes | **Type:** Csv | **Shape:** 700 rows × 13 columns

### Columns
```
week                                     String         
fold                                     Int64          
experiment                               String         
feature_set                              String         
model                                    String         
y_true_return                            Float64         (50.0% null)
y_pred_return                            Float64         (50.0% null)
train_start                              String         
train_end                                String         
n_train                                  Int64          
y_true_3class                            String          (50.0% null)
y_pred_3class                            String          (50.0% null)
target_log_return_next                   String          (50.0% null)
```

### Sample Values (first 5 rows)
```
Rows: 700
Columns: 13
$ week                   <str> '2023-01-06', '2023-01-13', '2023-01-20', '2023-01-27', '2023-02-03'
$ fold                   <i64> 0, 0, 0, 0, 0
$ experiment             <str> 'return_regression', 'return_regression', 'return_regression', 'return_regression', 'return_regression'
$ feature_set            <str> 'price_calendar', 'price_calendar', 'price_calendar', 'price_calendar', 'price_calendar'
$ model                  <str> 'price_only_ridge', 'price_only_ridge', 'price_only_ridge', 'price_only_ridge', 'price_only_ridge'
$ y_true_return          <f64> 0.0024110656570526245, -0.007558729831937505, 0.04091419471991031, -0.00465628239000182, -0.0015193966698214822
$ y_pred_return          <f64> -0.0026879685651374835, -0.002673485234279229, -0.0023521984721173233, -5.8082546002575716e-05, -0.001127041103793948
$ train_start            <str> '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07'
$ train_end              <str> '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30'
$ n_train                <i64> 626, 626, 626, 626, 626
$ y_true_3class          <str> null, null, null, null, null
$ y_pred_3class          <str> null, null, null, null, null
$ target_log_return_next <str> null, null, null, null, null
```

### Numeric Column Statistics
```
fold: min=0, max=13, mean=6.24, median=6.0
y_true_return: min=-0.04705158725929204, max=0.04091419471991031, mean=0.00, median=0.0004587613480366848
y_pred_return: min=-0.008114867796390077, max=0.004914865276110814, mean=-0.00, median=-0.0007107599942706166
n_train: min=626, max=795, mean=707.12, median=704.0
```

---

## threshold_selection_predictions.csv
**Path:** `reports/threshold_selection_predictions.csv`
**Size:** 93958 bytes | **Type:** Csv | **Shape:** 350 rows × 22 columns

### Columns
```
week                                     String         
fold                                     Int64          
k                                        Float64        
feature_set                              String         
y_true                                   Int64          
y_pred                                   Int64          
prob_down                                Float64        
prob_flat                                Float64        
prob_up                                  Float64        
target_log_return_next                   Float64        
target_vol_threshold                     Float64        
train_start                              String         
train_end                                String         
n_train                                  Int64          
position                                 Float64        
turnover                                 Float64        
transaction_cost                         Float64        
strategy_log_return                      Float64        
benchmark_log_return                     Float64        
cum_strategy_return                      Float64        
cum_benchmark_return                     Float64        
model                                    String         
```

### Sample Values (first 5 rows)
```
Rows: 350
Columns: 22
$ week                   <str> '2023-01-06', '2023-01-13', '2023-01-20', '2023-01-27', '2023-02-03'
$ fold                   <i64> 0, 0, 0, 0, 0
$ k                      <f64> 1.0, 1.0, 1.0, 1.0, 1.0
$ feature_set            <str> 'price_calendar', 'price_calendar', 'price_calendar', 'price_calendar', 'price_calendar'
$ y_true                 <i64> 0, 0, 1, 0, 0
$ y_pred                 <i64> -1, -1, -1, 0, -1
$ prob_down              <f64> 0.4089638956470679, 0.4315188156953112, 0.3992392298292426, 0.26959071483369096, 0.43944669413731663
$ prob_flat              <f64> 0.24900209852312147, 0.22299527851128634, 0.23058276154151716, 0.5097886098082101, 0.2876467887880634
$ prob_up                <f64> 0.34203400582981064, 0.3454859057934025, 0.37017800862924033, 0.22062067535809904, 0.2729065170746198
$ target_log_return_next <f64> 0.0024110656570526245, -0.007558729831937505, 0.04091419471991031, -0.00465628239000182, -0.0015193966698214822
$ target_vol_threshold   <f64> 0.013644533249982079, 0.013718338714047698, 0.01339534651793115, 0.018913421298383158, 0.018257719549027246
$ train_start            <str> '2011-04-01', '2011-04-01', '2011-04-01', '2011-04-01', '2011-04-01'
$ train_end              <str> '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30'
$ n_train                <i64> 614, 614, 614, 614, 614
$ position               <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ turnover               <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ transaction_cost       <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ strategy_log_return    <f64> 0.0, -0.0, 0.0, -0.0, -0.0
$ benchmark_log_return   <f64> 0.0024110656570526245, -0.007558729831937505, 0.04091419471991031, -0.00465628239000182, -0.0015193966698214822
$ cum_strategy_return    <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ cum_benchmark_return   <f64> 0.0024139746132789686, -0.0051344376566132555, 0.03641384726626007, 0.03159922952916583, 0.030033011249957386
$ model                  <str> 'vol_adj_k_1.0_price_calendar', 'vol_adj_k_1.0_price_calendar', 'vol_adj_k_1.0_price_calendar', 'vol_adj_k_1.0_price_calendar', 'vol_adj_k_1.0_price_calendar'
```

### Numeric Column Statistics
```
fold: min=0, max=13, mean=6.24, median=6.0
k: min=1.0, max=1.0, mean=1.00, median=1.0
y_true: min=-1, max=1, mean=0.02, median=0.0
y_pred: min=-1, max=1, mean=0.09, median=0.0
prob_down: min=0.1884168661919031, max=0.5635636274932235, mean=0.33, median=0.3263161486743439
prob_flat: min=0.1328233823040115, max=0.674620867749485, mean=0.34, median=0.32459922753061626
prob_up: min=0.11751729550507463, max=0.5780850306801594, mean=0.33, median=0.3322772124949458
target_log_return_next: min=-0.04705158725929204, max=0.04091419471991031, mean=0.00, median=0.0004587613480366848
target_vol_threshold: min=0.009536113165658949, max=0.02255829546706191, mean=0.02, median=0.016199501916877603
n_train: min=614, max=783, mean=695.12, median=692.0
position: min=0.0, max=1.0, mean=0.09, median=0.0
turnover: min=0.0, max=1.0, mean=0.10, median=0.0
transaction_cost: min=0.0, max=0.0005, mean=0.00, median=0.0
strategy_log_return: min=-0.01857012219783699, max=0.02552126719586595, mean=0.00, median=0.0
benchmark_log_return: min=-0.04705158725929204, max=0.04091419471991031, mean=0.00, median=0.0004587613480366848
cum_strategy_return: min=-0.019265152072670988, max=0.09072365321143483, mean=0.02, median=0.03084648100507159
cum_benchmark_return: min=-0.04075585041612628, max=0.15913636058971115, mean=0.05, median=0.050862385429549795
```