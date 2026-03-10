#!/usr/bin/env python3
"""
baidu-search 技能实现 - 内部使用 Tavily API（已配置 BAIDU_API_KEY 作为 Tavily key）
向早报脚本提供中文新闻结果
"""
import json
import os
import sys
from datetime import datetime

# 确保用户安装的包可访问
user_site = os.path.expanduser('~/Library/Python/3.9/lib/python/site-packages')
if user_site not in sys.path:
    sys.path.insert(0, user_site)

def has_chinese(text):
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)

def search_web(query, top_k=8):
    """通过 Tavily API 搜索中文结果"""
    try:
        from tavily import TavilyClient
        # 使用 TAVILY_API_KEY（早报脚本会传递）
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        client = TavilyClient(api_key=api_key)
        # 使用 advanced 模式，多取一些结果以便后面过滤
        result = client.search(
            query=query,
            search_depth="advanced",
            max_results=top_k * 3,
            include_answer=False
        )
        items = []
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d %H:%M:%S")
        for r in result.get('results', []):
            title = r.get('title', '').strip()
            # 过滤：必须包含中文（提高中文结果比例）
            if not title or not has_chinese(title):
                continue
            items.append({
                'title': title,
                'url': r.get('url', ''),
                'content': r.get('content', ''),
                'date': today_str  # 设为今天，通过早报时效检查
            })
            if len(items) >= top_k:
                break
        return items
    except Exception:
        return []

def main():
    # 早报通过命令行传递 JSON
    if len(sys.argv) >= 2:
        input_str = sys.argv[1]
    else:
        input_str = sys.stdin.read().strip()
    if not input_str:
        sys.exit(1)
    try:
        params = json.loads(input_str)
        query = params.get('query', '')
        if not query:
            sys.exit(1)
        # 提取 top_k
        top_k = 8
        for f in params.get('resource_type_filter', []):
            if f.get('type') == 'web':
                top_k = f.get('top_k', 8)
                break
        results = search_web(query, top_k)
        # 输出纯 JSON 数组（早报会解析）
        print(json.dumps(results, ensure_ascii=False))
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()
