# A股ETF量化策略研究

**目标**: 基于10年历史数据，探索天级别交易策略，验证有效性

**数据范围**: 2015-2025年（10年）
**标的**: 全体A股ETF（当前约80只，历史可能更多）
**策略类型**: 技术指标（MA, MACD, RSI, 布林带等）
**验证方法**: 训练集(2015-2021) + 测试集(2022-2025)

---

## 1. 数据抓取计划

### ETF列表获取
- 使用 AKShare: `ak.fund_etf_spot_em()` 获取当前所有ETF
- 包含：代码、名称、成立日期、规模等
- 筛选成立满5年的ETF（至少2019年以前成立）

### 历史数据抓取
- 日线数据：开盘、最高、最低、收盘、成交量、成交额
- 复权处理：前复权（qfq）
- 时间范围：2015-01-01 至 2025-03-04（最新）
- 存储格式：CSV（每个ETF一个文件）或 SQLite

### 预期数据量
- ETF数量：约 80 只
- 每只交易日：约 1200 天（10年）
- 总数据量：约 10万条记录

---

## 2. 策略探索方向

### 2.1 单指标策略
- **MA 均线系统**: MA5/MA20 金叉死叉
- **MACD**: 金叉死叉、背离
- **RSI**: 超买超卖（>70/<30）
- **布林带**: 突破上轨卖出，跌破下轨买入

### 2.2 多因子组合
- 趋势 + 动量 + 成交量（TAV框架）
- 多ETF轮动（选择最强N只）

### 2.3 风险控制
- 单次仓位 ≤ 10%
- 止损：-3%
- 止盈：+8%
- 最大回撤 > 20% 停止策略

---

## 3. 回测框架

```python
class Backtester:
    def __init__(self, data, initial_capital=100000):
        self.data = data  # OHLCV DataFrame
        self.capital = initial_capital
        self.position = 0  # 持有股数
        self.trades = []  # 交易记录

    def run_strategy(self, strategy):
        # 逐日计算信号
        for date, row in self.data.iterrows():
            signal = strategy.generate_signal(row)
            self.execute(signal, row)

    def execute(self, signal, price):
        # 执行交易
        pass

    def evaluate(self):
        # 计算收益率、夏普比率、最大回撤
        pass
```

---

## 4. 评估指标

- **总收益率**: (final - initial) / initial
- **年化收益率**: (1+total)^(252/N) - 1
- **最大回撤**: 最大峰值到谷值的跌幅
- **夏普比率**: (mean(returns) - risk_free) / std(returns)
- **胜率**: 盈利交易次数 / 总交易次数
- **盈亏比**: 平均盈利 / 平均亏损

---

## 5. 机器学习方法（可选）

如果规则策略效果一般，尝试：
- 特征工程：技术指标 + 基本面因子
- 模型：Random Forest, XGBoost, LSTM
- 标签：未来N日收益率（分类：涨/跌）

---

## 6. 时间安排

- Day 1-2: 数据抓取（约80只ETF × 10年）
- Day 3-4: 策略开发与回测框架
- Day 5-6: 训练集参数优化
- Day 7: 测试集验证 + 报告

---

## 7. 预期产出

- `data/raw/` 填充10年数据
- `results/` 包含：
  - 策略回测曲线（资金曲线）
  - 性能对比表（不同策略）
  - 最佳策略详细报告
- `strategies/` 保存最优策略代码（可直接用于实盘）

---

**开始**: 立即编写数据抓取脚本
