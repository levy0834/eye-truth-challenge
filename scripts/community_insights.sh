#!/bin/zsh
# OpenClaw 社区洞察日报任务 - 早上 7:00 运行
# 生成洞察报告并发布到飞书文档

cd /Users/levy/.openclaw/workspace

# 加载环境变量
source ~/.zshrc 2>/dev/null

# 生成洞察报告到临时文件
python3 scripts/community_insights.py > /tmp/community_insights.md 2>&1

# 检查输出是否非空
if [ ! -s /tmp/community_insights.md ]; then
  echo "❌ 洞察报告生成失败或为空"
  exit 1
fi

# 提取标题（第一行）
TITLE=$(head -n1 /tmp/community_insights.md | sed 's/# //;s/^[[:space:]]*//;s/[[:space:]]*$//')

# 调用 openclaw agent 发送到飞书（这里用简短指令，由 OpenClaw cron 执行器解析）
# 实际由 payload.message 中的指令执行，这里只是占位
echo "✅ 洞察报告已生成: /tmp/community_insights.md"
echo "📨 标题: $TITLE"
echo "⏳ 等待 OpenClaw cron 执行器发布到飞书..."
