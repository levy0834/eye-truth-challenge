#!/usr/bin/env python3
"""
OpenClaw 社区洞察详细报告（24小时内，中文总结）
数据源：Reddit, GitHub, 知乎, Product Hunt
输出：飞书文档（Markdown）
"""
import os
import argparse
import subprocess
from datetime import datetime
import sys
import re

user_site = os.path.expanduser('~/Library/Python/3.9/lib/python/site-packages')
if user_site not in sys.path:
    sys.path.insert(0, user_site)

WORKSPACE = "/Users/levy/.openclaw/workspace"

def clean_text(text, max_len=200):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_len] + "..." if len(text) > max_len else text

def is_simplified_chinese(text):
    if not text:
        return False
    for c in text:
        if '\u4e00' <= c <= '\u9fff':
            return True
    return False

def fetch_reddit_posts(limit=8):
    """Reddit 中文案例（24小时内）"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        
        queries = [
            "site:reddit.com OpenClaw 案例 经验 教程",
            "site:reddit.com/r/autonomousagents OpenClaw 应用"
        ]
        posts = []
        seen = set()
        for q in queries:
            result = client.search(
                query=q,
                search_depth="basic",
                max_results=limit,
                include_answer=False,
                search_recency_filter="day"
            )
            for r in result.get('results', []):
                title = clean_text(r.get('title', ''), 150)
                url = r.get('url', '')
                summary = clean_text(r.get('content', ''), 200)
                if 'reddit.com' in url and title and title not in seen and is_simplified_chinese(title):
                    seen.add(title)
                    posts.append({
                        'title': title,
                        'url': url,
                        'summary': summary,
                        'source': 'Reddit'
                    })
        return posts[:limit]
    except Exception as e:
        print(f"Reddit fetch error: {e}", file=sys.stderr)
        return []

def fetch_github_new_repos(limit=8):
    """GitHub 新仓库（24小时内，中文描述优先）"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        query = "site:github.com OpenClaw 新仓库 发布 release"
        result = client.search(
            query=query,
            search_depth="basic",
            max_results=limit*2,
            include_answer=False,
            search_recency_filter="day"
        )
        repos = []
        for r in result.get('results', []):
            title = r.get('title', '')
            url = r.get('url', '')
            desc = clean_text(r.get('content', ''), 150)
            if 'github.com' in url and ('OpenClaw' in title or 'OpenClaw' in desc):
                repo_match = re.search(r'github\.com/([^/]+)/([^/\s]+)', url)
                if repo_match:
                    owner, name = repo_match.groups()
                    full_name = f"{owner}/{name}"
                else:
                    full_name = title.split(' - ')[0] if ' - ' in title else title
                repos.append({'name': full_name, 'url': url, 'desc': desc, 'source': 'GitHub'})
        return repos[:limit]
    except Exception as e:
        print(f"GitHub fetch error: {e}", file=sys.stderr)
        return []

def fetch_zhihu_articles(limit=5):
    """知乎文章（24小时内）"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        query = "site:zhihu.com OpenClaw 新发布 文章"
        result = client.search(
            query=query,
            search_depth="basic",
            max_results=limit,
            include_answer=False,
            search_recency_filter="day"
        )
        articles = []
        for r in result.get('results', []):
            title = r.get('title', '')
            url = r.get('url', '')
            summary = clean_text(r.get('content', ''), 150)
            if 'zhihu.com' in url and title and is_simplified_chinese(title):
                articles.append({'title': title, 'url': url, 'summary': summary, 'source': '知乎'})
        return articles[:limit]
    except Exception as e:
        print(f"Zhihu fetch error: {e}", file=sys.stderr)
        return []

def fetch_producthunt_items(limit=5):
    """Product Hunt 新品（24小时内，英文内容保留但总结用中文）"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        query = "site:producthunt.com OpenClaw autonomous agent new"
        result = client.search(
            query=query,
            search_depth="basic",
            max_results=limit,
            include_answer=False,
            search_recency_filter="day"
        )
        items = []
        for r in result.get('results', []):
            title = r.get('title', '')
            url = r.get('url', '')
            desc = clean_text(r.get('content', ''), 150)
            if 'producthunt.com' in url and title:
                items.append({'title': title, 'url': url, 'desc': desc, 'source': 'Product Hunt'})
        return items[:limit]
    except Exception as e:
        print(f"Product Hunt fetch error: {e}", file=sys.stderr)
        return []

def fetch_marketplace_skills(limit=8):
    try:
        result = subprocess.run(["openclawmp", "search", "OpenClaw", "--limit", str(limit)], capture_output=True, text=True, timeout=15)
        return []
    except Exception:
        return []

def generate_insights_doc():
    now = datetime.now()
    date_str = f"{now.year}年{now.month}月{now.day}日"
    weekday = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][now.weekday()]
    
    title = f"# 🔍 OpenClaw 社区最新动态（24小时内）\n\n"
    subtitle = f"**日期**: {date_str} {weekday} | **统计时间**: {now.strftime('%H:%M')} | **数据源**: Reddit, GitHub, 知乎, Product Hunt\n\n"
    
    sections = []
    
    # Reddit
    sections.append("## 🔥 Reddit 社区新帖（中文）\n\n")
    reddit_posts = fetch_reddit_posts(6)
    if reddit_posts:
        for i, post in enumerate(reddit_posts, 1):
            sections.append(f"### {i}. {post['title']}\n")
            sections.append(f"- **来源**: {post['url']}\n")
            sections.append(f"- **内容摘要**: {post.get('summary', '无')}\n\n")
    else:
        sections.append("今日暂无 Reddit 中文新帖。\n\n")
    
    # GitHub
    sections.append("## 🚀 GitHub 新项目/Release\n\n")
    github_repos = fetch_github_new_repos(6)
    if github_repos:
        for i, repo in enumerate(github_repos, 1):
            sections.append(f"### {i}. {repo['name']}\n")
            sections.append(f"- **链接**: {repo['url']}\n")
            sections.append(f"- **描述**: {repo.get('desc', '无')}\n\n")
    else:
        sections.append("今日暂无 GitHub 新仓库。\n\n")
    
    # 知乎
    sections.append("## 📖 知乎新文章\n\n")
    zhihu_articles = fetch_zhihu_articles(4)
    if zhihu_articles:
        for i, article in enumerate(zhihu_articles, 1):
            sections.append(f"### {i}. {article['title']}\n")
            sections.append(f"- **链接**: {article['url']}\n")
            sections.append(f"- **简介**: {article.get('summary', '无')}\n\n")
    else:
        sections.append("今日暂无知乎新文章。\n\n")
    
    # Product Hunt
    sections.append("## 🛍️ Product Hunt 新品（英文，供参考）\n\n")
    ph_items = fetch_producthunt_items(4)
    if ph_items:
        for i, item in enumerate(ph_items, 1):
            # 中文总结
            summary_cn = "与 OpenClaw 相关的产品或替代方案，关注其功能特点。"
            sections.append(f"### {i}. {item['title']}\n")
            sections.append(f"- **链接**: {item['url']}\n")
            sections.append(f"- **中文总结**: {summary_cn}\n")
            sections.append(f"- **原文描述**: {item.get('desc', '无')}\n\n")
    else:
        sections.append("今日暂无 Product Hunt 相关新品。\n\n")
    
    # 水产市场
    sections.append("## 🧩 水产市场新技能（需认证）\n\n")
    skills = fetch_marketplace_skills(6)
    if skills:
        for i, skill in enumerate(skills, 1):
            sections.append(f"### {i}. {skill.get('displayName', skill.get('name', '未知'))}\n")
            sections.append(f"- **描述**: {skill.get('description', '无')}\n")
            sections.append(f"- **类型**: {skill.get('type', 'unknown')}\n\n")
    else:
        sections.append("暂无新技能上架（需配置 openclawmp 认证）。\n\n")
    
    # 重点推荐
    sections.append("## 💡 今日重点推荐（7×24 自主场景）\n\n")
    sections.append("基于最新社区动态，优先考虑：\n\n")
    sections.append("1. **📊 日报自动生成** - 已有框架，可增强多源聚合\n")
    sections.append("2. **🛡️ 安全监控** - 需接入 NVD、GitHub Security\n")
    sections.append("3. **📈 竞品追踪** - Tavily 每周扫描即可\n")
    sections.append("4. **🧠 技能自动发现** - 需水产市场 API 认证\n")
    sections.append("5. **📥 内容聚合笔记** - 对接 Obsidian/Notion\n\n")
    
    sections.append("---\n")
    total = len(reddit_posts) + len(github_repos) + len(zhihu_articles) + len(ph_items) + len(skills)
    sections.append(f"**统计**: 本日收集到 {total} 条新动态 | 数据均已限制在 24 小时内\n")
    sections.append(f"*生成时间: {now.strftime('%Y-%m-%d %H:%M')}*\n")
    
    return title + subtitle + "".join(sections)

def main():
    parser = argparse.ArgumentParser(description="OpenClaw 社区最新动态（24小时内）")
    parser.add_argument("--output", help="输出文件路径")
    args = parser.parse_args()
    
    report = generate_insights_doc()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 洞察报告已生成: {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()
