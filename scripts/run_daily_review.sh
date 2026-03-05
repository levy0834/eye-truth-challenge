#!/bin/zsh
# OpenClaw 每日复盘任务 - 晚上 22:00 运行
# 生成复盘卡片并发送到飞书

cd /Users/levy/.openclaw/workspace

# 加载环境变量
source ~/.zshrc 2>/dev/null

# 生成复盘卡片
python3 scripts/daily_review_card.py > /tmp/todays_review.txt 2>&1

# 发送到飞书（调用 message 工具，这里用 openclaw 的 CLI 或 API）
# 由于 cron 环境限制，我们调用 openclaw sessions_send 或直接使用 curl 调用飞书机器人
# 简单方案：写入文件，由主进程读取发送；或者直接调用 message 工具（如果可用）

# 方案：输出到 stdout，由 OpenClaw 的 cron 处理器自动发送？
# 实际情况：cron 输出会 mail 到用户，不理想

# 改用：将卡片追加到 reports/ 目录，并触发一個标记文件让主进程发送
REPORT_CONTENT=$(cat /tmp/todays_review.txt)
echo "$REPORT_CONTENT" >> /Users/levy/.openclaw/workspace/reports/daily_review_history.md

# 触发发送：创建一个 .send_review 标记
touch /Users/levy/.openclaw/workspace/.send_review_$(date +%Y%m%d)

echo "✅ 复盘卡片已生成: /tmp/todays_review.txt"
echo "📨 请手动发送或配置自动发送机制"
