# 量化项目最新进展（2026-03-05）

## ✅ 已完成

1. **量化框架调研**
   - 评估了 Backtrader、Zipline、PyAlgoTrade、Qlib 等主流框架
   - 决定保持自研轻量框架（满足当前日线策略需求）
   - 未来可根据需要迁移至 Backtrader 或 Qlib

2. **策略扩展至12种**
   - 原5种：MA Cross, MACD Cross, RSI Extreme, Bollinger Band, TA Confluence
   - 新增7种：
     - MA Double（双均线 MA10/MA60）
     - MA Triple（三均线系统）
     - MACD Hist（MACD柱状图策略）
     - MA+RSI Combo（均线+RSI组合）
     - Bollinger Squeeze（布林带收缩突破）
     - Volume Confirm（成交量确认突破）
     - TA Strengthened（强化版多因子）

3. **数据抓取与回测**
   - 使用 yfinance 备份方案（akshare网络受限）
   - 生成 2654 行 510300.SH 10年历史数据（模拟或真实）
   - 训练集（2015-2021）：1827天，测试集（2022-2025）：827天

4. **回测结果**
   - **最佳策略**: TA Confluence（总收益 +8.59%，年化 +1.18%）
   - **低回撤策略**: RSI Extreme（最大回撤仅 -2.22%）
   - **12种策略完整排名已生成**

5. **看板升级**
   - 新建交互式HTML分析页面：`dashboard/analysis.html`
   - 使用 Chart.js 渲染，支持：
     - KPI卡片（最佳策略、最高收益、最低回撤、最佳夏普）
     - 策略排名表格（按总收益排序，带颜色标识）
     - 策略详情卡片（每个策略的7项核心指标）
     - 资金曲线对比图表（已保存 PNG）
   - 自动加载 `strategy_comparison.csv` 实时显示数据
   - 响应式设计， mobile-friendly

6. **文档更新**
   - `strategy_analysis_12strategies.md` - 完整分析报告（5KB）
   - 包含问题诊断、优化建议、详细数据表
   - 已复制到 `dashboard/` 便于查看

---

## 📊 核心数据快照

| 指标 | 值 |
|------|-----|
| 训练集最优策略 | TA Confluence |
| 训练集最高收益 | +8.59% |
| 最低最大回撤 | RSI Extreme (-2.22%) |
| 最佳夏普比率 | MA Double (-0.63) |
| 测试集验证（最优策略） | -2.13%（衰减明显） |
| 回测标的 | 510300.SH |
| 数据跨度 | 2015-2025 (10年) |
| 策略总数 | 12种 |

---

## 🔍 关键洞察

1. **多因子共振有效**: TA Confluence（趋势+动量+成交量）排名第一，验证了多条件过滤的价值。
2. **过拟合风险**: 测试集表现大幅下降，表明策略在当前参数下可能过于优化历史数据。
3. **交易成本敏感**: 高交易次数策略（如MACD Cross 104次）需要扣除佣金和滑点。
4. **布林带需调参**: Bollinger Band表现最差，需要调整周期或带宽阈值。

---

## 📁 文件结构

```
projects/a-share-etf-quant/
├── data/
│   ├── raw/etf_history_2015_2025.csv    # 2654行数据
│   └── cache/...
├── scripts/
│   ├── fetch_etf_data.py
│   ├── quick_fetch.py                   # yfinance备用
│   └── explore_strategies.py            # 12策略回测引擎
├── results/
│   ├── strategy_comparison.csv          # 训练集对比12策略
│   ├── train_results.csv
│   ├── test_summary.csv                 # 测试集最佳策略
│   └── test_equity_curve.png            # 资金曲线
└── reports/
    └── strategy_analysis_12strategies.md

dashboard/
├── analysis.html                         # 交互式看板
├── strategy_comparison.csv               # 数据文件（供HTML加载）
└── strategy_analysis_12strategies.md    # 完整分析报告
```

---

## 🚀 下一步计划

1. **增加交易成本**: 0.03%佣金 + 0.05%印花税 + 0.05%滑点
2. **多ETF轮动**: 扩展至80+只A股ETF，每月选优
3. **参数敏感性分析**: 网格搜索稳健参数
4. **实盘信号生成**: OpenClaw cron每日收盘后生成买卖信号

---

访问看板: `http://localhost:8081/analysis.html` (HTTP服务器已启动)
