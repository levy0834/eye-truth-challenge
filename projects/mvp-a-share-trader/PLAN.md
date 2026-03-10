# 🎯 Clawstreet 模拟盘 MVP 实施计划

**目标**: 7天内完成 OpenClaw 自动交易系统（A股模拟盘）
**标的**: 沪深300ETF (510300.SH)
**平台**: Clawstreet + OpenClaw
**数据源**: akshare + 东方财富API

---

## 📅 每日任务清单

### Day 1 (今天): 环境准备 + 数据管道

- [x] 已安装 Proactive Agent
- [ ] 配置 akshare 数据抓取脚本
- [ ] 测试获取 510300.SH 实时行情
- [ ] 实现数据质量检查（价格、PE、成交量）

### Day 2: 策略逻辑开发

- [ ] 定义基础策略（如：均线交叉、突破均线）
- [ ] 实现技术指标计算（MA5, MA20, 布林带等）
- [ ] 编写买入/卖出信号生成器
- [ ] 回测历史数据（3个月）

### Day 3: 模拟交易接口对接

- [ ] 注册 Clawstreet 账户（clawstreet.io）
- [ ] 获取模拟交易 API Key
- [ ] 封装交易接口（下单、撤单、查询持仓）
- [ ] 实现资金管理模块

### Day 4: OpenClaw 技能开发

- [ ] 创建 `a-share-trader` 技能
- [ ] 集成数据抓取 + 策略计算 + 交易执行
- [ ] 配置文件：`config.yaml` 包含 API Key、股票代码、仓位限制
- [ ] 单元测试

### Day 5: Cron 自动化

- [ ] 设置盘前监测（8:50）：获取前日收盘价
- [ ] 设置盘中监测（9:30-11:30, 13:00-15:00）：每5分钟检查一次信号
- [ ] 设置盘后报告（15:10）：生成当日交易日志
- [ ] 添加异常报警（飞书消息）

### Day 6: 模拟盘上线测试

- [ ] 小仓位试运行（10%资金）
- [ ] 监控执行日志和错误
- [ ] 调整策略参数
- [ ] 验证交易指令正确性

### Day 7: 效果评估与迭代

- [ ] 生成完整绩效报告（收益率、最大回撤、胜率）
- [ ] 分析失败交易原因
- [ ] 优化策略参数或切换策略
- [ ] 制定下一周计划

---

## 🔧 技术实现细节

### 数据源配置 (akshare)

```python
import akshare as ak

# 获取ETF实时行情
etf_df = ak.fund_etf_spot_em()
# 筛选 510300
target = etf_df[etf_df['代码'] == '510300']

# 获取历史数据
hist = ak.fund_etf_hist_em("510300", period="daily")
```

### 策略示例（移动平均线）

```python
def ma_cross_strategy(df):
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    # 金叉：5日上穿20日
    if df['ma5'].iloc[-1] > df['ma20'].iloc[-1] and df['ma5'].iloc[-2] <= df['ma20'].iloc[-2]:
        return "BUY"
    # 死叉：5日下穿20日
    elif df['ma5'].iloc[-1] < df['ma20'].iloc[-1] and df['ma5'].iloc[-2] >= df['ma20'].iloc[-2]:
        return "SELL"
    return "HOLD"
```

### 交易接口（需Clawstreet API文档）

```python
class ClawstreetTrader:
    def __init__(self, api_key, symbol="510300.SH"):
        self.api_key = api_key
        self.symbol = symbol
        self.base_url = "https://api.clawstreet.io/v1"

    def place_order(self, side, quantity, order_type="market"):
        # POST /orders
        pass

    def get_position(self):
        # GET /positions
        pass

    def get_account(self):
        # GET /account
        pass
```

### OpenClaw Skill 结构

```
a-share-trader/
├── manifest.json
├── SKILL.md
├── scripts/
│   ├── data_fetcher.py      # 数据抓取
│   ├── strategy.py          # 策略逻辑
│   ├── trader.py            # 交易接口
│   ├── reporter.py          # 日报生成
│   └── main.py              # 主入口
├── config.yaml              # 配置（API Key、股票代码等）
└── tests/
    └── test_strategy.py
```

---

## ⚠️ 风险控制

- **仓位限制**: 单次交易不超过总资金 10%
- **止损**: 跌 3% 自动止损
- **时间限制**: 只在交易日 9:30-15:00 交易
- **人工干预**: 每日复盘卡片发送给用户，重大决策需确认

---

## 📊 成功指标

- ✅ 7天内无重大错误（API调用正常、数据准确）
- ✅ 至少完成 3 次买入和 3 次卖出交易
- ✅ 每日发送交易日志到飞书
- ✅ 周收益率 > 0.5% (扣掉手续费后)

---

## 🛠️ 立即开始

我现在先创建 `a-share-trader` skill 框架，然后实现数据抓取模块。继续吗？
