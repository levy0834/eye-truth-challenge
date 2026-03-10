#!/bin/bash
# Codex Codegen Wrapper
# 用法: ./codex-gen.sh "写一个Python函数计算斐波那契数列"

set -e

TASK="$1"
MODEL="${2:-gpt-5.3-codex-xhigh}"
WORKSPACE="${3:-/Users/levy/.openclaw/workspace}"
API_KEY="${CODEX_API_KEY:-sk-U4Clj0nuId2WfTZyWjXKyLzKZzbCgi7myU52qsirORQrh4tb}"
BASE_URL="${CODEX_BASE_URL:-https://ai.shares.indevs.in/v1}"

# 切换到 workspace
cd "$WORKSPACE"

# 调用 Codex API (简化版本，实际可用 curl 或 python)
cat << 'PYTHON_SCRIPT' > /tmp/codex_call.py
import os, sys, json, requests
api_key = os.environ.get('CODEX_API_KEY')
base_url = os.environ.get('CODEX_BASE_URL')
model = os.environ.get('CODEX_MODEL')
task = sys.argv[1]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are an expert software engineer. Write clean, production-ready code with tests."},
        {"role": "user", "content": task}
    ],
    "temperature": 0.2
}

resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=120)
resp.raise_for_status()
content = resp.json()["choices"][0]["message"]["content"]
print(content)
PYTHON_SCRIPT

export CODEX_API_KEY="$API_KEY"
export CODEX_BASE_URL="$BASE_URL"
export CODEX_MODEL="$MODEL"

OUTPUT=$(python3 /tmp/codex_call.py "$TASK")
echo "=== Codex 生成结果 ==="
echo "$OUTPUT"
echo "======================="

# 可选：保存到文件
# echo "$OUTPUT" > "codex_output_$(date +%s).txt"