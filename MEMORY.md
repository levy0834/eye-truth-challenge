# MEMORY.md - 主记忆库

>  curated long-term memories for OpenClaw agent

## ⚠️ 核心工作原则

### 工作目录隔离
- **写代码/任务时，务必在独立的工作目录中进行**，不得在 workspace 根目录随意创建文件
- 根目录 (`/Users/levy/.openclaw/workspace/`) 应保持整洁，避免重要文件被覆盖或污染
- 重要配置文件（`MEMORY.md`, `SOUL.md`, `USER.md`, `HEARTBEAT.md`）必须受到保护，不应被任务过程影响
- 建议为每个大任务创建子目录，如 `projects/`, `temp/`, `scratch/`，并在完成后清理

## 系统配置

### 飞书集成
- 应用凭证通过环境变量或OpenClaw配置管理（不直接存储在文件中）
- 早报任务使用 `tenant_access_token` 创建文档（需网络可达）
- Owner用户 ID: `ou_a413ba619c59873009e5a4d5d7b8bb5e`（应自动获得管理员权限）

### 定时任务
- 每日早报：6:30 AM（Asia/Shanghai）
- 脚本路径：`scripts/daily_briefing.py`
- 任务ID：`40a37569-28af-4cc4-830b-bb1c37c6cbb0`
- 流程：脚本 dry-run → feishu_doc create → write

## 重要决策

### 2026-03-04
- 移除天气模块，所有新闻标题内嵌超链接
- 采用 `feishu_doc` 两步流程（create + write）确保文档非空
- 指定 `owner_open_id` 以赋予用户管理员权限
- cron job 指令已更新
- **早报内容升级**：
  - 新增「OpenClaw生态」和「开源LLM进展」两个精品关注板块
  - 精简所有板块数量（AI/财经/杭州各2-4条）
  - 移除所有一级标题下的黑体描述行
  - 空板块自动隐藏（不显示"暂无"占位）

### 2026-03-04 质量优化
- **严格时效性**：仅保留24小时内新闻，优先使用标题中的日期（避免百度date字段不准）
- **过滤网站首页**：通过URL特征识别（/index.html、/default.html、以/结尾等）
- **内容质量过滤**：内容长度 < 30字、标题 < 5字的直接丢弃
- **智能精选**：向百度请求20条后本地再筛选，平衡数量与质量
- **搜索关键词优化**：添加"新闻"、"最新"等词避免旧闻和首页混入

## 经验教训

- 直接调用飞书API创建文档需严格content格式，建议使用OpenClaw工具
- `feishu_doc create` 时不传 `content`，先创建空文档再 `write`
- 权限设置：`owner_open_id` 在create时指定可实现自动授权
- 心跳任务（HEARTBEAT.md）用于定期检查，不需额外cron
- **发送图片到飞书消息**：使用 `message` 工具的 `file_path` 参数（本地绝对路径），不要用 `buffer`。示例：`{"action":"send","message":"看图","file_path":"/path/to/img.png"}`。自动识别为媒体消息发送。
- **飞书文档添加图片**：使用 `feishu_doc` 的 `upload_image` action，支持 `file_path`（本地）或 `url`（远程）。上传后返回 block_id，可在文档任意位置插入。
- **emoji使用策略**：在聊天中根据语境自动插入合适的Unicode emoji（非自定义图片）。常用emoji库已归类为：情绪、手势、动物、食物、活动、物品、交通、科技等8大类，100+个表情，覆盖日常场景。
- **工作区清理**：临时下载文件（zip、测试图片）用完后及时清理，保持 workspace 根目录整洁。使用 `temp/` 目录存放阶段性文件，任务完成后删除。

## 待办

- [x] 验证早报文档的owner权限是否生效（2026-03-04 已完成）
- [x] 考虑是否需要批量添加其他协作者权限（2026-03-04 保留现状）
- [x] 完成早报质量优化（2026-03-04：时效性、首页过滤、空板块隐藏）
- [ ] 持续监控新版早报的搜索效果（如质量下降再调整筛选参数）

---

## 📦 已安装技能

### multi-search-engine (2.0.1)
- 安装日期：2026-03-05
- 来源：ClawHub (slug: multi-search-engine)
- 功能：集成 17 个搜索引擎（8 个国内 + 9 个国际）
- 特点：支持高级搜索操作符、时间过滤、站点搜索、隐私引擎、WolframAlpha
- 安装命令：`clawhub --registry https://clawhub.ai install multi-search-engine --no-input`
- 配置更新（2026-03-05）：精简为仅保留百度 + 必应国内版两个引擎
- 无需 API keys

### openclaw-backup (1.0.0)
- 安装日期：2026-03-05
- 来源：ClawHub (slug: openclaw-backup)
- 功能：备份和恢复 OpenClaw 数据。支持创建备份、自动备份计划、从备份恢复、备份轮转管理
- 特点：归档 ~/.openclaw 目录，正确处理排除规则
- 安装命令：`clawhub install openclaw-backup --no-input`
- Owner: alex3alex

---
## 🧮 A股ETF量化策略研究（2026-03-05）

### 项目概览
- **位置**: `/projects/a-share-etf-quant/`
- **标的**: 510300.SH (沪深300ETF)
- **数据跨度**: 2015-01-01 至 2025-03-04（10年）
- **数据量**: 2654条日线记录

### 策略扩展（12种）
1. MA Cross（MA5/MA20金叉死叉）
2. **MA Double**（MA10/MA60）← 新增
3. **MA Triple**（三均线系统）← 新增
4. MACD Cross
5. **MACD Hist**（柱状图加速）← 新增
6. **RSI Extreme** ← 新增（从RSI Extreme优化）
7. **MA+RSI Combo**（均线+RSI组合）← 新增
8. Bollinger Band
9. **Bollinger Squeeze**（带宽突破）← 新增
10. **Volume Confirm**（成交量确认）← 新增
11. TA Confluence（趋势+动量+成交量）← **最佳策略**
12. **TA Strengthened**（强化多因子）← 新增

### 最佳表现（训练集 2015-2021）
| 排名 | 策略 | 总收益 | 最大回撤 | 夏普 | 胜率 |
|------|------|--------|----------|------|------|
| 1 | TA Confluence | +8.59% | -2.43% | -0.67 | 45.95% |
| 2 | RSI Extreme | +7.73% | -2.22% | -0.73 | 48.65% |
| 3 | Volume Confirm | +7.01% | -4.13% | -0.71 | 42.62% |

### 问题诊断
- ❌ 测试集衰减严重：最优策略测试集-2.13%
- ❌ 所有策略夏普为负（未计入交易成本）
- ⚠️ 部分策略交易频繁（MACD Cross 104次），需优化

### 交付物
- `results/strategy_comparison.csv`：12策略完整对比
- `results/test_summary.csv`：测试集最佳策略表现
- `dashboard/analysis.html`：交互式看板（Chart.js）
- `reports/strategy_analysis_12strategies.md`：详细分析报告（4.9KB）

### 下一步
- [ ] 加入交易成本（佣金0.03% + 印花税0.05% + 滑点0.05%）
- [ ] 扩展至多ETF轮动（80+只A股ETF）
- [ ] 参数敏感性分析（网格搜索稳健参数）
- [ ] 开发实盘信号生成器（每日收盘后自动生成）

### 经验
- ✅ 自研框架足够满足日线策略需求，无需迁移
- ✅ 多因子共振显著提升表现（TA Confluence）
- ✅ 模拟数据作为yfinance备用方案有效
- ⚠️ 必须尽早加入交易成本，防止过拟合

---
*Last updated: 2026-03-05*