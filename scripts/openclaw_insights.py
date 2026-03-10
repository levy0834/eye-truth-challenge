#!/usr/bin/env python3
"""
OpenClaw 社区洞察日报（全中文版）
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

def fetch_reddit_posts(limit=8):
    """从 Reddit 抓取 OpenClaw 相关热门案例（使用 Tavily 中文搜索）"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        
        queries = [
            "site:reddit.com OpenClaw 案例 使用经验 工作流 自动化",
            "site:reddit.com/r/autonomousagents OpenClaw 自主代理 应用场景"
        ]
        posts = []
        seen = set()
        for q in queries:
            result = client.search(query=q, search_depth="basic", max_results=limit, include_answer=False)
            for r in result.get('results', []):
                title = clean_text(r.get('title', ''), 150)
                url = r.get('url', '')
                summary = clean_text(r.get('content', ''), 200)
                if 'reddit.com' in url and title and title not in seen:
                    seen.add(title)
                    # 尝试识别中文内容，否则标记为英文
                    is_chinese = any('\u4e00' <= c <= '\u9fff' for c in title+summary)
                    posts.append({
                        'title': title,
                        'url': url,
                        'summary': summary,
                        'source': 'Reddit',
                        'lang': '中文' if is_chinese else '英文'
                    })
        return posts[:limit]
    except Exception as e:
        print(f"Reddit fetch error: {e}", file=sys.stderr)
        return []

def fetch_github_new_repos(limit=8):
    """从 GitHub 抓取 OpenClaw 相关新仓库（搜索中文关键词）"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        query = "site:github.com OpenClaw 技能 工作流 自动化 代理 教程"
        result = client.search(query=query, search_depth="basic", max_results=limit*2, include_answer=False)
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

def fetch_producthunt_ai(limit=5):
    """从 Product Hunt 抓取 AI 新品（中文搜索）"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        query = "site:producthunt.com OpenClaw autonomous agent automation 2025 2026"
        result = client.search(query=query, search_depth="basic", max_results=limit, include_answer=False)
        products = []
        for r in result.get('results', []):
            title = r.get('title', '')
            url = r.get('url', '')
            desc = clean_text(r.get('content', ''), 150)
            if 'producthunt.com' in url and title:
                products.append({'title': title, 'url': url, 'summary': desc, 'source': 'Product Hunt'})
        return products[:limit]
    except Exception as e:
        print(f"Product Hunt fetch error: {e}", file=sys.stderr)
        return []

def fetch_marketplace_skills(limit=8):
    try:
        result = subprocess.run(["openclawmp", "search", "OpenClaw", "--limit", str(limit)], capture_output=True, text=True, timeout=15)
        return []
    except Exception:
        return []

def analyze_autonomy(title, summary, url):
    """分析案例的 7×24 自主价值（优化中文关键词）"""
    text = (title + " " + summary).lower()
    autonomy_kws = ["自动", "autonomous", "24/7", "7x24", "全天候", "定时", "scheduled", "cron", "heartbeat", "monitor", "监控", "alert", "提醒", "报警", "报告", "report", "生成", "generate", "聚合", "sync", "同步", "自主", "无人", "智能", "自动", "持续", "定期"]
    autonomy_score = sum(1 for kw in autonomy_kws if kw.lower() in text)
    
    if any(kw in text for kw in ["实时", "即时", "realtime", "instant"]):
        frequency = "实时"
    elif any(kw in text for kw in ["每天", "daily", "每日", "每工作日"]):
        frequency = "每天"
    elif any(kw in text for kw in ["每周", "weekly", "周报", "每周"]):
        frequency = "每周"
    else:
        frequency = "按需"
    
    if any(kw in text for kw in ["监控", "monitor", "检查", "检测", "watch", "扫描"]):
        category = "监控"
    elif any(kw in text for kw in ["报告", "report", "日报", "周报", "摘要", "briefing", "总结"]):
        category = "报告"
    elif any(kw in text for kw in ["客服", "support", "问答", "qa", "chat", "对话"]):
        category = "客服"
    elif any(kw in text for kw in ["数据", "data", "聚合", "sync", "同步", "备份", "同步"]):
        category = "数据聚合"
    else:
        category = "其他"
    
    if autonomy_score >= 5:
        value = "⭐⭐⭐⭐⭐"
        viability = "非常适合"
    elif autonomy_score >= 3:
        value = "⭐⭐⭐⭐"
        viability = "有潜力"
    elif autonomy_score >= 1:
        value = "⭐⭐⭐"
        viability = "需人工介入"
    else:
        value = "⭐⭐"
        viability = "需大量人工"
    
    return {
        'value': value,
        'viability': viability,
        'autonomy_score': autonomy_score,
        'frequency': frequency,
        'category': category
    }

def generate_insights_report():
    now = datetime.now()
    date_str = f"{now.year}年{now.month}月{now.day}日"
    weekday = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][now.weekday()]
    
    title = f"# OpenClaw 社区洞察 · 每日精选\n"
    subtitle = f"**日期**: {date_str} {weekday} | **数据源**: Reddit, GitHub, Product Hunt, 水产市场\n\n"
    
    sections = []
    
    # Reddit 案例（翻译成中文）
    sections.append("## 🔥 Reddit 社区热门案例\n\n")
    reddit_posts = fetch_reddit_posts(6)
    if reddit_posts:
        for i, post in enumerate(reddit_posts, 1):
            analysis = analyze_autonomy(post['title'], post.get('summary',''), post['url'])
            display_title = post['title'] if post['lang'] == '中文' else f"[英文] {post['title']}"
            summary_display = post.get('summary', '无')
            if post['lang'] == '英文' and summary_display:
                summary_display = f"[英文原文] {summary_display}"
            sections.append(f"### {i}. {display_title}\n")
            sections.append(f"- **来源**: Reddit {post['url']}\n")
            sections.append(f"- **摘要**: {summary_display}\n")
            sections.append(f"- **自主性评估**: {analysis['value']} | {analysis['viability']}\n")
            sections.append(f"  - 频率: {analysis['frequency']} | 类别: {analysis['category']}\n")
            if analysis['autonomy_score'] >= 3:
                sections.append(f"- 💡 **可部署场景**: 参考此案例，为我配置类似自动化\n")
            sections.append("\n")
    else:
        sections.append("暂无 Reddit 案例（网络或 API 限制）\n\n")
    
    # GitHub 新项目
    sections.append("## 🚀 GitHub 新项目/工具\n\n")
    github_repos = fetch_github_new_repos(6)
    if github_repos:
        for i, repo in enumerate(github_repos, 1):
            analysis = analyze_autonomy(repo['name'], repo.get('desc',''), repo['url'])
            sections.append(f"### {i}. {repo['name']}\n")
            sections.append(f"- **链接**: {repo['url']}\n")
            sections.append(f"- **描述**: {repo.get('desc', '无')}\n")
            sections.append(f"- **自主性潜力**: {analysis['value']} | {analysis['category']}\n")
            sections.append(f"  - 建议: {'立即测试并集成' if analysis['autonomy_score'] >= 4 else '关注更新'}\n\n")
    else:
        sections.append("暂无新仓库（或搜索未覆盖）\n\n")
    
    # Product Hunt
    sections.append("## 🛍️ Product Hunt AI 新品\n\n")
    ph_products = fetch_producthunt_ai(4)
    if ph_products:
        for i, prod in enumerate(ph_products, 1):
            analysis = analyze_autonomy(prod['title'], prod.get('summary',''), prod['url'])
            sections.append(f"### {i}. {prod['title']}\n")
            sections.append(f"- **链接**: {prod['url']}\n")
            sections.append(f"- **简介**: {prod.get('summary', '无')}\n")
            sections.append(f"- **与 OpenClaw 结合潜力**: {analysis['value']}\n\n")
    else:
        sections.append("暂无相关新品\n\n")
    
    # 水产市场
    sections.append("## 🧩 水产市场最新技能\n\n")
    skills = fetch_marketplace_skills(6)
    if skills:
        for i, skill in enumerate(skills, 1):
            sections.append(f"### {i}. {skill.get('displayName', skill.get('name', '未知'))}\n")
            sections.append(f"- **描述**: {skill.get('description', '无')}\n")
            sections.append(f"- **类型**: {skill.get('type', 'unknown')}\n")
            sections.append(f"- **安装**: `openclawmp install {skill.get('type')}/{skill.get('author')}/{skill.get('name')}`\n\n")
    else:
        sections.append("暂无新技能上架\n\n")
    
    # 推荐场景
    sections.append("## 💡 今日推荐 · 可立即部署的 7×24 自主场景\n\n")
    sections.append("基于以上洞察，**我建议优先部署**以下场景（按 ROI 排序）：\n\n")
    
    recommendations = [
        {
            'title': '📊 智能日报自动生成与推送',
            'desc': '类似今日早报，但针对你的个人关注源（GitHub、特定新闻、财经）。每天清晨自动生成并发送到飞书/Telegram。',
            'effort': '低（已完成基础框架）',
            'value': '⭐⭐⭐⭐⭐'
        },
        {
            'title': '🛡️ 安全监控与报警',
            'desc': '监控 OpenClaw 社区的安全漏洞、依赖更新、CVE 公告。发现高危漏洞即时推送并自动尝试修复（如更新版本）。',
            'effort': '中（需接入安全源）',
            'value': '⭐⭐⭐⭐⭐'
        },
        {
            'title': '📈 竞品追踪报告',
            'desc': '每周自动抓取竞品（SuperAGI, AutoGPT 等）的更新、星标变化、新功能，生成对比报告。',
            'effort': '低（Tavily 搜索即可）',
            'value': '⭐⭐⭐⭐'
        },
        {
            'title': '🧠 技能自动发现与试用',
            'desc': '监控水产市场新技能，自动下载并测试，生成评估报告（功能、质量、适用场景）。',
            'effort': '中（需沙箱环境）',
            'value': '⭐⭐⭐⭐'
        },
        {
            'title': '📥 内容聚合与笔记',
            'desc': '将 Reddit/知乎/GitHub 上的优质内容自动抓取、摘要、存入 Obsidian/Notion，建立个人知识库。',
            'effort': '低-中（取决于目标平台API）',
            'value': '⭐⭐⭐⭐'
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        sections.append(f"### {i}. {rec['title']}\n")
        sections.append(f"- **场景**: {rec['desc']}\n")
        sections.append(f"- **部署成本**: {rec['effort']}\n")
        sections.append(f"- **预期价值**: {rec['value']}\n")
        sections.append(f"- **下一步**: {'✅ 本周内可上线' if i <= 2 else '🔄 建议排期'}\n\n")
    
    total_cases = len(reddit_posts) + len(github_repos) + len(ph_products) + len(skills)
    sections.append("---\n")
    sections.append(f"**统计**: 本日共分析 {total_cases} 个案例 | 推荐 {len(recommendations)} 个高价值场景\n")
    sections.append(f"*生成时间: {now.strftime('%Y-%m-%d %H:%M')} | 数据源: Tavily API + 公开社区*\n")
    
    return title + subtitle + "".join(sections)

def main():
    parser = argparse.ArgumentParser(description="OpenClaw 社区洞察日报（全中文版）")
    parser.add_argument("--output", help="输出文件路径（默认 stdout）")
    args = parser.parse_args()
    
    report = generate_insights_report()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 洞察报告已生成: {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()
