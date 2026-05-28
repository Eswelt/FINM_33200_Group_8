# Data Glimpses Report
Generated: 2026-05-28 00:30:21
Total files: 10

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

### Volatility
- [`prices_CORN.csv`](#prices-corn-csv)
- [`volatility_predictions.csv`](#volatility-predictions-csv)

### Wwcb Ai Features
- [`ai_weekly.parquet`](#ai-weekly-parquet)
- [`ai_wwcb_raw.parquet`](#ai-wwcb-raw-parquet)
- [`wwcb_core_text.parquet`](#wwcb-core-text-parquet)

### Wwcb Ai Features Mock
- [`wwcb_core_text.parquet`](#wwcb-core-text-parquet)

### Wwcb Parse
- [`wwcb_core_text.parquet`](#wwcb-core-text-parquet)

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

## wwcb_core_text.parquet
**Path:** `data/interim/wwcb_core_text.parquet`
**Size:** 3.0 MB | **Type:** Parquet | **Shape:** 806 rows × 9 columns

### Columns
```
source_file                              String         
report_date                              String         
week_ending                              String         
week                                     String         
weather_highlights                       String         
national_ag_summary                      String         
corn_section                             String         
corn_table_text                          String         
report_text                              String         
```

### Sample Values (first 5 rows)
```
Rows: 806
Columns: 9
$ source_file         <str> 'data/external/wwcb_pdfs/weather_weekly-01-02-2013.pdf', 'data/external/wwcb_pdfs/weather_weekly-01-03-2018.pdf', 'data/external/wwcb_pdfs/weather_weekly-01-04-2017.pdf', 'data/external/wwcb_pdfs/weather_weekly-01-05-2011.pdf', 'data/external/wwcb_pdfs/weather_weekly-01-05-2012.pdf'
$ report_date         <str> '2013-01-02', '2018-01-03', '2017-01-04', '2011-01-04', '2012-01-05'
$ week_ending         <str> '2012-12-29', '2017-12-30', '2016-12-31', '2010-12-25', '2011-12-31'
$ week                <str> '2013-01-04', '2018-01-05', '2017-01-06', '2011-01-07', '2012-01-06'
$ weather_highlights  <str> '', '', '', '', ''
$ national_ag_summary <str> '', 'During the last week of 2017, frigid weather blanketed Temperatures east of the Rockies were below\nthe northern part of the nation, particularly along the average, while many Western States were warmer\nCanadian border. Temperatures in Montana, which than normal. Most of the nation was fairly dry during\nhad been warmer than average for most of the week, with snow reported in the North and rain\nDecember, plunged well below zero at month’s end. falling along the Gulf and Southern Atlantic Coasts.\n\nCalifornia: As the end of the year approached, much of the Florida: There were 6.5 days suitable for fieldwork for the\nstate was subject to warmer-than-average afternoon week ending Sunday, December 31, 2017. Precipitation\ntemperatures, while evening temperatures were seasonal. estimates ranged from no rain in multiple locations to 1.23\nAlong the northern coast, occasional light rain appeared at the inches in Miami-Dade County. The average mean temperature\nstart of the week before giving way to high pressure aloft. ranged from 43.4°F in Leon County to 75.2°F in Monroe\nHigh pressure dominated the central interior region throughout County. Some cover crops, such as millet and rye, were\nthe week. Hazy conditions existed most nights. In the south, planted in Dixie and Volusia Counties. Sugarcane harvest was\nthe beginning of the week brought high clouds and mist or ongoing in Glades and Hendry Counties. Temperatures were\nhaze. Conditions dried out as high pressure strengthened aloft, variable in the citrus region last week as cooler weather began\nfollowed by a warming trend over the region. At the end of to enter the peninsula. Lows were in the 50s and upper 40s,\nthe week, high broke down and moved northward, allowing for while highs ranged from the mid-60s to a maximum of 80°F,\nsome regional cooling. Fields that were planted earlier in the as reported in DeSoto County. No significant rainfall was\nseason had signs of good growth, though most fields were recorded during the week. Grove operations included\nirrigated due to the lack of rain to maintain growth. Planting fertilizing, mowing, topping and hedging, spraying, and\nwas ongoing for wheat, other cereal grains, and forage. harvesting. All growers irrigated regularly due to the drier-\nPruning continued in stone fruit orchards and vineyards, while than-normal weather. Field staff reported more instances of\nsome older, poorly producing orchards and vineyards were sporadic bloom, especially in Navel orange groves.\nremoved and prepared for replanting. Some growers prepared Tangerines and tangelos being harvested for the fresh market\nto apply winter dormant sprays. The Navel orange and pomelo included midseason cultivars (Autumn Honey, Orri, Osceola,\nharvests continued, but overnight temperatures were a concern Robinson and Tango tangerines, and Orlando tangelos were\nfor citrus growers. Olive growers continued to prune groves the main varieties at the packinghouses). Early orange harvest\nand strawberry fields thrived. Pruning continued in nut for the fresh market was mostly Hamlins and Navels.\norchards, while some older orchards were pushed out and the Persistently dry conditions caused continued irrigation in Palm\nground was prepped for planting. Fields were being prepared Beach County. Foggy conditions persisted in several southern\nand planted with winter vegetable crops, while lettuce counties, increasing disease pressures in some vegetable crops.\ncontinued to grow well. In already-planted winter vegetable Growers continued to plant cool season crops and were\nfields, crops continued to develop. Work continued preparing harvesting a wide variety of crops, including avocado, beans,\ntomato beds and planting onions. Brussels sprouts were eggplant, herbs, peppers, radishes, squash, sweet corn,\nharvested in San Mateo County. In Tulare County, the lack of tomatoes, and zucchini. Hard freezes in Holmes County had\nrainfall has left rangeland forage conditions poor. More rain winter grazing at a standstill. In Washington County, forages\nwas needed for germination and growth of rangeland forage. were beginning to improve as moisture conditions remained\nSupplemental feeding was ongoing. Sheep were grazing on favorable. Pasture quality continued to decline as a result of\nidle cropland, stubble fields, and dormant alfalfa fields. Honey cold weather. Producers in several counties were feeding\nbees were moved into almond orchards in preparation for supplements as necessary. Cattle remained in mostly good\nbloom. condition throughout the state.', 'Most of the nation experienced above-average 0°F in large sections of the Rocky Mountains and\ntemperatures, with the southern Great Plains the Great Basin. Precipitation totaled less than 2\nand lower Mississippi Valley recording inches in most locations, with the most notable\ntemperatures more than 10°F above normal. In exception being the central Gulf Coast, where in\ncontrast, the Northwest had below-average some areas rainfall totaled more than 4.5 inches\ntemperatures, with temperatures dipping below above normal weekly values.\n\nArizona: Barley and Durum wheat planting was well underway by level of the ground allowed. Winter wheat continued to progress\nthe end of the week. Barley planting was 25 percent complete, well due to adequate soil moisture. Post-harvest pruning and\ncompared to 29 percent last year and 49 percent for the 5-year orchard removal continued in all deciduous tree fruit orchards and\naverage. Durum wheat planting was estimated at 22 percent vineyards. Wet weather slowed citrus harvest. Navel and Mandarin\ncomplete, 8 percentage points ahead of last year. Alfalfa conditions oranges were harvested and exported. Melogold grapefruit, lemons,\nwere rated mostly good to excellent, depending on location, with and limes were exported. New planting of citrus trees were covered\nharvesting taking place on almost three-quarters of the state’s alfalfa for frost protection. Almonds, pistachios, shelled and in-shell\nacreage. Central Arizona growers shipped anise, beets, broccoli, walnuts, and shelled pecans continued to be packed and shipped.\ncabbage (green and red), carrots, cauliflower, cilantro, kale greens, Nut orchards continued to be pruned, irrigated, and treated in\ngreen onions, parsley, and Swiss chard. In western Arizona, growers preparation for their dormant season. Orchard replanting continued.\nshipped anise, arugula, bok choy, broccoli, cabbage (green and red), In San Joaquin County, winter farmers’ market vegetables were\ncauliflower, celery, Chinese cabbage, cilantro, endive, escarole, harvested. In Fresno County, winter vegetables were in good\nfrisee, kale greens, lettuce (Boston, green leaf, iceberg, red leaf, condition. Irrigation was not needed due to the rainy weather. With\nromaine and other), parsley, radicchio, and spinach. Beneficial rains snow covering higher rangeland, more cattle were in valley pastures\ncontinued last week in Coconino and Yavapai Counties, where soil and most were being fed supplemental hay. Also in Fresno County,\nmoisture levels were reported as high and water tanks were nearly full supplemental feeding of livestock continued as new germination of\nor completely full. Wheat planting was delayed in Graham County rangeland grasses improved from recent rains. Sheep were grazing\naccording to respondents, due to cold and wet weather. For the on idle crop fields, dormant alfalfa, and stubble crop grounds.\nsecond week in a row, every weather station reported some\nmeasurable precipitation. Douglas reported the least at 0.07 inch, Florida: There were 6.4 days suitable for fieldwork. Precipitation\nwhile Payson reported the most at 1.71 inches. All but 12 of the estimates ranged from no rain in several locations including Apopka\n52 weather stations reported above-normal temperatures. The highest (Orange County), Dade City (Pasco County), and Sebring\ntemperature was 78°F at Buckeye; the lowest was 0°F at Flagstaff. (Highlands County) to 7.74 inches in DeFuniak Springs\n(Walton County). Average temperatures ranged from 60.6°F in\nCalifornia: Rainfall was limited to the far northwestern mountains Macclenny (Baker County) to 73.2°F in Ft. Lauderdale\non Monday, where over an inch of rain fell. Tuesday and (Broward County). Although rain fell during the week across many\nWednesday were fairly dry, but the Pineapple Express began on parts of the state, most farms remain in drought or abnormally dry.\nThursday evening affecting areas from Salinas to Los Angeles with In the citrus-growing region, temperatures were warmer than\nlight rain. Friday and Saturday saw moderate to heavy rain across average for the first part of the week. Daily highs were in the mid\nthe southern one-third of the state, with the highest totals (over to upper 80s on most afternoons. A front passing through the center\n2 inches) in and around Bakersfield. The deserts received around an of the state late Thursday lowered temperature about 20°F, but did\ninch of rain, while other locations in the southern valley saw up to not bring much rain. Canals and ditches remained at low levels due\nan inch. Upslope showers also affected the central Sierras, where of the lack of widespread rain over the past couple of months.\nup to one-half of an inch of rain fell. On Sunday, the main rainfall Growers were irrigating frequently to keep moisture in the ground\narea shifted to the northern half of the state, where most locations and on the trees. Early tangerine harvest (Fallglo and Sunburst) was\nsaw up to one-quarter inch of rain, but the northwestern mountains about over for the season. Early and mid-season oranges were still\nand windward slopes of the Sierras saw just over one-half inch. being harvested for the fresh market. Grapefruit harvest was in full\nTemperatures at higher elevations in the central and southern swing, with internal quality holding well. All processing plants\nSierras were low enough to result in snow. Up to 10 inches of new were open and accepting field-run fruit. Growers continued to\nsnow fell at high elevations, particularly at Mt. Whitney. Up to spray in order to lower the psyllid population. Primarily, growers\n6 inches fell just south of Tahoe. However, mild weather resulted were performing general grove maintenance in well-kept groves.\nin a decrease of the mountain snowpack, as meltwater runoff Strawberry harvesting activities were reported during the week in\nincreased. High temperatures were in the 30s to 50s in the Hillsborough County. Greens, cabbage, and broccoli were being\nmountains, 40s to 50s along the coast and in the valley, and 50s to planted in Bradford County. Spring watermelons continued to be\n70s in the desert. Low temperatures were between the 0s and 30s in planted in several counties. Crops coming to market included\nthe mountains; 20s to 40s in the desert; and 30s to 40s in the coast avocado, beets, bitter melon, boniato, collards, eggplant, green\nand valley. On Monday and Tuesday temperatures fell into the 20s beans, kale, malanga, pepper, squash, sweet corn, tomato, zucchini,\nwith widespread hard freezes across the agricultural areas of the and other tropical fruits. Cattle condition remained mostly fair to\nvalley, and subzero temperatures in the mountains. Field good despite persistently dry conditions and deteriorating pasture\npreparation for winter forage crops continued where the moisture quality. Many cattle operators were using supplemental feeding.', '', ''
$ corn_section        <str> '', '', '', '', ''
$ corn_table_text     <str> '', '', '', '', ''
$ report_text         <str> '[WEATHER HIGHLIGHTS]\n\n[CORN SECTION]\n\n[CORN PROGRESS TABLE]', '[WEATHER HIGHLIGHTS]\n\n[CORN SECTION]\n\n[CORN PROGRESS TABLE]', '[WEATHER HIGHLIGHTS]\n\n[CORN SECTION]\n\n[CORN PROGRESS TABLE]', '[WEATHER HIGHLIGHTS]\n\n[CORN SECTION]\n\n[CORN PROGRESS TABLE]', '[WEATHER HIGHLIGHTS]\n\n[CORN SECTION]\n\n[CORN PROGRESS TABLE]'
```

---

## feature_panel.parquet
**Path:** `data/processed/feature_panel.parquet`
**Size:** 162923 bytes | **Type:** Parquet | **Shape:** 802 rows × 39 columns

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
report_text                              String         
ai_moisture_stress                       Float64         (1.6% null)
ai_heat_stress                           Float64         (1.6% null)
ai_excess_rain_risk                      Float64         (1.6% null)
ai_planting_delay_risk                   Float64         (1.6% null)
ai_harvest_delay_risk                    Float64         (1.6% null)
ai_yield_risk                            Float64         (1.6% null)
ai_crop_condition_trend                  Float64         (1.6% null)
gdelt_relevance_score                    Float64         (28.1% null)
gdelt_yield_supply_risk                  Float64         (28.1% null)
gdelt_inventory_supply_tightness         Float64         (28.1% null)
gdelt_demand_strength                    Float64         (28.1% null)
gdelt_ethanol_export_signal              Float64         (28.1% null)
gdelt_trade_policy_risk                  Float64         (28.1% null)
```

### Sample Values (first 5 rows)
```
Rows: 802
Columns: 39
$ close                                           <f64> 37.43000030517578, 40.22999954223633, 40.70000076293945, 40.099998474121094, 42.150001525878906
$ volume                                          <i64> 443900, 657300, 371200, 310100, 420000
$ week                                   <datetime[μs]> 2011-01-07 00:00:00, 2011-01-14 00:00:00, 2011-01-21 00:00:00, 2011-01-28 00:00:00, 2011-02-04 00:00:00
$ price_log_close                                 <f64> 3.6224725300695777, 3.6946129745830323, 3.7062281111939903, 3.6913762962606795, 3.741234720649024
$ price_log_return                                <f64> null, 0.07214044451345458, 0.011615136610958032, -0.01485181493331078, 0.049858424388344424
$ price_lag_return_1w                             <f64> null, null, 0.07214044451345458, 0.011615136610958032, -0.01485181493331078
$ price_lag_return_2w                             <f64> null, null, null, 0.07214044451345458, 0.011615136610958032
$ price_lag_return_4w                             <f64> null, null, null, null, null
$ price_lag_return_12w                            <f64> null, null, null, null, null
$ price_rolling_vol_4w                            <f64> null, null, null, null, 0.03881356955406374
$ price_rolling_vol_12w                           <f64> null, null, null, null, null
$ price_momentum_4w                               <f64> null, null, null, null, 0.11876219057944626
$ price_momentum_12w                              <f64> null, null, null, null, null
$ price_volume_change_4w                          <f64> null, null, null, null, -0.05534460056257558
$ target_log_return_next                          <f64> 0.07214044451345458, 0.011615136610958032, -0.01485181493331078, 0.049858424388344424, 0.03473942632978799
$ target_up_next                                  <f64> 1.0, 1.0, 0.0, 1.0, 1.0
$ calendar_month                                  <i32> 1, 1, 1, 1, 2
$ calendar_quarter                                <i32> 1, 1, 1, 1, 1
$ calendar_week_of_year                           <i64> 1, 2, 3, 4, 5
$ calendar_week_sin                               <f64> 0.12053668025532305, 0.23931566428755774, 0.3546048870425356, 0.4647231720437685, 0.5680647467311558
$ calendar_week_cos                               <f64> 0.992708874098054, 0.970941817426052, 0.9350162426854148, 0.8854560256532099, 0.8229838658936564
$ calendar_is_planting_season                     <i64> 0, 0, 0, 0, 0
$ calendar_is_pollination_weather_season          <i64> 0, 0, 0, 0, 0
$ calendar_is_harvest_season                      <i64> 0, 0, 0, 0, 0
$ calendar_is_winter_storage_season               <i64> 1, 1, 1, 1, 1
$ report_text                                     <str> '', '', '', '', ''
$ ai_moisture_stress                              <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_heat_stress                                  <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_excess_rain_risk                             <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_planting_delay_risk                          <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_harvest_delay_risk                           <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_yield_risk                                   <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ ai_crop_condition_trend                         <f64> 0.0, 0.0, 0.0, 0.0, 0.0
$ gdelt_relevance_score                           <f64> null, null, null, null, null
$ gdelt_yield_supply_risk                         <f64> null, null, null, null, null
$ gdelt_inventory_supply_tightness                <f64> null, null, null, null, null
$ gdelt_demand_strength                           <f64> null, null, null, null, null
$ gdelt_ethanol_export_signal                     <f64> null, null, null, null, null
$ gdelt_trade_policy_risk                         <f64> null, null, null, null, null
```

### Numeric Column Statistics
```
close: min=11.59000015258789, max=51.36000061035156, mean=24.43, median=20.90999984741211
volume: min=60700, max=9555100, mean=676546.13, median=398150.0
price_log_close: min=2.4501426705171383, max=3.9388596712654977, mean=3.13, median=3.0402201872692
price_log_return: min=-0.13984923381861636, max=0.11158576469817572, mean=-0.00, median=-0.0005964944213276979
price_lag_return_1w: min=-0.13984923381861636, max=0.11158576469817572, mean=-0.00, median=-0.0005821026957320008
price_lag_return_2w: min=-0.13984923381861636, max=0.11158576469817572, mean=-0.00, median=-0.0005677109701363037
price_lag_return_4w: min=-0.13984923381861636, max=0.11158576469817572, mean=-0.00, median=-0.0005964944213276979
price_lag_return_12w: min=-0.13984923381861636, max=0.11158576469817572, mean=-0.00, median=-0.0006337280979558102
price_rolling_vol_4w: min=0.0015756596193694358, max=0.10972818015591461, mean=0.02, median=0.02148892925655887
price_rolling_vol_12w: min=0.00890176468741303, max=0.08032535289019585, mean=0.03, median=0.023510440417527503
price_momentum_4w: min=-0.22093450024319905, max=0.30313848706068525, mean=-0.00, median=-0.003797647256803538
price_momentum_12w: min=-0.29371849352609614, max=0.36294226478401503, mean=-0.01, median=-0.019747363018708164
price_volume_change_4w: min=-1.7668431179635204, max=3.5579259226646456, mean=0.01, median=-0.03001673628646175
target_log_return_next: min=-0.13984923381861636, max=0.11158576469817572, mean=-0.00, median=-0.0005964944213276979
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
ai_moisture_stress: min=0.0, max=3.0, mean=0.17, median=0.0
ai_heat_stress: min=0.0, max=3.0, mean=0.12, median=0.0
ai_excess_rain_risk: min=0.0, max=3.0, mean=0.14, median=0.0
ai_planting_delay_risk: min=0.0, max=3.0, mean=0.17, median=0.0
ai_harvest_delay_risk: min=0.0, max=2.0, mean=0.12, median=0.0
ai_yield_risk: min=0.0, max=3.0, mean=0.30, median=0.0
ai_crop_condition_trend: min=-2.0, max=2.0, mean=-0.01, median=0.0
gdelt_relevance_score: min=0.0, max=2.5384615384615383, mean=1.85, median=1.9047619047619047
gdelt_yield_supply_risk: min=0.0, max=1.847457627118644, mean=0.85, median=0.845679012345679
gdelt_inventory_supply_tightness: min=0.0, max=1.4179104477611941, mean=0.66, median=0.6470588235294118
gdelt_demand_strength: min=0.0, max=2.255892255892256, mean=0.95, median=0.9192546583850931
gdelt_ethanol_export_signal: min=0.0, max=1.7965451055662187, mean=0.63, median=0.5766871165644172
gdelt_trade_policy_risk: min=0.0, max=1.86, mean=0.27, median=0.20714285714285716
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
**Size:** 598336 bytes | **Type:** Csv | **Shape:** 2,800 rows × 18 columns

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
Rows: 2800
Columns: 18
$ week                   <str> '2023-01-06', '2023-01-13', '2023-01-20', '2023-01-27', '2023-02-03'
$ fold                   <i64> 0, 0, 0, 0, 0
$ feature_set            <str> 'price_ai_gdelt', 'price_ai_gdelt', 'price_ai_gdelt', 'price_ai_gdelt', 'price_ai_gdelt'
$ estimator              <str> 'hgb', 'hgb', 'hgb', 'hgb', 'hgb'
$ model                  <str> 'price_ai_gdelt_hgb', 'price_ai_gdelt_hgb', 'price_ai_gdelt_hgb', 'price_ai_gdelt_hgb', 'price_ai_gdelt_hgb'
$ target_log_return_next <f64> 0.026637756991465977, -0.005271073667588055, 0.0018857687565256853, 0.0015059870145548437, 0.0030052586123381353
$ predicted_return       <f64> 0.008084752295827505, -0.0032932471307475196, 0.004446621839089969, -0.008702088708664162, -0.003893687693006561
$ train_start            <str> '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07'
$ train_end              <str> '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30'
$ n_train                <i64> 626, 626, 626, 626, 626
$ trade_threshold        <f64> 0.003, 0.003, 0.003, 0.003, 0.003
$ position               <f64> 1.0, 0.0, 1.0, 0.0, 0.0
$ turnover               <f64> 1.0, 1.0, 1.0, 1.0, 0.0
$ transaction_cost       <f64> 0.0005, 0.0005, 0.0005, 0.0005, 0.0
$ strategy_log_return    <f64> 0.026137756991465977, -0.0005, 0.0013857687565256853, -0.0005, 0.0
$ benchmark_log_return   <f64> 0.026637756991465977, -0.005271073667588055, 0.0018857687565256853, 0.0015059870145548437, 0.0030052586123381353
$ cum_strategy_return    <f64> 0.02648234385359971, 0.025969230970583457, 0.027391972643818097, 0.026878405060091426, 0.026878405060091426
$ cum_benchmark_return   <f64> 0.026995713357207185, 0.021596585397285928, 0.023524897924116273, 0.02506747438797885, 0.028152700873305347
```

### Numeric Column Statistics
```
fold: min=0, max=13, mean=6.24, median=6.0
target_log_return_next: min=-0.1386444483967515, max=0.1047184545507811, mean=-0.00, median=-0.0004552801920918448
predicted_return: min=-0.042631901773694206, max=0.03919041496771588, mean=-0.00, median=-0.001505576329211728
n_train: min=626, max=795, mean=707.12, median=704.0
trade_threshold: min=0.003, max=0.003, mean=0.00, median=0.003
position: min=0.0, max=1.0, mean=0.27, median=0.0
turnover: min=0.0, max=1.0, mean=0.34, median=0.0
transaction_cost: min=0.0, max=0.0005, mean=0.00, median=0.0
strategy_log_return: min=-0.1391444483967515, max=0.1047184545507811, mean=-0.00, median=0.0
benchmark_log_return: min=-0.1386444483967515, max=0.1047184545507811, mean=-0.00, median=-0.0004552801920918448
cum_strategy_return: min=-0.3178399020577737, max=0.23882738294848926, mean=-0.01, median=0.007753249615289448
cum_benchmark_return: min=-0.34284609660702303, max=0.028152700873305347, mean=-0.23, median=-0.27111456243377985
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
**Size:** 359596 bytes | **Type:** Csv | **Shape:** 2,800 rows × 13 columns

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
Rows: 2800
Columns: 13
$ week                   <str> '2023-01-06', '2023-01-13', '2023-01-20', '2023-01-27', '2023-02-03'
$ fold                   <i64> 0, 0, 0, 0, 0
$ experiment             <str> 'return_regression', 'return_regression', 'return_regression', 'return_regression', 'return_regression'
$ feature_set            <str> 'price_ai', 'price_ai', 'price_ai', 'price_ai', 'price_ai'
$ model                  <str> 'price_only_ridge', 'price_only_ridge', 'price_only_ridge', 'price_only_ridge', 'price_only_ridge'
$ y_true_return          <f64> 0.026637756991465977, -0.005271073667588055, 0.0018857687565256853, 0.0015059870145548437, 0.0030052586123381353
$ y_pred_return          <f64> 0.0034024391760000706, -0.0022157332551042993, -0.000777280100868632, -0.00018789958747508426, -0.001984342289117705
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
y_true_return: min=-0.1386444483967515, max=0.1047184545507811, mean=-0.00, median=-0.0004552801920918448
y_pred_return: min=-0.030128189347007603, max=0.03919041496771588, mean=-0.00, median=-0.0014918937072026432
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

---

## volatility_predictions.csv
**Path:** `reports/volatility_predictions.csv`
**Size:** 470364 bytes | **Type:** Csv | **Shape:** 2,800 rows × 14 columns

### Columns
```
week                                     String         
fold                                     Int64          
feature_set                              String         
estimator                                String         
model                                    String         
target_log_return_next                   Float64        
target_abs_return_next                   Float64        
predicted_abs_return_next                Float64        
high_vol_threshold                       Float64        
y_true_high_vol                          Int64          
y_pred_high_vol                          Int64          
train_start                              String         
train_end                                String         
n_train                                  Int64          
```

### Sample Values (first 5 rows)
```
Rows: 2800
Columns: 14
$ week                      <str> '2023-01-06', '2023-01-13', '2023-01-20', '2023-01-27', '2023-02-03'
$ fold                      <i64> 0, 0, 0, 0, 0
$ feature_set               <str> 'price_ai_gdelt', 'price_ai_gdelt', 'price_ai_gdelt', 'price_ai_gdelt', 'price_ai_gdelt'
$ estimator                 <str> 'hgb', 'hgb', 'hgb', 'hgb', 'hgb'
$ model                     <str> 'price_ai_gdelt_hgb', 'price_ai_gdelt_hgb', 'price_ai_gdelt_hgb', 'price_ai_gdelt_hgb', 'price_ai_gdelt_hgb'
$ target_log_return_next    <f64> 0.0024110656570526245, -0.007558729831937505, 0.04091419471991031, -0.00465628239000182, -0.0015193966698214822
$ target_abs_return_next    <f64> 0.0024110656570526245, 0.007558729831937505, 0.04091419471991031, 0.00465628239000182, 0.0015193966698214822
$ predicted_abs_return_next <f64> 0.01044648495481766, 0.010719116925302863, 0.01168537911713701, 0.011482403115315832, 0.012592687476475371
$ high_vol_threshold        <f64> 0.0182262198375418, 0.0182262198375418, 0.0182262198375418, 0.0182262198375418, 0.0182262198375418
$ y_true_high_vol           <i64> 0, 0, 1, 0, 0
$ y_pred_high_vol           <i64> 0, 0, 0, 0, 0
$ train_start               <str> '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07', '2011-01-07'
$ train_end                 <str> '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30', '2022-12-30'
$ n_train                   <i64> 626, 626, 626, 626, 626
```

### Numeric Column Statistics
```
fold: min=0, max=13, mean=6.24, median=6.0
target_log_return_next: min=-0.04705158725929204, max=0.04091419471991031, mean=0.00, median=0.0004587613480366848
target_abs_return_next: min=0.0002309886158760044, max=0.04705158725929204, mean=0.01, median=0.011295155480222974
predicted_abs_return_next: min=0.003783356297469759, max=0.02743627110554362, mean=0.01, median=0.013828642894690952
high_vol_threshold: min=0.01805487745517942, max=0.018246381393258734, mean=0.02, median=0.018133283173099635
y_true_high_vol: min=0, max=1, mean=0.29, median=0.0
y_pred_high_vol: min=0, max=1, mean=0.07, median=0.0
n_train: min=626, max=795, mean=707.12, median=704.0
```