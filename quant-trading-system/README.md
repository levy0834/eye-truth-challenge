# 量化交易系统

一个基于 Python 的多市场量化交易研究框架，支持 A股ETF、美股ETF 和 加密货币 的历史数据获取、策略回测与绩效评估。

## 特性

- ✅ **多数据源支持**：AKShare（A股）、yfinance（美股）、CCXT（加密货币）
- ✅ **自动降级机制**：主源失败自动切换备用源
- ✅ **T+1交易模拟**：符合A股市场规则
- ✅ **5种内置策略**：MA均线、MACD、RSI、布林带、TAV共振
- ✅ **完整回测引擎**：支持止损止盈、滑点模拟、交易成本
- ✅ **丰富评估指标**：收益、回撤、夏普比率、胜率等
- ✅ **自动化任务**：Cron调度支持（数据更新、回测、报告）

## 快速开始

### 1. 安装依赖

```bash
cd quant-trading-system
pip3 install -r requirements.txt
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env 填入必要的API Key（可选）
```

### 3. 抓取数据

```bash
# 抓取所有配置的标的（默认：510300.SH, SPY, BTC/USDT）
python3 -m src.main fetch

# 或使用脚本
./scripts/fetch_data.sh
```

数据将保存到 `data/raw/` 目录。

### 4. 运行回测

```bash
# 回测所有标的+所有策略
python3 -m src.main backtest

# 指定标的和策略
python3 -m src.main backtest --symbol 510300.SH --strategy ma_cross

# 或使用脚本
./scripts/run_backtest.sh
```

### 5. 查看结果

回测结果输出到 `results/` 目录：
- `metrics.json` - 绩效指标
- `trades.csv` - 逐笔交易记录
- `equity_curve.png` - 资金曲线图
- `comparison.csv` - 多策略对比

## 项目结构

```
quant-trading-system/
├── config/          配置文件（标的列表、参数）
├── data/           数据存储（原始/处理/缓存）
├── src/            源代码
│   ├── data/       数据获取与清洗
│   ├── strategies/ 交易策略
│   ├── backtest/   回测引擎
│   └── utils/      工具函数
├── scripts/        便捷脚本
├── tests/          单元测试
├── notebooks/      Jupyter notebooks
├── docs/           文档
└── results/        回测输出（自动生成）
```

## 支持的标的

### A股ETF（通过AKShare/yfinance）
- 510300.SH - 沪深300ETF
- 其他ETF代码可配置

### 美股ETF（通过yfinance）
- SPY - 标普500
- QQQ - 纳斯达克100
- DIA - 道琼斯工业平均

### 加密货币（通过CCXT）
- BTC/USDT - 比特币
- ETH/USDT - 以太坊
- 其他交易对可配置

## 策略说明

| 策略 | 简介 | 适合市场 |
|-----|------|---------|
| MA Cross | 均线金叉/死叉 | 趋势市场 |
| MACD Cross | MACD交叉 | 动量市场 |
| RSI Extreme | 超买超卖 | 震荡市场 |
| Bollinger Band | 布林带突破 | 高波动市场 |
| TAV Confluence | 多因子共振 | 综合信号 |

## 风控参数

可在 `config/settings.yaml` 调整：
- `position_size` - 单次仓位（默认 10%）
- `stop_loss` - 止损线（默认 -3%）
- `take_profit` - 止盈线（默认 +8%）
- `max_drawdown` - 最大回撤停损（默认 -20%）

## 自动化

使用 OpenClaw cron 自动运行：
```json
{
  "jobs": [
    {
      "name": "daily_data_update",
      "schedule": "0 8 * * *",
      "command": "cd ~/.openclaw/workspace/quant-trading-system && python3 -m src.main fetch"
    },
    {
      "name": "daily_backtest",
      "schedule": "0 14 * * *",
      "command": "cd ~/.openclaw/workspace/quant-trading-system && python3 -m src.main backtest"
    }
  ]
}
```

## 开发

### 添加新策略
```python
# src/strategies/my_strategy.py
from .base import Strategy

class MyStrategy(Strategy):
    def generate_signal(self, row):
        # 返回 'buy', 'sell', 或 'hold'
        return 'hold'
```

### 添加新数据源
```python
# src/data/my_fetcher.py
from .fetchers import DataFetcher

class MyFetcher(DataFetcher):
    def fetch(self, symbol, start, end):
        # 返回 pandas.DataFrame
        pass
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 免责声明

本项目仅供学习和研究使用。交易有风险，决策需谨慎。开发者不对任何交易损失负责。
