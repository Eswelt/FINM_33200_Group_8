# FINM 33200 Group 8: CORN ETF Direction Forecast MVP

本项目实现一个可跑通的初版 pipeline，用来预测 `CORN` ETF 下一周 log return 是否为正，并比较三组信息集：

- 方案 A：历史价格
- 方案 B：历史价格 + 玉米带天气
- 方案 C：历史价格 + 玉米带天气 + USDA 文本

初版优先保证端到端可复现。天气模块提供 ERA5/CFSv2/GEFS 的 adapter 和缓存入口，但默认 demo 不下载多年 GRIB 数据。

## Quick Start

```bash
uv sync --extra dev
uv run python -m corn_forecast.cli all --demo
```

运行后会生成：

- `data/raw/prices_CORN.csv`
- `data/raw/usda_releases.csv`
- `data/interim/weather_weekly.parquet`
- `data/processed/feature_panel.parquet`
- `reports/metrics.json`
- `reports/predictions.csv`
- `reports/model_report.md`
- `reports/figures/predicted_probabilities.png`
- `reports/figures/roc_curves.png`
- `reports/figures/cumulative_returns.png`

这些数据和报告输出默认被 `.gitignore` 忽略，避免把大文件或本地结果提交进仓库。

## CLI

一键 demo：

```bash
uv run python -m corn_forecast.cli all --demo
```

分步运行：

```bash
uv run python -m corn_forecast.cli fetch-prices --demo
uv run python -m corn_forecast.cli fetch-usda --demo
uv run python -m corn_forecast.cli fetch-weather --demo
uv run python -m corn_forecast.cli build-features
uv run python -m corn_forecast.cli train-evaluate
uv run python -m corn_forecast.cli make-report
```

只用历史价格测试预测目标：

```bash
uv run python -m corn_forecast.cli test-price-targets --demo
```

该命令比较两组历史可得特征：

- `price_only`：价格滞后、波动率、momentum、volume change
- `price_calendar`：`price_only` + month、week-of-year sin/cos、种植季、生长期、收获季、冬季库存期

- 连续目标：预测 `target_log_return_next`
- 三分类目标：`return <= -5%`、`-5% < return < 5%`、`return >= 5%`

输出：

- `reports/price_target_tests.json`
- `reports/price_target_predictions.csv`

常用参数：

- `--symbol CORN`：Yahoo Finance 标的，默认 `CORN`
- `--start 2011-01-01`：数据开始日期
- `--end YYYY-MM-DD`：数据结束日期，默认到当前日期
- `--split-date 2022-12-31`：训练集最后一周，之后为测试集
- `--test-window-weeks 13`：每个 walk-forward 测试窗口长度
- `--retrain-step-weeks 13`：每隔多少周重新扩展训练集并训练
- `--long-threshold 0.55`：预测上涨概率达到该阈值时持有 CORN
- `--transaction-cost-bps 5`：每次仓位变化的单边交易成本
- `--root PATH`：指定输出目录，测试或临时运行时很有用
- `--demo`：使用确定性离线样本，不访问外部 API

`config/research.example.toml` 是带注释的研究配置说明，记录默认 target、walk-forward、模型和策略假设。

## Data Sources

价格数据：

- Yahoo Finance through `yfinance`

天气数据：

- ERA5 daily statistics: `derived-era5-single-levels-daily-statistics`
- NOAA CFSv2 operational 9-month forecast
- NOAA GEFSv12 retrospective S3 reforecast
- 玉米带 bbox 固定为 `[49, -104, 37, -80]`

真实天气数据的完整 GRIB 下载和聚合通常较重。当前 MVP 的 `fetch-weather` 在非 demo 且没有缓存时，会写出 `data/interim/weather_request_catalog.csv`，说明 ERA5/CFSv2/GEFS 的请求形状；之后可把处理好的周频天气表放到 `data/interim/weather_weekly.parquet`。

文本数据：

- USDA Crop Progress
- USDA Weekly Weather and Crop Bulletin

文本特征按报告发布日期对齐到周五周频。TF-IDF 在模型 pipeline 内只用训练集拟合，避免测试期文本信息泄漏。

## Modeling Design

预测目标：

- `target_log_return_next = log(close_t+1 / close_t)`
- `target_up_next = 1[target_log_return_next > 0]`

价格特征：

- 1/2/4/12 周滞后收益率
- 4/12 周 rolling volatility
- 4/12 周 momentum
- 4 周 volume change

天气特征：

- weekly mean temperature
- precipitation
- growing degree days
- temperature/precipitation anomaly
- week-1/week-2 forecast-style demo features

文本特征：

- USDA report text
- small TF-IDF representation inside the model pipeline
- keyword counts for drought, rain, heat, planting, harvest, yield, export, ethanol

模型：

- Baseline: `StandardScaler` + `LogisticRegression(class_weight="balanced")`
- Main model: `HistGradientBoostingClassifier`
- 文本方案额外使用 `TfidfVectorizer(max_features=30)`，并与数值特征一起进入模型

行业化验证与交易层：

- 使用 expanding walk-forward，而不是随机切分。
- 默认从 `2023-01-01` 后开始 out-of-sample，每 13 周测试一次并重新训练。
- 每个模型输出 `P(next_week_return > 0)`。
- 策略默认 long/flat：`P(up) >= 0.55` 时持有，否则空仓。
- 回测扣除 `transaction_cost_bps`，并输出累计收益、Sharpe、最大回撤和 turnover。

评估：

- walk-forward out-of-sample metrics
- classification: accuracy, balanced accuracy, F1, ROC-AUC, log loss, confusion matrix counts
- strategy: total return, annualized return, annualized volatility, Sharpe, max drawdown

## Tests

```bash
uv run pytest
```

测试覆盖：

- target shift 是否只把下一周收益作为标签
- USDA listing parser 和周频文本对齐
- ERA5/CFSv2/GEFS adapter URL/request shape
- price/weather/text feature join
- walk-forward split 和交易成本逻辑
- `all --demo` smoke test

## Team Workflow

建议协作方式：

1. 不直接改 `main`，在 feature branch 上开发。
2. 小步提交：scaffold、data ingestion、features/models、tests/docs。
3. 不提交本地下载数据或报告输出。
4. PR 中附上 `uv run pytest` 和 `uv run python -m corn_forecast.cli all --demo` 的结果。

可分工模块：

- Data: Yahoo/USDA/weather adapter 和缓存表
- Features: 周频对齐、target、weather/text feature engineering
- Modeling: A/B/C 方案、指标和图表
- Reporting: README、报告文字、结果解释和 presentation 图表
