# A股/加密货币量化交易系统

**目标**: 基于10年历史数据，探索天级别交易策略，支持多市场（A股ETF、美股ETF、加密货币）
**数据范围**: 2015-2025年（10年）
**核心约束**:
- 免费数据源
- A股 T+1 交易制度（隔日交易）
- 实时性要求不高（日线级别）

---

## 1. 系统架构

```
quant-trading-system/
├── config/
│   ├── __init__.py
│   ├── settings.yaml        # 主配置（标的列表、时间范围、风控参数）
│   └── strategies.yaml      # 策略参数配置
├── data/
│   ├── __init__.py
│   ├── raw/                # 原始数据（按来源分类）
│   │   ├── akshare/        # A股ETF历史数据
│   │   ├── yfinance/       # 美股ETF数据
│   │   └── crypto/         # 加密货币数据
│   ├── processed/          # 处理后的特征数据（Parquet格式）
│   └── cache/              # HTTP请求缓存
├── src/
│   ├── __init__.py
│   ├── data/               # 数据获取模块
│   │   ├── __init__.py
│   │   ├── fetchers.py     # 统一数据获取接口
│   │   ├── akshare_fetcher.py
│   │   ├── yfinance_fetcher.py
│   │   ├── ccxt_fetcher.py # 加密货币（币安、OKX）
│   │   ├── cleaner.py      # 数据清洗
│   │   └── features.py     # 特征工程（技术指标）
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py         # 策略基类
│   │   ├── ma_cross.py     # 均线金叉死叉
│   │   ├── macd_cross.py   # MACD交叉
│   │   ├── rsi_extreme.py  # RSI超买超卖
│   │   ├── bollinger.py    # 布林带突破
│   │   └── confluence.py   # TAV多因子共振
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py       # 回测引擎
│   │   ├── broker.py       # 模拟券商接口
│   │   ├── metrics.py      # 绩效指标计算
│   │   └── visualizer.py   # 可视化（资金曲线、回撤图）
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py       # 日志系统
│   │   ├── timer.py        # 计时器
│   │   └── config_loader.py # 配置加载
│   └── main.py             # 主入口（命令行CLI）
├── tests/
│   ├── __init__.py
│   ├── test_fetchers.py
│   ├── test_strategies.py
│   └── test_backtest.py
├── notebooks/
│   └── exploratory_analysis.ipynb  # 探索性数据分析
├── docs/
│   ├── architecture.md      # 架构设计
│   ├── api.md              # API文档
│   └── deployment.md       # 部署指南
├── scripts/
│   ├── fetch_data.sh       # 一键抓取所有数据
│   ├── run_backtest.sh     # 一键回测
│   ├── deploy_cron.sh      # 部署定时任务
│   └── export_results.sh   # 导出结果到飞书/邮件
├── .env.example            # 环境变量模板
├── .gitignore
├── requirements.txt        # Python依赖
├── README.md               # 项目说明
├── pyproject.toml          # 项目元数据
├── LICENSE
└── CHANGELOG.md
```

---

## 2. 数据源策略（优先级）

### 2.1 A股ETF（首选标的：510300.SH）

**首选方案**: AKShare
- 接口: `ak.fund_etf_hist_em(symbol="510300", period="daily")`
- 数据频率: 日线
- 延迟: 3-10分钟（可接受）
- 稳定性: 差（源站易变，需重试机制）
- 成本: 免费

**备用方案1**: Tushare Pro（需token）
- 注册免费，每日500次调用
- 数据质量更高，稳定性好
- 备用当 AKShare 失效时

**备用方案2**: yfinance（支持A股代码后缀.SH/.SZ）
- `yf.download("510300.SH", ...)`
- 延迟15分钟
- 稳定性较好

### 2.2 美股ETF（标普500 SPY）

**方案**: yfinance
- 接口: `yf.download("SPY", start="2015-01-01")`
- 数据频率: 日线
- 延迟: 15分钟（免费）
- 稳定性: 好

### 2.3 加密货币（BTC/USDT）

**方案**: CCXT 库 + 币安/OKX
- 接口: `ccxt.binance().fetch_ohlcv("BTC/USDT", "1d")`
- 数据频率: 日线/小时线
- 实时性: ✅ 真正实时
- 成本: 免费（有请求频率限制）
- 优势: 7×24交易，无T+1限制

**为什么加加密货币**：
- 数据质量高（交易所API稳定）
- 可以作为对比基准
- 若A股数据源崩了，至少还有币可用

---

## 3. 数据抓取流程

```python
# 伪代码
fetcher = DataFetcher(config)
for market in ['a_share', 'us_etf', 'crypto']:
    for symbol in config['symbols'][market]:
        data = fetcher.fetch(symbol, start_date, end_date)
        if data is not None:
            save_to_disk(data, market, symbol)
        else:
            retry_with_fallback(symbol)
```

**重试策略**：
- 第一层：AKShare → yfinance → 本地缓存
- 第二层：如果全失败，用最近一次缓存数据（即使旧一点）
- 第三层：标记该symbol为"不可用"，跳过

---

## 4. 策略设计（5种）

### 4.1 MA均线交叉
```
买入: MA5 > MA20 且 前一日 MA5 <= MA20 (金叉)
卖出: MA5 < MA20 且 前一日 MA5 >= MA20 (死叉)
持仓周期: 直到反向信号
```

### 4.2 MACD交叉
```
买入: MACD > Signal 且前一日 MACD <= Signal
卖出: MACD < Signal 且前一日 MACD >= Signal
```

### 4.3 RSI超买超卖
```
买入: RSI < 30 (超卖)
卖出: RSI > 70 (超买)
注意: RSI可能长期超买/超卖，需结合趋势过滤
```

### 4.4 布林带突破
```
买入: 收盘价 < 下轨 (超卖反弹)
卖出: 收盘价 > 上轨 (超买回落)
```

### 4.5 TAV多因子共振（综合策略）
```
买入条件（全部满足）:
  1. 趋势: close > MA20 且 MA5 > MA20
  2. 动量: RSI在30-70健康区间 且 MACD金叉
  3. 成交量: 当日成交量 > 1.5倍5日均量

卖出条件:
  趋势破坏（close < MA20）或 达到止盈/止损
```

---

## 5. 回测引擎设计

**核心类**:

```python
class Backtester:
    def __init__(self, data, config):
        self.data = data  # DataFrame with OHLCV
        self.config = config
        self.broker = SimulatedBroker(initial_capital=100000)
        self.strategy = None

    def run(self):
        for timestamp, row in self.data.iterrows():
            signal = self.strategy.generate_signal(row)
            self.broker.execute(signal, row['close'])
            self.record_portfolio_value()

    def evaluate(self):
        return calculate_metrics(self.broker.trades, self.broker.portfolio_history)
```

**关键特性**:
- 支持 T+1 约束（A股）
- 自动计算交易成本（佣金、印花税）
- 风险控制模块（单票仓位、止损止盈）
- 滑点模拟（可选）

---

## 6. 风控规则（必须包含）

| 规则 | 参数 | 说明 |
|-----|------|------|
| 单次仓位 | ≤ 10% 总资金 | 避免过度集中 |
| 最大持仓 | ≤ 50% 总资金 | 最多5只标的 |
| 止损 | -3% （相对于买入价） | 硬止损 |
| 止盈 | +8% （相对于买入价） | 分批止盈 |
| 最大回撤 | -20% 停止策略 | 保护资本 |
| 交易时间 | A股: 9:30-15:00 | 仅在交易时段执行 |

---

## 7. 评估指标

**收益率类**:
- 总收益率
- 年化收益率 (CAGR)
- 超额收益（相对于基准如沪深300）

**风险类**:
- 最大回撤（Max Drawdown）
- 波动率（标准差）
- Value at Risk (VaR)

**效率类**:
- 夏普比率（Sharpe Ratio）
- 索提诺比率（Sortino Ratio）
- 卡玛比率（Calmar Ratio）

**交易类**:
- 胜率（Win Rate）
- 盈亏比（Profit Factor）
- 平均持仓天数

---

## 8. 输出产物

### 8.1 数据文件
```
data/raw/akshare/etf_510300_2015_2025.csv
data/raw/yfinance/etf_SPY_2015_2025.csv
data/processed/features_510300.parquet
```

### 8.2 回测结果
```
results/
├── backtest_510300_ma_cross/
│   ├── trades.csv          # 逐笔交易
│   ├── portfolio_value.csv # 每日资产
│   ├── metrics.json        # 绩效指标
│   └── equity_curve.png    # 资金曲线
├── comparison/
│   └── all_strategies.csv  # 多策略对比
└── best_strategy/
    └── strategy_config.yaml  # 最优策略参数
```

### 8.3 报告
- `reports/daily_briefing.md` - 每日交易简报（发送到飞书）
- `reports/weekly_summary.md` - 周度总结
- `reports/monthly_performance.pdf` - 月度绩效（图表）

---

## 9. 自动化任务（Cron）

| 时间 | 任务 | 说明 |
|-----|------|------|
| 每日 8:50 | 晨间数据检查 | 获取前日数据，检查数据质量 |
| 每日 14:55 | 收盘前信号计算 | 基于当日K线生成次日交易计划 |
| 每日 15:05 | 生成日报 | 发送到飞书（持仓、信号、计划） |
| 次日 9:25 | 开盘前检查 | 确认计划有效性 |
| 次日 9:30-9:35 | 执行交易 | 挂单买入/卖出 |
| 每周日 20:00 | 周度复盘 | 策略参数微调 |

** Saturday 和 Sunday 不交易（A股休市）

---

## 10. 部署与GitHub

### 10.1 项目初始化
```bash
# 创建目录结构
mkdir -p quant-trading-system/{config,data/{raw,processed,cache},src/{data,strategies,backtest,utils},tests,notebooks,docs,scripts}

# 初始化Git
cd quant-trading-system
git init
echo "*.pyc" > .gitignore
echo "__pycache__/" >> .gitignore
echo "data/raw/*.csv" >> .gitignore  # 原始数据太大，不提交
echo "data/processed/*.parquet" >> .gitignore
echo ".env" >> .gitignore
echo "results/" >> .gitignore

git add .
git commit -m "Initial commit: project structure"
```

### 10.2 GitHub Repo
- 名称: `openclaw-quant` 或 `a-share-etf-trader`
- 开源协议: MIT
- README: 包含快速开始指南
- 配置: 提供 `config/settings.example.yaml`

---

## 11. 即时行动计划（今晚）

### Step 1: 创建项目根目录和结构
```bash
mkdir -p ~/.openclaw/workspace/quant-trading-system
cd ~/.openclaw/workspace/quant-trading-system
# 创建上述目录树
```

### Step 2: 编写统一数据抓取脚本 `src/data/fetchers.py`
- 集成 akshare、yfinance、ccxt
- 实现自动重试和fallback链
- 统一输出格式（OHLCV标准DataFrame）

### Step 3: 测试抓取 510300.SH（A股ETF）
- 尝试 akshare 3次 → yfinance 3次 → 报错
- 如果成功，保存到 `data/raw/akshare/`

### Step 4: 测试抓取 BTC/USDT（加密货币）
- 使用 ccxt 连接币安
- 获取最近3个月日线
- 保存到 `data/raw/crypto/`

### Step 5: 运行回测（单策略，单标的）
- 用 SPY 或 510300 数据
- 跑通 MA Cross 策略
- 输出基本指标（总收益、最大回撤）

---

## 12. 预期问题与应对

| 问题 | 解决方案 |
|-----|---------|
| akshare 安装失败 | 直接用 yfinance 抓 510300.SH（后缀.SH） |
| yfinance 限流 | 设置 sleeps 和 backoff，单日最多100次 |
| 币安API限频 | 使用 public endpoint（无需key），rate limit 1200/分钟 |
| 数据缺失（停牌） | forward fill + 剔除零成交量日 |
| 回测速度慢 | 使用Parquet格式 + 向量化计算 |

---

**现在开始实现**：我将按上述结构创建项目，并优先实现数据抓取的多源fallback机制。
