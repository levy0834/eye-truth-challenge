#!/usr/bin/env python3
"""
智能搜索：优先 Tavily，失败降级百度
Usage: smart_search.py "查询词" [--max-results N]
"""
import os
import sys
import json
import subprocess
from typing import Dict, Any

def search_tavily(query: str, max_results: int = 5) -> Dict[str, Any]:
    """使用 Tavily 搜索"""
    try:
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            raise ValueError("未配置 TAVILY_API_KEY")
        
        client = TavilyClient(api_key=api_key)
        result = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
            include_images=False
        )
        return {
            "success": True,
            "source": "tavily",
            "answer": result.get("answer", ""),
            "results": result.get("results", []),
            "raw": result
        }
    except Exception as e:
        return {
            "success": False,
            "source": "tavily",
            "error": str(e)
        }

def search_baidu(query: str, max_results: int = 5) -> Dict[str, Any]:
    """使用百度搜索（通过 baidu-search 技能）"""
    try:
        # 调用 web_fetch 进行搜索（实际可能需要使用 skill）
        # 这里简化：假设使用百度搜索接口
        # 实际部署时会通过 OpenClaw 的 web_fetch 或 baidu-search skill
        return {
            "success": False,
            "source": "baidu",
            "error": "百度搜索集成待实现"
        }
    except Exception as e:
        return {
            "success": False,
            "source": "baidu",
            "error": str(e)
        }

def smart_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """智能搜索：Tavily 优先，失败降级百度"""
    # 1. 尝试 Tavily
    result = search_tavily(query, max_results)
    if result["success"]:
        return result
    
    print(f"⚠️ Tavily 失败: {result.get('error', 'Unknown')}")
    print("🔄 降级到百度搜索...")
    
    # 2. 降级百度
    result = search_baidu(query, max_results)
    if result["success"]:
        return result
    
    # 3. 都失败了
    return {
        "success": False,
        "answer": None,
        "results": [],
        "error": f"Tavily: {result.get('error')} | 百度: {result.get('error')}"
    }

def main():
    if len(sys.argv) < 2:
        print("用法: smart_search.py '查询词' [--max-results N]")
        sys.exit(1)
    
    query = sys.argv[1]
    max_results = 5
    if len(sys.argv) >= 4 and sys.argv[2] == "--max-results":
        max_results = int(sys.argv[3])
    
    result = smart_search(query, max_results)
    
    # 输出 JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
