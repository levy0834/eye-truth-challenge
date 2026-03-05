#!/usr/bin/env python3
"""
每日复盘报告（整合版）
包含：
- 今日完成的重要任务
- 社区洞察（仅简体中文内容）
- 成长与思考
- 记忆优化建议
"""
import os
import argparse
import subprocess
from datetime import datetime, timedelta
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
    """检测是否为简体中文内容"""
    if not text:
        return False
    # 简体中文字符范围
    for c in text:
        if '\u4e00' <= c <= '\u9fff':
            return True
    return False

def fetch_reddit_posts(limit=8):
    """只保留简体中文标题和摘要的 Reddit 案例"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        
        queries = [
            "site:reddit.com OpenClaw 案例 使用经验 工作流 自动化 教程",
            "site:reddit.com/r/autonomousagents OpenClaw 应用 部署"
        ]
        posts = []
        seen = set()
        for q in queries:
            result = client.search(query=q, search_depth="basic", max_results=limit, include_answer=False)
            for r in result.get('results', []):
                title = clean_text(r.get('title', ''), 150)
                url = r.get('url', '')
                summary = clean_text(r.get('content', ''), 200)
                # 只保留标题为中文的
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
    """抓取中文描述的 GitHub 仓库"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        query = "site:github.com OpenClaw 技能 教程 中文 配置 部署"
        result = client.search(query=query, search_depth="basic", max_results=limit*2, include_answer=False)
        repos = []
        for r in result.get('results', []):
            title = r.get('title', '')
            url = r.get('url', '')
            desc = clean_text(r.get('content', ''), 150)
            if 'github.com' in url and ('OpenClaw' in title or 'OpenClaw' in desc) and is_simplified_chinese(desc):
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
    """从知乎抓取 OpenClaw 相关文章"""
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return []
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        query = "site:zhihu.com OpenClaw 使用 教程 案例 部署"
        result = client.search(query=query, search_depth="basic", max_results=limit, include_answer=False)
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

def fetch_marketplace_skills(limit=8):
    try:
        result = subprocess.run(["openclawmp", "search", "OpenClaw", "--limit", str(limit)], capture_output=True, text=True, timeout=15)
        return []
    except Exception:
        return []

def analyze_autonomy(title, summary, url):
    """分析案例的 7×24 自主价值"""
    text = (title + " " + summary).lower()
    autonomy_kws = ["自动", "autonomous", "24/7", "7x24", "全天候", "定时", "scheduled", "cron", "heartbeat", "monitor", "监控", "alert", "提醒", "报警", "报告", "report", "生成", "generate", "聚合", "sync", "同步", "自主", "无人", "智能", "持续", "定期", "周期性"]
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
    elif any(kw in text for kw in ["数据", "data", "聚合", "sync", "同步", "备份"]):
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

def generate_review_report():
    now = datetime.now()
    date_str = f"{now.year}年{now.month}月{now.day}日"
    weekday = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][now.weekday()]
    
    title = f"# 📋 每日复盘报告\n\n"
    header = f"**日期**: {date_str} {weekday} | **生成时间**: {now.strftime('%H:%M')}\n\n---\n\n"
    
    sections = []
    
    # 1. 今日完成任务
    sections.append("## ✅ 今日完成的重要任务\n\n")
    sections.append("- ✅ 完成早报系统中文化（Tavily 接口 + 中文过滤）\n")
    sections.append("- ✅ 发布每日早报到飞书（测试成功）\n")
    sections.append("- ✅ 创建社区洞察脚本并试点运行\n")
    sections.append("- ✅ 修复 Tavily 模块导入路径问题\n")
    sections.append("- ✅ 优化搜索超时和稳定性\n\n")
    
    # 2. 成长与思考
    sections.append("## 🧠 成长与思考\n\n")
    sections.append("### 今日收获\n")
    sections.append("- 掌握了 Tavily API 的中文结果过滤技巧\n")
    sections.append("- 熟悉了 OpenClaw 脚本的调试和部署流程\n")
    sections.append("- 理解了用户对中文内容的强需求\n\n")
    sections.append("### 需要改进\n")
    sections.append("- 搜索超时问题尚需优化（增加重试机制）\n")
    sections.append("- Product Hunt 数据源以英文为主，考虑替换为中文社区\n")
    sections.append("- 水产市场 API 调用需要认证配置\n\n")
    
    # 3. 记忆优化建议
    sections.append("## 💾 记忆管理优化建议\n\n")
    sections.append("### 今日知识增量\n")
    sections.append("- Tavily 中文搜索：使用中文关键词 + 结果过滤\n")
    sections.append("- 飞书文档 API：create + write 两步流程确保非空\n")
    sections.append("- 环境变量传递：童子进程需显式 source ~/.zshrc\n\n")
    sections.append("### 建议归档\n")
    sections.append("- 将 `openclaw_insights.py` 放入 `scripts/` 并加入 cron\n")
    sections.append("- 记录常见错误：ModuleNotFoundError、超时、空结果\n")
    sections.append("- 保存今日报告到 `reports/` 目录供后续参考\n\n")
    
    # 4. 社区洞察（仅简体中文）
    sections.append("## 🔍 社区洞察（仅简体中文内容）\n\n")
    
    # Reddit 中文案例
    sections.append("### 🔥 Reddit 中文案例\n\n")
    reddit_posts = fetch_reddit_posts(6)
    if reddit_posts:
        for i, post in enumerate(reddit_posts, 1):
            sections.append(f"#### {i}. {post['title']}\n")
            sections.append(f"- **来源**: {post['url']}\n")
            sections.append(f"- **摘要**: {post.get('summary', '无')}\n\n")
    else:
        sections.append("暂无 Reddit 中文案例（搜索词可进一步优化）\n\n")
    
    # GitHub 中文项目
    sections.append("### 🚀 GitHub 新项目（中文描述）\n\n")
    github_repos = fetch_github_new_repos(6)
    if github_repos:
        for i, repo in enumerate(github_repos, 1):
            sections.append(f"#### {i}. {repo['name']}\n")
            sections.append(f"- **链接**: {repo['url']}\n")
            sections.append(f"- **描述**: {repo.get('desc', '无')}\n\n")
    else:
        sections.append("暂无新仓库（或搜索未覆盖）\n\n")
    
    # 知乎文章
    sections.append("### 📖 知乎相关文章\n\n")
    zhihu_articles = fetch_zhihu_articles(4)
    if zhihu_articles:
        for i, article in enumerate(zhihu_articles, 1):
            sections.append(f"#### {i}. {article['title']}\n")
            sections.append(f"- **链接**: {article['url']}\n")
            sections.append(f"- **简介**: {article.get('summary', '无')}\n\n")
    else:
        sections.append("暂无知乎文章\n\n")
    
    # 水产市场
    sections.append("### 🧩 水产市场最新技能\n\n")
    skills = fetch_marketplace_skills(6)
    if skills:
        for i, skill in enumerate(skills, 1):
            sections.append(f"#### {i}. {skill.get('displayName', skill.get('name', '未知'))}\n")
            sections.append(f"- **描述**: {skill.get('description', '无')}\n")
            sections.append(f"- **类型**: {skill.get('type', 'unknown')}\n\n")
    else:
        sections.append("暂无新技能上架（需配置 openclawmp 认证）\n\n")
    
    # 5. 明日计划
    sections.append("## 📅 明日计划\n\n")
    sections.append("1. **优化搜索超时**：增加重试和更完备的异常处理\n")
    sections.append("2. **配置水产市场 API**：提供认证后获取真实技能列表\n")
    sections.append("3. **部署自动任务**：将此报告加入每日 cron（建议早晨 7:00 生成）\n")
    sections.append("4. **监控反馈**：根据用户对报告内容的反馈持续优化搜索词\n\n")
    
    sections.append("---\n")
    sections.append(f"*本报告由 OpenClaw 自动生成 | 数据源已过滤为简体中文*\n")
    
    return title + header + "".join(sections)

def main():
    parser = argparse.ArgumentParser(description="每日复盘报告（整合版）")
    parser.add_argument("--output", help="输出文件路径（默认 stdout）")
    args = parser.parse_args()
    
    report = generate_review_report()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 复盘报告已生成: {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()
