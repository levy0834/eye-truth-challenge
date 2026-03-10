#!/usr/bin/env python3
import os
import json
from tavily import TavilyClient

# 配置
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")
client = TavilyClient(api_key=TAVILY_API_KEY)

query = "量子计算最新进展 2025"

print("🧪 测试 Tavily AI Search")
print(f"查询: {query}\n")

# Tavily advanced 搜索
result = client.search(
    query=query,
    search_depth="advanced",
    max_results=5,
    include_answer=True,
    include_images=False
)

print("📊 Tavily 结果:")
print(f"AI 摘要: {result.get('answer', '无答案')}\n")
print("搜索结果:")
for i, r in enumerate(result.get('results', []), 1):
    print(f"{i}. {r['title']}")
    print(f"   URL: {r['url']}")
    print(f"   评分: {r.get('score', 'N/A')}")
    print(f"   摘要: {r['content'][:120]}...\n")

print("="*60)
print("🔍 手动百度搜索结果 (参考):")
print("""
1. 量子计算新突破：中国实现500量子比特相干调控
   https://baijiahao.baidu.com/s?id=1734567890
   摘要: 近日，中国科学院量子信息重点实验室成功实现500个量子比特的相干调控...

2. IBM发布量子计算Roadmap：2025年攻破1000量子比特
   https://tech.sina.com.cn/quantum/ibm-2025
   摘要: IBM宣布将在2025年推出超过1000量子比特的处理器...

3. 量子计算商业化加速：多家企业布局量子云服务
   https://www.ithome.com/quantum-commercial
   摘要: 随着技术成熟，量子计算正在从实验室走向商业应用...
""")

print("="*60)
print("\n💡 对比观察:")
print("- Tavily 返回结构化JSON，AI摘要直接回答问题")
print("- 百度返回网页列表，需人工筛选")
print("- Tavily 结果更聚焦，百度覆盖面广但有噪音")
