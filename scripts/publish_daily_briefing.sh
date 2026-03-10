#!/bin/zsh
set -e

WORKSPACE="/Users/levy/.openclaw/workspace"
PYTHON="python3"

TITLE_FILE="/tmp/daily_report_title.txt"
CONTENT_FILE="/tmp/daily_report_content.md"

# 生成标题和内容文件
echo "🔄 正在生成早报内容..."
$PYTHON $WORKSPACE/scripts/daily_briefing.py --output-title "$TITLE_FILE" --output-content "$CONTENT_FILE"

# 子代理任务描述
TASK="请读取 $TITLE_FILE 作为标题，读取 $CONTENT_FILE 作为内容。然后：
1. 使用 feishu_doc create 创建文档，传入 title（读取的文件内容）和 owner_open_id=ou_a413ba619c59873009e5a4d5d7b8bb5e
2. 获取返回的 doc_token 后，使用 feishu_doc write 将内容写入该文档
3. 写入成功后删除 $TITLE_FILE 和 $CONTENT_FILE 两个临时文件
4. 将文档链接回复给我

注意：先 create 空文档，再 write 写入全部内容。"

echo "🚀 正在调用 OpenClaw 代理执行发布..."
/Users/levy/.nvm/versions/node/v24.14.0/bin/openclaw agent --agent main --message "$TASK" --thinking low
