# FINM 33200 Group 8: CORN ETF Trading Signal Pipeline

本项目实现一个模块化 weekly pipeline，用来预测 `CORN` ETF 下一周是否出现有交易意义的 move，并比较不同信息集的增量价值。

当前主线是固定 2% 三分类：

```text
Y =  1 if next_week_return >= +2%
Y =  0 if -2% < next_week_return < +2%
Y = -1 if next_week_return <= -2%
```

当前 baseline 信息集：

- `price_only`：历史价格特征
- `price_calendar`：历史价格 + 玉米农业季节特征

天气、文本、AI 特征由队友处理成 weekly tables 后接入；接口见 `pipeline_contract.md`。`src/corn_forecast/data/usda.py` 和 `src/corn_forecast/data/weather.py` 只是 optional adapter / demo reference，不是当前主线分工要求。

## Quick Start

```bash
uv sync --extra dev
uv run python run_classification_baseline.py
```

运行后会生成：

- `reports/price_target_tests.json`
- `reports/price_target_predictions.csv`

这些数据和报告输出默认被 `.gitignore` 忽略，避免把大文件或本地结果提交进仓库。

## CLI

一键 baseline：

```bash
uv run python run_classification_baseline.py
```

等队友放入 weekly weather/text/AI tables 后，先构建 feature panel：

```bash
uv run python -m corn_forecast.cli fetch-prices --demo
uv run python -m corn_forecast.cli build-features
```

当前主分类 pipeline：

```bash
uv run python -m corn_forecast.cli classify-move \
  --fixed-return-threshold 0.02 \
  --feature-sets price_only,price_calendar
```

该命令比较两组历史可得特征：

- `price_only`：价格滞后、波动率、momentum、volume change
- `price_calendar`：`price_only` + month、week-of-year sin/cos、种植季、生长期、收获季、冬季库存期

- 连续目标：预测 `target_log_return_next`
- 三分类目标：`return <= -2%`、`-2% < return < 2%`、`return >= 2%`

输出：

- `reports/price_target_tests.json`
- `reports/price_target_predictions.csv`

当前主实验使用固定 2% 三分类：

```bash
uv run python -m corn_forecast.cli test-price-targets --fixed-return-threshold 0.02
```

也可以直接运行一键脚本：

```bash
uv run python run_classification_baseline.py
```

选择 volatility-adjusted 三分类阈值的旧实验仍可运行，但不是当前主线：

```bash
uv run python -m corn_forecast.cli select-threshold --threshold-grid 1.0
```

输出：

- `reports/threshold_selection.json`
- `reports/threshold_selection_predictions.csv`

当前阶段固定使用 `2%`，并且只比较 `price_only` 和 `price_calendar` 两组特征。
当前主验证方式使用 expanding window；最近 5 年 rolling window 作为 robustness check：

```bash
uv run python -m corn_forecast.cli select-threshold --threshold-grid 1.0 --validation-scheme expanding
uv run python -m corn_forecast.cli select-threshold --threshold-grid 1.0 --validation-scheme rolling --train-window-weeks 260
```

完整研究步骤见 `step_by_step.md`。
模块化数据接口和两条预测 pipeline 见 `pipeline_contract.md`。

辅助 expected-return pipeline：

```bash
uv run python -m corn_forecast.cli return-strategy --transaction-cost-bps 5 --buffer-bps 25
```

该命令预测下一周 log return，只有当预测收益超过交易成本加安全垫时才持有 CORN。默认交易门槛为 `5 bps + 25 bps = 30 bps`。这是辅助实验，不是当前主分类目标。

输出：

- `reports/expected_return_metrics.json`
- `reports/expected_return_predictions.csv`

常用参数：

- `--symbol CORN`：Yahoo Finance 标的，默认 `CORN`
- `--start 2011-01-01`：数据开始日期
- `--end YYYY-MM-DD`：数据结束日期，默认到当前日期
- `--split-date 2022-12-31`：训练集最后一周，之后为测试集
- `--test-window-weeks 13`：每个 walk-forward 测试窗口长度
- `--retrain-step-weeks 13`：每隔多少周重新扩展训练集并训练
- `--long-threshold 0.55`：旧概率策略使用的 long 阈值
- `--transaction-cost-bps 5`：每次仓位变化的单边交易成本
- `--buffer-bps 25`：预测收益必须额外超过的安全垫
- `--root PATH`：指定输出目录，测试或临时运行时很有用
- `--demo`：使用确定性离线样本，不访问外部 API

`config/research.example.toml` 是带注释的研究配置说明，记录默认 target、walk-forward、模型和策略假设。

## Data Sources

价格数据：

- Yahoo Finance through `yfinance`

天气数据接口：

- 队友交付 `data/interim/weather_weekly.parquet` 或 `.csv`
- 必须包含 `week`
- 天气列统一命名为 `weather_*`

`src/corn_forecast/data/weather.py` 只保留 optional adapter 和 request-shape reference。

文本/AI 数据接口：

- 队友交付 `data/interim/text_weekly.parquet`、`data/interim/ai_weekly.parquet` 或同名 `.csv`
- 必须包含 `week`
- 文本数值列命名为 `text_*`
- AI 结构化分数命名为 `ai_*`
- 可选自由文本列为 `report_text`

具体接口见 `pipeline_contract.md`。

## Modeling Design

主预测目标：

- fixed 2% three-class next-week return label

价格特征：

- 1/2/4/12 周滞后收益率
- 4/12 周 rolling volatility
- 4/12 周 momentum
- 4 周 volume change

模型：

- Classification baseline: `LogisticRegression(class_weight="balanced")`
- Return auxiliary models: `Ridge` and `HistGradientBoostingRegressor`
- `report_text` 如存在，会在 pipeline 内用 TF-IDF，只在训练集拟合，避免文本泄漏。

行业化验证与交易层：

- 使用 expanding walk-forward，而不是随机切分。
- 默认从 `2023-01-01` 后开始 out-of-sample，每 13 周测试一次并重新训练。
- 分类模型输出 down / flat / up。
- 简单策略解释：预测 up 时 long，否则 flat。
- 回测扣除 `transaction_cost_bps`，并输出累计收益、Sharpe、最大回撤和 turnover。

评估：

- walk-forward out-of-sample metrics
- classification: accuracy, balanced accuracy, macro F1, confusion matrix counts
- strategy: total return, annualized return, annualized volatility, Sharpe, max drawdown

## Tests

```bash
uv run pytest
```

测试覆盖：

- target shift 是否只把下一周收益作为标签
- optional USDA adapter 和周频文本对齐
- optional ERA5/CFSv2/GEFS adapter URL/request shape
- price/weather/text feature join
- walk-forward split 和交易成本逻辑
- CLI smoke test
