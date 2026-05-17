# FINM_33200_Group_8

## 任务概览

本项目目标是预测 CORN ETF 的未来表现，并比较不同数据源对预测效果的提升。

## 1. 数据源

### 1.1 历史价格数据

数据来源：

- Yahoo Finance API

待确定：

- 使用日度数据还是周度数据
- 使用多长时间区间的数据

### 1.2 天气数据

可能的数据来源：

- NOAA API
- ERA5 reanalysis: https://cds.climate.copernicus.eu/datasets/derived-era5-single-levels-daily-statistics?tab=download

### 1.3 文本数据

可能的数据来源：

- USDA Crop Progress Report: https://esmis.nal.usda.gov/publication/crop-progress
- AgWeb corn price 页面: https://www.agweb.com/markets/futures/corn-price
- WRDS
- WSJ

## 2. 预测目标

主要预测对象：

- CORN ETF

待确定的预测目标包括：

- 预测价格
- 预测回报
- 预测是否出现大幅上涨

## 3. 预测方案

预测频率：

- 提前一周预测

比较以下三个方案：

### 方案 A：历史价格 Baseline

只使用历史价格数据进行预测。

### 方案 B：历史价格 + 天气数据

在历史价格数据基础上加入天气数据。

### 方案 C：历史价格 + 天气数据 + 文本数据

在历史价格和天气数据基础上加入文本数据，例如新闻、报告或表格信息。

## 4. 评估

需要比较不同方案的预测效果，判断加入天气数据和文本数据是否能提升模型表现。

## 5. 未来改进

未来可以进一步完善：

- 数据频率选择
- 数据时间跨度
- 天气变量选择
- 文本数据来源
- 预测目标定义
- 模型评估方式
