# 飞书文档操作技巧（每日早报专用）

## 📝 核心流程（必看）

### 1️⃣ 两步创建法（避免空文档错误）
```bash
# 第一步：创建空文档（不传 content）
feishu_doc --action create --title "今日早报" --owner_open_id ou_a413ba619c59873009e5a4d5d7b8bb5e

# 第二步：写入内容
feishu_doc --action write --doc_token <返回的token> --content "markdown内容..."
```

**为什么？** 飞书API要求文档必须有内容才能创建，OpenClaw的 `feishu_doc create` 必须配合后续 `write` 使用。

### 2️⃣ 权限设置（让用户能编辑）
- `create` 时通过 `--owner_open_id` 指定所有者，自动获得管理员权限
- Owner: `ou_a413ba619c59873009e5a4d5d7b8bb5e`
- 如需添加其他协作者，需额外调用权限接口（暂未实现）

### 3️⃣ 内容格式建议
- 使用 Markdown 格式
- 新闻标题内嵌超链接（已移除独立天气模块）
- 示例：
  ```markdown
  ## 今日头条
  - [科技新闻标题](https://news.url)
  - [财经动态](https://finance.url)
  ```

## ⚠️ 常见坑

1. **不要**在 `create` 时传 `content` → 会失败
2. **不要**直接调用飞书API → 格式复杂，用OpenClaw工具
3. **不要**忘记 `owner_open_id` → 文档创建者可能不是用户
4. **不要**用cron做精确时间任务 → 用HEARTBEAT.md定期检查

## 📋 早报任务流程

1. 脚本运行（dry-run测试）
2. 调用 `feishu_doc create` 创建空文档
3. 获取返回的 `doc_token`
4. 调用 `feishu_doc write` 写入内容
5. 记录日志到 `memory/YYYY-MM-DD.md`
6. cron或心跳触发下一次执行

## 🔗 参考配置

- 任务ID: `40a37569-28af-4cc4-830b-bb1c37c6cbb0`
- 触发时间: 6:30 AM (Asia/Shanghai)
- 脚本路径: `scripts/daily_briefing.py`
- 用户ID: `ou_a413ba619c59873009e5a4d5d7b8bb5e`

---

**最后更新**: 2026-03-04 | 来源: MEMORY.md + 实操经验
