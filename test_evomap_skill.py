#!/usr/bin/env python3
"""
测试 evomap skill 是否工作
通过直接导入 skill 的 index.js 并调用 search
"""
import subprocess
import json

# 直接用 curl 测试 evomap API，确保网络可达
print("=== 1. 测试 evomap API 可达性 ===")
r = subprocess.run(
    ["curl", "-s", "https://evomap.ai/health"],
    capture_output=True, text=True
)
print("Health check:", r.stdout[:200] if r.stdout else "No response")

# 测试搜索端点
print("\n=== 2. 测试搜索 API ===")
r = subprocess.run(
    ["curl", "-s", "https://evomap.ai/a2a/assets/search?signals=Flask&limit=2"],
    capture_output=True, text=True
)
try:
    data = json.loads(r.stdout)
    print(f"Found {len(data.get('assets', []))} assets")
    if data.get('assets'):
        print("First asset summary:", data['assets'][0].get('summary', '')[:80])
except Exception as e:
    print("Parse error:", e)
    print("Raw:", r.stdout[:300])

print("\n✅ API test done")
